"""FastAPI server for the WonderLens Activity Demo."""

import asyncio
import json
import mimetypes
import re
import struct
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Ensure JS/CSS MIME types are correct (some systems default .js to application/json)
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from pydantic import BaseModel, Field

try:
    from .agents.pipeline import initialize_session
    from .agents.script_agent import ScriptAgent
    from .config import get_settings
    from .db import init_db, log_session, log_turn, update_session_status
    from .entity_registry import (
        ENTITY_REGISTRY,
        all_entities_for_api,
        generate_round_items,
        is_demo_entity,
        lookup_by_entity_name,
        validate_registry,
    )
    from .game_loader import get_demo_recipe  # noqa: F401 — triggers game loading + registry population
    from .logger import setup_logger
    from .recipe_loader import load_instruction_recipe, recipe_to_session_state
    from .scenarios import load_scenario, match_scenario
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel, UpstreamConversationTurn
    from .schemas.turn_response import TurnResponse
    from .state_machine import get_screen_frame
    from .stt import transcribe_audio
    from .tts import synthesize_speech_ogg_async, synthesize_speech_ogg_stream_async
    from .turn_handler import (
        TurnInput,
        _generate_with_retry,
        _should_auto_advance,
        _step_round_number,
        resolve_turn,
    )
    from .vision import analyze_image
except ImportError:
    from agents.pipeline import initialize_session
    from agents.script_agent import ScriptAgent
    from config import get_settings
    from db import init_db, log_session, log_turn, update_session_status
    from entity_registry import (
        ENTITY_REGISTRY,
        all_entities_for_api,
        generate_round_items,
        is_demo_entity,
        lookup_by_entity_name,
        validate_registry,
    )
    from game_loader import get_demo_recipe  # noqa: F401
    from logger import setup_logger
    from recipe_loader import load_instruction_recipe, recipe_to_session_state
    from scenarios import load_scenario, match_scenario
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel, UpstreamConversationTurn
    from schemas.turn_response import TurnResponse
    from state_machine import get_screen_frame
    from stt import transcribe_audio
    from tts import synthesize_speech_ogg_async, synthesize_speech_ogg_stream_async
    from turn_handler import (
        TurnInput,
        _generate_with_retry,
        _should_auto_advance,
        _step_round_number,
        resolve_turn,
    )
    from vision import analyze_image

logger = setup_logger(__name__)


_sessions: dict[str, SessionStateModel] = {}


def _suppress_genai_close_error(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """Suppress the google-genai SDK's BaseApiClient.aclose() AttributeError.

    The SDK lazily initializes _async_httpx_client but its finalizer always
    tries to close it, causing a harmless AttributeError on cleanup.
    """
    exc = context.get("exception")
    if isinstance(exc, AttributeError) and "_async_httpx_client" in str(exc):
        return
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    asyncio.get_event_loop().set_exception_handler(_suppress_genai_close_error)
    validate_registry()
    await init_db(settings.db_path)
    logger.info("WonderLens server started")
    yield


app = FastAPI(title="WonderLens Activity Demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-PCM-Size"],
)


# --- Request models ---


class TurnRequest(BaseModel):
    session_id: str
    text: str = ""
    is_silent: bool = False
    photo_id: str | None = None


class TTSRequest(BaseModel):
    text: str
    tier: str = "T0"


class DeepLinkStartRequest(BaseModel):
    entity: str
    tier: str = "T0"
    context_url: str = ""
    conversation_context: list[UpstreamConversationTurn] = Field(default_factory=list)


# --- Endpoints ---


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/entities")
async def list_entities() -> JSONResponse:
    """Return all demo entities grouped by category for the frontend."""
    return JSONResponse({"categories": all_entities_for_api()})


@app.post("/api/start-deep-link")
async def start_deep_link(req: DeepLinkStartRequest) -> JSONResponse:
    start_time = time.perf_counter()
    settings = get_settings()
    session_id = str(uuid.uuid4())

    try:
        entity_config = lookup_by_entity_name(req.entity)
        if not entity_config:
            available = [e.entity_name for e in ENTITY_REGISTRY]
            return JSONResponse(
                {"error": "Unknown entity", "available_entities": available},
                status_code=400,
            )

        activity_type = entity_config.activity_type
        recipe = load_instruction_recipe(activity_type)
        state = recipe_to_session_state(recipe, session_id, req.tier, entity_config.demo_filename)

        # Fetch upstream conversation from context_url (server-side, no CORS issues)
        conversation_context = list(req.conversation_context)
        if req.context_url and not conversation_context:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    ctx_res = await client.get(req.context_url)
                    ctx_res.raise_for_status()
                    ctx_data = ctx_res.json()
                if isinstance(ctx_data, list):
                    conversation_context = [
                        UpstreamConversationTurn(role=t["role"], text=t["text"])
                        for t in ctx_data
                        if isinstance(t, dict) and t.get("role") in ("ai", "child") and isinstance(t.get("text"), str)
                    ]
            except Exception as ctx_err:
                logger.warning(f"Failed to fetch context_url {req.context_url}: {ctx_err}")

        state.deep_linked = True
        state.upstream_conversation = conversation_context

        if state.template_type == "cat5":
            state.round_items = generate_round_items(state.activity_type, state.total_rounds)

        await log_session(settings.db_path, session_id, req.tier, activity_type, source="deep_link")

        script_agent = ScriptAgent()
        first_turn = await _generate_with_retry(script_agent, state, is_first_on_step=True)

        state.conversation_history.append(
            ConversationTurn(role="ai", text=first_turn.dialogue, step=state.current_step, round_number=None)
        )
        state.turn_count = 1

        _sessions[session_id] = state

        hook_frame = get_screen_frame(
            "STEP_1_HOOK",
            state.template_type,
            state.creative_slots,
            {"entity_name": state.entity_name, "ib_key_concepts": state.ib_key_concepts},
            visual_frames=state.visual_frames or None,
        )
        first_turn_data = _build_turn_response(first_turn, hook_frame, "hook")
        await _log_hook_turn(state, session_id, first_turn.dialogue)

        vision_result = {
            "entity": state.entity_name,
            "category": "",
            "scene": "",
            "features": [],
        }

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"Deep link session started: {session_id}, entity={req.entity}, "
            f"activity={activity_type}, tier={req.tier}, latency={latency_ms}ms"
        )

        return JSONResponse(
            {
                "session_id": session_id,
                "vision_result": vision_result,
                "first_turn": first_turn_data,
                "activity_type": activity_type,
                "template_type": state.template_type,
                "session_state": _session_state_dict(state),
                "photo_url": entity_config.icon_src,
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )

    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Deep link start failed ({latency_ms}ms): {e}")
        return JSONResponse(
            {"error": str(e), "status": "error", "latency_ms": latency_ms},
            status_code=500,
        )


@app.post("/api/start")
async def start_session(
    photo: UploadFile = File(...),
    tier: str = Form("T0"),
) -> JSONResponse:
    start_time = time.perf_counter()
    settings = get_settings()
    session_id = str(uuid.uuid4())

    try:
        # 1. Read photo
        image_bytes = await photo.read()
        mime_type = photo.content_type or "image/jpeg"

        # 2. Match scenario from filename (instant — no LLM needed)
        filename = photo.filename or ""
        activity_type = match_scenario("unknown", [], filename=filename)

        # --- Instruction recipe path (demo entities) ---
        if is_demo_entity(filename):
            recipe = load_instruction_recipe(activity_type)
            state = recipe_to_session_state(recipe, session_id, tier, filename)

            if state.template_type == "cat5":
                state.round_items = generate_round_items(state.activity_type, state.total_rounds)

            await log_session(settings.db_path, session_id, tier, activity_type)

            # Generate hook turn via Script Agent (uses instruction recipe)
            script_agent = ScriptAgent()
            first_turn = await _generate_with_retry(script_agent, state, is_first_on_step=True)

            # Record hook in conversation history; STEP_2 is generated on the first follow-up turn.
            state.conversation_history.append(
                ConversationTurn(role="ai", text=first_turn.dialogue, step=state.current_step, round_number=None)
            )
            state.turn_count = 1

            _sessions[session_id] = state

            hook_frame = get_screen_frame(
                "STEP_1_HOOK",
                state.template_type,
                state.creative_slots,
                {"entity_name": state.entity_name, "ib_key_concepts": state.ib_key_concepts},
                visual_frames=state.visual_frames or None,
            )
            first_turn_data = _build_turn_response(first_turn, hook_frame, "hook")
            await _log_hook_turn(state, session_id, first_turn.dialogue)

            vision_result = {
                "entity": state.entity_name,
                "category": "",
                "scene": "",
                "features": [],
            }

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"Instruction recipe session started: {session_id}, activity={activity_type}, "
                f"template={state.template_type}, tier={tier}, latency={latency_ms}ms"
            )

            return JSONResponse(
                {
                    "session_id": session_id,
                    "vision_result": vision_result,
                    "first_turn": first_turn_data,
                    "activity_type": activity_type,
                    "template_type": state.template_type,
                    "session_state": _session_state_dict(state),
                    "status": "ok",
                    "latency_ms": latency_ms,
                }
            )

        # --- Live pipeline path (custom photo uploads) ---
        scenario = load_scenario(activity_type)

        # 3. Build pipeline context with filename-based entity for Director
        filename_entity = _entity_from_filename(filename)
        context = {
            "entity": filename_entity,
            "entity_category": "",
            "tier": tier,
            "activity_type": activity_type,
            "scene": "",
            "features": [],
            "key_concepts": scenario.get("key_concepts", []),
            "ib_theme": "Who We Are",
        }

        # 4. Run Vision + Director in parallel
        vision_task = asyncio.create_task(analyze_image(image_bytes, mime_type))
        session_task = asyncio.create_task(initialize_session(context, session_id))

        # Wait for both — Director+Script don't need vision results
        vision_result, (state, first_turn) = await asyncio.gather(vision_task, session_task)

        # 5. Enrich session state with vision results (better entity info for future turns)
        if vision_result.get("entity") and vision_result["entity"] != "unknown":
            state.entity_name = vision_result["entity"]
        if vision_result.get("features"):
            state.entity_attributes = vision_result["features"]
        if vision_result.get("category"):
            state.entity_category = vision_result["category"]
        if vision_result.get("scene"):
            state.scene = vision_result["scene"]

        # 6. Log session to DB
        await log_session(settings.db_path, session_id, tier, activity_type)

        # 7. Generate per-round items for Cat 5
        if state.template_type == "cat5":
            state.round_items = generate_round_items(state.activity_type, state.total_rounds)

        # 8. Store session state
        _sessions[session_id] = state

        # 9. Build first turn response using Visual Agent frames
        hook_frame = get_screen_frame(
            "STEP_1_HOOK",
            state.template_type,
            state.creative_slots,
            {"entity_name": state.entity_name, "ib_key_concepts": state.ib_key_concepts},
            visual_frames=state.visual_frames or None,
        )
        first_turn_data = _build_turn_response(first_turn, hook_frame, "hook")
        await _log_hook_turn(state, session_id, first_turn.dialogue)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"Session started: {session_id}, activity={activity_type}, "
            f"template={state.template_type}, tier={tier}, latency={latency_ms}ms"
        )

        return JSONResponse(
            {
                "session_id": session_id,
                "vision_result": vision_result,
                "first_turn": first_turn_data,
                "activity_type": activity_type,
                "template_type": state.template_type,
                "session_state": _session_state_dict(state),
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )

    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Start session failed ({latency_ms}ms): {e}")
        return JSONResponse(
            {"error": str(e), "status": "error", "latency_ms": latency_ms},
            status_code=500,
        )


@app.post("/api/turn")
async def process_turn(req: TurnRequest) -> JSONResponse:
    start_time = time.perf_counter()
    settings = get_settings()

    state = _sessions.get(req.session_id)
    if not state:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    if state.status != "active":
        return JSONResponse(
            {
                "error": f"Session is {state.status}",
                "session_state": _session_state_dict(state),
            },
            status_code=400,
        )

    script_agent = ScriptAgent()

    await _log_user_turn(req, state)

    # Resolve the turn using unified turn handler
    result = await resolve_turn(
        state, TurnInput(text=req.text, is_silent=req.is_silent, photo_id=req.photo_id), script_agent
    )

    # DB logging based on result
    response_type = "error" if result.error_exit else result.response_type

    if state.status == "exited":
        exit_reason = "consecutive_silence" if state.consecutive_silence >= 2 else "invitation_declined"
        if state.consecutive_wrong >= 2:
            exit_reason = "wrong_photos"
        await update_session_status(settings.db_path, req.session_id, "exited", exit_reason, state.turn_count)
    elif state.status == "completed":
        completion_reason = "closing_delivered" if result.response_type == "closing" else "all_steps_done"
        await update_session_status(settings.db_path, req.session_id, "completed", completion_reason, state.turn_count)

    await _log_ai_turn(req, state, result.turn_response.dialogue, response_type)

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    turn_data = _build_turn_response(result.turn_response, result.screen_frame, response_type, result.error_exit)
    turn_data["auto_advance"] = result.auto_advance

    return JSONResponse(
        {
            "turn": turn_data,
            "session_state": _session_state_dict(state),
            "latency_ms": latency_ms,
        }
    )


@app.post("/api/turn-speak")
async def turn_and_speak(req: TurnRequest) -> Response:
    """Combined turn + TTS endpoint.

    Streams Script Agent output, starts TTS as soon as dialogue is extracted,
    and returns a binary response: [4-byte JSON length][JSON][OGG/Opus audio].

    This eliminates the round-trip between /api/turn and /api/tts, while still
    allowing TTS generation to overlap with Script Agent completion.
    """
    start_time = time.perf_counter()
    settings = get_settings()

    state = _sessions.get(req.session_id)
    if not state:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    if state.status != "active":
        return JSONResponse(
            {"error": f"Session is {state.status}", "session_state": _session_state_dict(state)},
            status_code=400,
        )

    async def _stream() -> bytes:  # type: ignore[return]
        script_agent = ScriptAgent()

        await _log_user_turn(req, state)

        # Resolve the turn using unified turn handler
        result = await resolve_turn(
            state, TurnInput(text=req.text, is_silent=req.is_silent, photo_id=req.photo_id), script_agent
        )

        # DB logging based on result
        response_type = "error" if result.error_exit else result.response_type

        if state.status == "exited":
            exit_reason = "consecutive_silence" if state.consecutive_silence >= 2 else "invitation_declined"
            if state.consecutive_wrong >= 2:
                exit_reason = "wrong_photos"
            await update_session_status(settings.db_path, req.session_id, "exited", exit_reason, state.turn_count)
        elif state.status == "completed":
            completion_reason = "closing_delivered" if result.response_type == "closing" else "all_steps_done"
            await update_session_status(
                settings.db_path, req.session_id, "completed", completion_reason, state.turn_count
            )

        await _log_ai_turn(req, state, result.turn_response.dialogue, response_type)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        turn_data = _build_turn_response(result.turn_response, result.screen_frame, response_type, result.error_exit)
        turn_data["auto_advance"] = result.auto_advance

        # Yield JSON header (4-byte length prefix + JSON)
        response_json = json.dumps(
            {
                "turn": turn_data,
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        ).encode()
        yield struct.pack(">I", len(response_json))
        yield response_json

        # Stream OGG/Opus audio pages as they are encoded
        async for ogg_chunk in synthesize_speech_ogg_stream_async(result.turn_response.dialogue, state.tier):
            yield ogg_chunk

    return StreamingResponse(
        _stream(),
        media_type="application/octet-stream",
    )


@app.post("/api/stt")
async def speech_to_text(audio: UploadFile = File(...)) -> JSONResponse:
    audio_bytes = await audio.read()
    mime_type = audio.content_type or None
    result = await transcribe_audio(audio_bytes, mime_type)
    if not result["text"]:
        return JSONResponse({"text": "", "error": "transcription_failed"}, status_code=422)
    return JSONResponse(result)


@app.post("/api/tts")
async def text_to_speech(req: TTSRequest) -> Response:
    result = await synthesize_speech_ogg_async(req.text, req.tier)
    if result is None:
        return Response(status_code=204)
    audio_bytes, pcm_size = result
    content_type = "audio/ogg" if audio_bytes[:4] == b"OggS" else "audio/wav"
    return Response(content=audio_bytes, media_type=content_type, headers={"X-PCM-Size": str(pcm_size)})


@app.get("/api/tts")
async def text_to_speech_stream(text: str, tier: str = "T0") -> Response:
    """Streaming OGG/Opus TTS — set as <audio src> for progressive playback in Chrome."""
    return StreamingResponse(
        synthesize_speech_ogg_stream_async(text, tier),
        media_type="audio/ogg",
    )


# --- Helpers ---


def _build_turn_response(
    turn: TurnResponse,
    screen_frame: ScreenFrame,
    response_type: str,
    error_exit: bool = False,
) -> dict:
    """Build the turn response dict for the API."""
    # Merge Script Agent's sfx_cue into screen frame so frontend SFX player picks it up
    frame_dict = screen_frame.model_dump()
    if not frame_dict.get("sfx_cue") and turn.sfx_cue:
        frame_dict["sfx_cue"] = turn.sfx_cue

    audio: dict = {"sfx": turn.sfx_cue or frame_dict.get("sfx_cue")}
    if screen_frame.sfx_label:
        audio["sfx_label"] = screen_frame.sfx_label
    return {
        "dialogue": turn.dialogue,
        "tone_marker": turn.tone_marker,
        "screen_frame": frame_dict,
        "audio": audio,
        "response_type": response_type,
        "error_exit": error_exit,
    }


def _state_context(state: SessionStateModel) -> dict:
    """Build a context dict from session state for screen frame generation."""
    return {
        "entity_name": state.entity_name,
        "entity": state.entity_name,
        "ib_key_concepts": state.ib_key_concepts,
        "key_concepts": state.ib_key_concepts,
    }


def _entity_from_filename(filename: str) -> str:
    """Extract a best-guess entity name from the photo filename."""
    if not filename:
        return "object"
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    name = re.sub(r"[\d_-]+", " ", stem).strip()
    return name if name else "object"


async def _log_hook_turn(state: SessionStateModel, session_id: str, dialogue: str) -> None:
    """Log the first AI hook turn when a session starts."""
    settings = get_settings()
    await log_turn(
        settings.db_path,
        session_id,
        state.turn_count,
        "ai",
        dialogue,
        "hook",
        step=state.current_step,
        state_snapshot=_build_state_snapshot(state),
    )


async def _log_user_turn(req: TurnRequest, state: SessionStateModel) -> None:
    """Log the incoming user turn with the pre-resolution state snapshot."""
    settings = get_settings()
    await log_turn(
        settings.db_path,
        req.session_id,
        state.turn_count + 1,
        "user",
        text=req.text if req.text else None,
        is_silent=req.is_silent,
        photo_id=req.photo_id,
        step=state.current_step,
        state_snapshot=_build_state_snapshot(state),
    )


async def _log_ai_turn(
    req: TurnRequest,
    state: SessionStateModel,
    dialogue: str,
    response_type: str,
) -> None:
    """Log the outgoing AI turn with the step that produced the dialogue."""
    settings = get_settings()
    await log_turn(
        settings.db_path,
        req.session_id,
        state.turn_count,
        "ai",
        dialogue,
        response_type,
        is_silent=req.is_silent,
        consecutive_silence=state.consecutive_silence,
        step=_latest_ai_turn_step(state, dialogue),
        state_snapshot=_build_state_snapshot(state),
    )


def _latest_ai_turn_step(state: SessionStateModel, dialogue: str) -> str:
    """Return the step attached to the most recently appended AI dialogue."""
    for turn in reversed(state.conversation_history):
        if turn.role == "ai" and turn.text == dialogue:
            return turn.step
    return state.current_step


def _build_state_snapshot(state: SessionStateModel) -> str:
    """Build a compact JSON snapshot of key state fields for turn logging."""
    snapshot: dict = {
        "current_step": state.current_step,
        "current_round": state.current_round,
        "collection_phase": state.collection_phase,
        "synthesis_phase": state.synthesis_phase,
        "consecutive_silence": state.consecutive_silence,
        "consecutive_wrong": state.consecutive_wrong,
        "collected_photos": state.collected_photos,
        "collected_names": state.collected_names,
        "turn_count": state.turn_count,
    }
    return json.dumps(snapshot, separators=(",", ":"))


def _session_state_dict(state: SessionStateModel) -> dict:
    result: dict = {
        "status": state.status,
        "current_step": state.current_step,
        "current_round": state.current_round,
        "total_rounds": state.total_rounds,
        "collected_photos": state.collected_photos,
        "consecutive_silence": state.consecutive_silence,
        "consecutive_wrong": state.consecutive_wrong,
        "invitation_decline_count": state.invitation_decline_count,
        "turn_count": state.turn_count,
        "template_type": state.template_type,
        "auto_advance": _should_auto_advance(state),
    }

    # Expose Cat 5 collection context
    if state.template_type == "cat5" and isinstance(state.creative_slots, Cat5CreativeSlots):
        result["collection_criterion"] = state.creative_slots.collection_criterion
        result["collection_phase"] = state.collection_phase
        result["collected_names"] = state.collected_names
        result["collected_details"] = state.collected_details

    # Expose synthesis loop state
    if state.current_step == "STEP_4_SYNTHESIS":
        result["synthesis_phase"] = state.synthesis_phase
        result["synthesis_prompt_count"] = state.synthesis_prompt_count

    if state.round_items and state.current_step.startswith("STEP_3_COLLECT_"):
        round_idx = _step_round_number(state.current_step) - 1
        if 0 <= round_idx < len(state.round_items):
            result["current_round_items"] = [
                {"id": item["id"], "label": item["label"], "image": item.get("image", "")}
                for item in state.round_items[round_idx]
            ]

    return result


# --- Serve frontend static files in production ---
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
logger.info(f"Frontend dist path: {_FRONTEND_DIST} (exists={_FRONTEND_DIST.is_dir()})")


@app.get("/api/debug-static")
async def debug_static() -> JSONResponse:
    """Debug endpoint to verify static file serving."""
    if not _FRONTEND_DIST.is_dir():
        return JSONResponse({"error": "dist dir not found", "path": str(_FRONTEND_DIST)})
    assets = list((_FRONTEND_DIST / "assets").iterdir()) if (_FRONTEND_DIST / "assets").is_dir() else []
    return JSONResponse(
        {
            "dist_path": str(_FRONTEND_DIST),
            "index_html": (_FRONTEND_DIST / "index.html").exists(),
            "assets": [f.name for f in assets],
            "top_level": [f.name for f in _FRONTEND_DIST.iterdir()],
        }
    )


if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
