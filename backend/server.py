"""FastAPI server for the WonderLens Activity Demo."""

import asyncio
import json
import mimetypes
import re
import struct
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path, PurePosixPath

import httpx
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Ensure JS/CSS MIME types are correct (some systems default .js to application/json)
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from pydantic import BaseModel, Field, ValidationError

try:
    from . import feedback_storage
    from .activity_catalog import activity_summaries, is_text_game_activity
    from .agents.pipeline import initialize_session
    from .agents.script_agent import ScriptAgent
    from .character_sounds import pick_fallback_cue, validate_character_sfx
    from .config import get_settings
    from .db import init_db, log_session, log_turn, update_session_status
    from .entity_registry import (
        ENTITY_REGISTRY,
        EntityConfig,
        all_entities_for_api,
        generate_round_items,
        get_entity_or_none,
        is_demo_entity,
        lookup_by_entity_name,
        validate_registry,
    )
    from .feedback_storage import (
        build_folder_name,
        list_all_feedback,
        read_feedback_image,
        write_feedback_bundle,
    )
    from .game_loader import get_demo_recipe  # noqa: F401 — triggers game loading + registry population
    from .logger import setup_logger
    from .recipe_loader import load_instruction_recipe, recipe_to_session_state
    from .scenarios import load_scenario, match_scenario
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat1CreativeSlots, Cat3CreativeSlots, Cat5CreativeSlots
    from .schemas.feedback import FeedbackPayload
    from .schemas.session_state import ConversationTurn, SessionStateModel, UpstreamConversationTurn
    from .schemas.turn_response import TurnResponse
    from .state_machine import get_screen_frame
    from .stt import transcribe_audio
    from .stt_stream import (
        MAX_BINARY_FRAME_SIZE_BYTES,
        SttPingMessage,
        SttStartMessage,
        SttStopMessage,
        select_stt_provider_route,
        validate_first_audio_chunk,
    )
    from .tts import synthesize_speech_ogg_async, synthesize_speech_ogg_stream_async
    from .turn_handling import (
        TurnInput,
        _generate_with_retry,
        _should_auto_advance,
        _step_round_number,
        get_retry_stats,
        resolve_turn,
    )
    from .vision import analyze_image
except ImportError:
    import feedback_storage
    from activity_catalog import activity_summaries, is_text_game_activity
    from agents.pipeline import initialize_session
    from agents.script_agent import ScriptAgent
    from character_sounds import pick_fallback_cue, validate_character_sfx
    from config import get_settings
    from db import init_db, log_session, log_turn, update_session_status
    from entity_registry import (
        ENTITY_REGISTRY,
        EntityConfig,
        all_entities_for_api,
        generate_round_items,
        get_entity_or_none,
        is_demo_entity,
        lookup_by_entity_name,
        validate_registry,
    )
    from feedback_storage import (
        build_folder_name,
        list_all_feedback,
        read_feedback_image,
        write_feedback_bundle,
    )
    from game_loader import get_demo_recipe  # noqa: F401
    from logger import setup_logger
    from recipe_loader import load_instruction_recipe, recipe_to_session_state
    from scenarios import load_scenario, match_scenario
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat1CreativeSlots, Cat3CreativeSlots, Cat5CreativeSlots
    from schemas.feedback import FeedbackPayload
    from schemas.session_state import ConversationTurn, SessionStateModel, UpstreamConversationTurn
    from schemas.turn_response import TurnResponse
    from state_machine import get_screen_frame
    from stt import transcribe_audio
    from stt_stream import (
        MAX_BINARY_FRAME_SIZE_BYTES,
        SttPingMessage,
        SttStartMessage,
        SttStopMessage,
        select_stt_provider_route,
        validate_first_audio_chunk,
    )
    from tts import synthesize_speech_ogg_async, synthesize_speech_ogg_stream_async
    from turn_handling import (
        TurnInput,
        _generate_with_retry,
        _should_auto_advance,
        _step_round_number,
        get_retry_stats,
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
    is_selection: bool = False


class TTSRequest(BaseModel):
    text: str
    tier: str = "T0"


class DeepLinkStartRequest(BaseModel):
    entity: str
    tier: str = "T0"
    context_url: str = ""
    conversation_context: list[UpstreamConversationTurn] = Field(default_factory=list)


class ActivityStartRequest(BaseModel):
    activity_type: str
    tier: str = "T1"
    interaction_mode: str = "text"


# --- Endpoints ---


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/entities")
async def list_entities() -> JSONResponse:
    """Return all demo entities grouped by category for the frontend."""
    return JSONResponse({"categories": all_entities_for_api()})


@app.get("/api/activities")
async def list_activities() -> JSONResponse:
    """Return standalone text-game activities for the frontend."""
    summaries = [activity.model_dump() for activity in activity_summaries()]
    return JSONResponse({"count": len(summaries), "activities": summaries})


@app.post("/api/start-activity")
async def start_activity(req: ActivityStartRequest) -> JSONResponse:
    """Start a standalone activity text-game session."""
    entity_config = get_entity_or_none(req.activity_type)
    if not entity_config or not is_text_game_activity(entity_config):
        return JSONResponse({"error": "unknown_activity"}, status_code=404)
    if req.interaction_mode != "text":
        return JSONResponse({"error": "unsupported_interaction_mode"}, status_code=422)
    return await _start_activity_session(entity_config, req.tier, interaction_mode="text")


async def _start_activity_session(
    entity_config: EntityConfig,
    tier: str,
    *,
    interaction_mode: str,
    source: str = "activity_text_game",
) -> JSONResponse:
    """Start a recipe-backed activity session without photo or upstream context."""
    start_time = time.perf_counter()
    settings = get_settings()
    session_id = str(uuid.uuid4())
    activity_type = entity_config.activity_type

    try:
        recipe = load_instruction_recipe(activity_type)
        state = recipe_to_session_state(
            recipe,
            session_id,
            tier,
            entity_config.demo_filename,
            interaction_mode=interaction_mode,
        )

        if state.template_type == "cat5":
            state.round_items = generate_round_items(state.activity_type, state.total_rounds)

        await log_session(settings.db_path, session_id, tier, activity_type, source=source)

        script_agent = ScriptAgent()
        first_turn, _gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)

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
        first_turn_data = _build_turn_response(first_turn, hook_frame, "hook", activity_type=state.activity_type)
        await _log_hook_turn(state, session_id, first_turn.dialogue)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"Activity text session started: {session_id}, activity={activity_type}, "
            f"template={state.template_type}, tier={tier}, latency={latency_ms}ms"
        )

        return JSONResponse(
            {
                "session_id": session_id,
                "vision_result": {"entity": state.entity_name, "category": "", "scene": "", "features": []},
                "first_turn": first_turn_data,
                "activity_type": activity_type,
                "template_type": state.template_type,
                "session_state": _session_state_dict(state),
                "photo_url": entity_config.icon_src,
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Activity text start failed ({latency_ms}ms): {exc}")
        return JSONResponse(
            {"error": str(exc), "status": "error", "latency_ms": latency_ms},
            status_code=500,
        )


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
        first_turn, _gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)

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
        first_turn_data = _build_turn_response(first_turn, hook_frame, "hook", activity_type=state.activity_type)
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
            first_turn, _gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)

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
            first_turn_data = _build_turn_response(first_turn, hook_frame, "hook", activity_type=state.activity_type)
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
        first_turn_data = _build_turn_response(first_turn, hook_frame, "hook", activity_type=state.activity_type)
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
        state,
        TurnInput(text=req.text, is_silent=req.is_silent, photo_id=req.photo_id, is_selection=req.is_selection),
        script_agent
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

    await _log_ai_turn(req, state, result.turn_response.dialogue, response_type, debug=result.debug)

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    turn_data = _build_turn_response(
        result.turn_response,
        result.screen_frame,
        response_type,
        result.error_exit,
        activity_type=state.activity_type,
    )
    turn_data["auto_advance"] = result.auto_advance
    # Use POST-turn scenario — after an advance, the state holds the scenario
    # that the response dialogue is presenting (not the previous round's).
    post_turn_scenario = _current_scenario(state)
    if post_turn_scenario:
        turn_data["current_scenario"] = post_turn_scenario

    response_payload: dict = {
        "turn": turn_data,
        "session_state": _session_state_dict(state),
        "latency_ms": latency_ms,
    }
    if result.debug:
        response_payload["debug"] = result.debug

    return JSONResponse(response_payload)


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

    async def _stream():  # type: ignore[return]
        script_agent = ScriptAgent()

        await _log_user_turn(req, state)

        # Resolve the turn using unified turn handler
        result = await resolve_turn(
            state,
            TurnInput(text=req.text, is_silent=req.is_silent, photo_id=req.photo_id, is_selection=req.is_selection),
            script_agent
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

        await _log_ai_turn(req, state, result.turn_response.dialogue, response_type, debug=result.debug)

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        turn_data = _build_turn_response(
            result.turn_response,
            result.screen_frame,
            response_type,
            result.error_exit,
            activity_type=state.activity_type,
        )
        turn_data["auto_advance"] = result.auto_advance
        post_turn_scenario = _current_scenario(state)
        if post_turn_scenario:
            turn_data["current_scenario"] = post_turn_scenario

        # Yield JSON header (4-byte length prefix + JSON)
        stream_payload: dict = {
            "turn": turn_data,
            "session_state": _session_state_dict(state),
            "latency_ms": latency_ms,
        }
        if result.debug:
            stream_payload["debug"] = result.debug
        response_json = json.dumps(stream_payload).encode()
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


def _stt_error_payload(code: str, message: str) -> dict[str, str]:
    """Build a stable STT WebSocket error payload."""
    return {
        "type": "error",
        "code": code,
        "message": message,
    }


async def _close_stt_stream(websocket: WebSocket, code: str, message: str, close_code: int = 1003) -> None:
    """Send an STT error payload, then close the WebSocket."""
    await websocket.send_json(_stt_error_payload(code, message))
    await websocket.close(code=close_code)


def _decode_stt_control_message(text: str) -> dict:
    """Decode a client STT control message."""
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("STT control message must be a JSON object")
    return payload


@app.websocket("/api/stt/stream")
async def speech_to_text_stream(websocket: WebSocket) -> None:
    """Accept ordered browser Opus chunks over WebSocket and transcribe on stop."""
    await websocket.accept()

    try:
        first_message = await websocket.receive()
    except WebSocketDisconnect:
        return

    if first_message.get("bytes") is not None:
        await _close_stt_stream(websocket, "start_required", "Send a start JSON message before binary audio")
        return

    first_text = first_message.get("text")
    if first_text is None:
        await _close_stt_stream(websocket, "invalid_control", "Expected a start JSON message")
        return

    try:
        first_payload = _decode_stt_control_message(first_text)
    except (json.JSONDecodeError, ValueError) as exc:
        await _close_stt_stream(websocket, "invalid_control", str(exc))
        return

    if first_payload.get("type") != "start":
        await _close_stt_stream(websocket, "start_required", "First STT control message must be start")
        return

    try:
        start_message = SttStartMessage.model_validate(first_payload)
        route = select_stt_provider_route(start_message.audio)
    except (ValidationError, ValueError) as exc:
        await _close_stt_stream(websocket, "invalid_start", str(exc))
        return

    await websocket.send_json(
        {
            "type": "ready",
            "audio": start_message.audio.model_dump(mode="json"),
            "route": route.name,
        }
    )
    if start_message.stt.interim_results:
        await websocket.send_json(
            {
                "type": "warning",
                "code": "interim_results_unavailable",
                "message": "This provider route returns the final transcript after stop.",
            }
        )

    audio_chunks: list[bytes] = []
    has_first_audio_chunk = False

    while True:
        try:
            message = await websocket.receive()
        except WebSocketDisconnect:
            return

        if message.get("bytes") is not None:
            chunk = message["bytes"]
            if len(chunk) > MAX_BINARY_FRAME_SIZE_BYTES:
                await _close_stt_stream(
                    websocket,
                    "chunk_too_large",
                    f"Audio chunk exceeds {MAX_BINARY_FRAME_SIZE_BYTES} bytes",
                    close_code=1009,
                )
                return
            if not has_first_audio_chunk:
                try:
                    validate_first_audio_chunk(start_message.audio, chunk)
                except ValueError as exc:
                    await _close_stt_stream(websocket, "container_mismatch", str(exc))
                    return
                has_first_audio_chunk = True
            audio_chunks.append(chunk)
            continue

        text = message.get("text")
        if text is None:
            continue

        try:
            payload = _decode_stt_control_message(text)
        except (json.JSONDecodeError, ValueError) as exc:
            await _close_stt_stream(websocket, "invalid_control", str(exc))
            return

        message_type = payload.get("type")
        if message_type == "ping":
            SttPingMessage.model_validate(payload)
            await websocket.send_json({"type": "ready", "state": "streaming"})
            continue

        if message_type != "stop":
            await _close_stt_stream(websocket, "invalid_control", "Expected stop or ping after start")
            return

        try:
            stop_message = SttStopMessage.model_validate(payload)
        except ValidationError as exc:
            await _close_stt_stream(websocket, "invalid_control", str(exc))
            return

        audio_bytes = b"".join(audio_chunks)
        result = await transcribe_audio(audio_bytes, route.mime_type) if audio_bytes else {
            "text": "",
            "confidence": 0.0,
            "latency_ms": 0,
        }
        final_text = result.get("text", "")
        close_reason = "stream_complete" if final_text else "transcription_failed"
        await websocket.send_json(
            {
                "type": "closed",
                "reason": close_reason,
                "client_reason": stop_message.reason,
                "final_text": final_text,
                "confidence": result.get("confidence", 0.0),
                "latency_ms": result.get("latency_ms", 0),
            }
        )
        await websocket.close(code=1000)
        return


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


@app.post("/api/feedback")
async def submit_feedback(
    feedback: str = Form(...),
    screenshots: list[UploadFile] = File(default_factory=list),
) -> JSONResponse:
    """Persist a tester feedback bundle (JSON + screenshot PNGs) to disk."""
    try:
        payload = FeedbackPayload.model_validate_json(feedback)
    except ValidationError as exc:
        return JSONResponse(
            {"status": "error", "error": "invalid_feedback_payload", "details": exc.errors()},
            status_code=422,
        )

    referenced_paths = [rel for flag in payload.flags for rel in flag.screenshots]
    for rel in referenced_paths:
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts:
            return JSONResponse(
                {"status": "error", "error": "unsafe_screenshot_path", "path": rel},
                status_code=422,
            )

    expected = {PurePosixPath(rel).name for rel in referenced_paths}
    received = {Path(up.filename or "").name for up in screenshots if up.filename}
    missing = sorted(expected - received)
    extra = sorted(received - expected)
    if missing or extra:
        return JSONResponse(
            {
                "status": "error",
                "error": "screenshot_filename_mismatch",
                "missing": missing,
                "extra": extra,
            },
            status_code=422,
        )

    try:
        blobs = {Path(up.filename or "").name: await up.read() for up in screenshots if up.filename}
        screenshots_by_relative = {rel: blobs[PurePosixPath(rel).name] for rel in referenced_paths}

        folder_name = build_folder_name(
            payload.session_ended_at,
            payload.tester_alias,
            payload.session_id,
        )
        normalized_json = json.dumps(payload.model_dump(mode="json"), indent=2)
        bundle_path = write_feedback_bundle(
            feedback_storage.FEEDBACK_DIR,
            folder_name,
            normalized_json,
            screenshots_by_relative,
        )

        backend_root = Path(__file__).resolve().parent
        try:
            relative_str = str(bundle_path.resolve().relative_to(backend_root))
        except ValueError:
            relative_str = str(bundle_path)

        return JSONResponse({"status": "saved", "path": relative_str})

    except ValueError as exc:
        return JSONResponse({"status": "error", "error": str(exc)}, status_code=422)
    except Exception:
        logger.exception("Feedback submission failed")
        return JSONResponse(
            {"status": "error", "error": "feedback_write_failed"},
            status_code=500,
        )


@app.get("/api/feedback/list")
async def list_feedback() -> JSONResponse:
    """Return every flag across every saved feedback bundle, newest first."""
    try:
        entries = list_all_feedback(feedback_storage.FEEDBACK_DIR)
    except Exception:
        logger.exception("Feedback list read failed")
        return JSONResponse(
            {"status": "error", "error": "feedback_list_failed"},
            status_code=500,
        )

    entries.sort(key=lambda e: (e.get("flag") or {}).get("flagged_at") or "", reverse=True)
    return JSONResponse({"entries": entries})


@app.get("/api/feedback/image/{folder_name}/{relative_path:path}")
async def get_feedback_image(folder_name: str, relative_path: str) -> Response:
    """Serve a single screenshot file from a feedback bundle."""
    try:
        data = read_feedback_image(folder_name, relative_path, feedback_storage.FEEDBACK_DIR)
    except ValueError:
        return JSONResponse(
            {"status": "error", "error": "unsafe_feedback_path"},
            status_code=400,
        )
    except Exception:
        logger.exception("Feedback image read failed")
        return JSONResponse(
            {"status": "error", "error": "feedback_image_failed"},
            status_code=500,
        )

    if data is None:
        return JSONResponse(
            {"status": "error", "error": "feedback_image_not_found"},
            status_code=404,
        )

    mime_type, _ = mimetypes.guess_type(relative_path)
    return Response(content=data, media_type=mime_type or "application/octet-stream")


# --- Helpers ---


_EMOTION_TO_CHARACTER_STATE: dict[str, str] = {
    "excited": "excited",
    "celebrating": "excited",
    "impressed": "excited",
    "joyful": "excited",
    "proud": "excited",
    "gentle": "encouraging",
    "encouraging": "encouraging",
    "warm": "encouraging",
    "curious": "surprised",
    "mysterious": "surprised",
    "adventurous": "surprised",
}

_RESPONSE_TYPE_TO_CHARACTER_STATE: dict[str, str] = {
    "hook": "waving",
    "celebration": "celebrating",
    "celebrate": "celebrating",
    "closing": "waving",
    "graceful_exit": "waving",
}


def _current_scenario(state: SessionStateModel) -> str | None:
    """Return the current round scenario text, or None."""
    if state.template_type != "cat1" or not isinstance(state.creative_slots, Cat1CreativeSlots):
        return None
    round_idx = max(0, state.current_round - 1)
    if round_idx < len(state.creative_slots.round_scenarios):
        return state.creative_slots.round_scenarios[round_idx]
    return None


def _map_character_state(tone_marker: str, response_type: str) -> str:
    """Map emotion tag and response type to a character animation state."""
    if response_type in _RESPONSE_TYPE_TO_CHARACTER_STATE:
        return _RESPONSE_TYPE_TO_CHARACTER_STATE[response_type]
    # Exact match
    if tone_marker in _EMOTION_TO_CHARACTER_STATE:
        return _EMOTION_TO_CHARACTER_STATE[tone_marker]
    # Partial match — LLM returns compound markers like "excited and warm"
    marker_lower = tone_marker.lower()
    for emotion, state in _EMOTION_TO_CHARACTER_STATE.items():
        if emotion in marker_lower:
            return state
    return "speaking"


def _build_turn_response(
    turn: TurnResponse,
    screen_frame: ScreenFrame,
    response_type: str,
    error_exit: bool = False,
    activity_type: str = "",
) -> dict:
    """Build the turn response dict for the API."""
    # Merge Script Agent's sfx_cue into screen frame so frontend SFX player picks it up
    frame_dict = screen_frame.model_dump()
    if not frame_dict.get("sfx_cue") and turn.sfx_cue:
        frame_dict["sfx_cue"] = turn.sfx_cue

    audio: dict = {"sfx": turn.sfx_cue or frame_dict.get("sfx_cue")}
    if screen_frame.sfx_label:
        audio["sfx_label"] = screen_frame.sfx_label

    # Validate character/environment sound cues; fall back if LLM returned none
    character_sfx = []
    if activity_type:
        validated = (
            validate_character_sfx(activity_type, turn.character_sfx)
            if turn.character_sfx
            else pick_fallback_cue(activity_type)
        )
        character_sfx = [c.model_dump() for c in validated]

    return {
        "dialogue": turn.dialogue,
        "tone_marker": turn.tone_marker,
        "character_state": _map_character_state(turn.tone_marker, response_type),
        "screen_frame": frame_dict,
        "audio": audio,
        "character_sfx": character_sfx,
        "response_type": response_type,
        "error_exit": error_exit,
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
    debug: dict | None = None,
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
        debug_payload=json.dumps(debug, separators=(",", ":")) if debug else None,
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
        "interaction_mode": state.interaction_mode,
        "collection_phase": state.collection_phase,
        "synthesis_phase": state.synthesis_phase,
        "consecutive_silence": state.consecutive_silence,
        "consecutive_wrong": state.consecutive_wrong,
        "collected_photos": state.collected_photos,
        "collected_text_items": state.collected_text_items,
        "collected_names": state.collected_names,
        "turn_count": state.turn_count,
        "child_intent": state.child_intent,
    }
    return json.dumps(snapshot, separators=(",", ":"))


def _session_state_dict(state: SessionStateModel) -> dict:
    result: dict = {
        "status": state.status,
        "current_step": state.current_step,
        "current_round": state.current_round,
        "total_rounds": state.total_rounds,
        "interaction_mode": state.interaction_mode,
        "collected_photos": state.collected_photos,
        "collected_text_items": state.collected_text_items,
        "consecutive_silence": state.consecutive_silence,
        "consecutive_wrong": state.consecutive_wrong,
        "invitation_decline_count": state.invitation_decline_count,
        "turn_count": state.turn_count,
        "template_type": state.template_type,
        "auto_advance": _should_auto_advance(state),
        "child_intent": state.child_intent,
        "last_directive_action": state.last_directive_action,
    }

    # Expose Cat1 current round scenario for video clip selection
    if state.template_type == "cat1" and isinstance(state.creative_slots, Cat1CreativeSlots):
        round_idx = max(0, state.current_round - 1)
        if round_idx < len(state.creative_slots.round_scenarios):
            result["current_scenario"] = state.creative_slots.round_scenarios[round_idx]

    # Expose Cat 3 guided build context
    if (
        state.template_type == "cat3"
        and isinstance(state.creative_slots, Cat3CreativeSlots)
        and state.current_step.startswith("STEP_3_BUILD_")
    ):
        round_idx = _step_round_number(state.current_step) - 1
        result["build_materials"] = state.creative_slots.build_materials
        if 0 <= round_idx < len(state.creative_slots.build_steps):
            result["current_build_step"] = state.creative_slots.build_steps[round_idx]

    # Expose Cat 5 collection context
    if state.template_type == "cat5" and isinstance(state.creative_slots, Cat5CreativeSlots):
        result["collection_criterion"] = state.creative_slots.collection_criterion
        result["collection_phase"] = state.collection_phase
        result["collected_names"] = state.collected_names
        result["collected_details"] = state.collected_details
        result["detail_exchange_count"] = state.detail_exchange_count

        # Story elements (Turn Director path)
        if state.story_elements:
            result["story_elements"] = [
                {
                    "round_number": el.round_number,
                    "character_name": el.character_name,
                    "trait_or_detail": el.trait_or_detail,
                    "child_words": el.child_words,
                }
                for el in state.story_elements
            ]

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
