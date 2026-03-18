"""FastAPI server for the WonderLens Activity Demo."""

import asyncio
import json
import random
import re
import struct
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

try:
    from .agents.pipeline import initialize_session
    from .agents.script_agent import ScriptAgent
    from .config import get_settings
    from .db import init_db, log_session, log_turn, update_session_status
    from .logger import setup_logger
    from .recipe_loader import is_demo_entity, load_instruction_recipe, recipe_to_session_state
    from .scenarios import load_scenario, match_scenario
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.turn_response import TurnResponse
    from .state_machine import get_screen_frame
    from .stt import transcribe_audio
    from .tts import SAMPLE_RATE, synthesize_speech_stream_async
    from .turn_handler import (
        TurnInput,
        TurnResult,
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
    from logger import setup_logger
    from recipe_loader import is_demo_entity, load_instruction_recipe, recipe_to_session_state
    from scenarios import load_scenario, match_scenario
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import get_screen_frame
    from stt import transcribe_audio
    from tts import SAMPLE_RATE, synthesize_speech_stream_async
    from turn_handler import (
        TurnInput,
        TurnResult,
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
    expose_headers=["X-Sample-Rate"],
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


# --- Cat 5 collection validation ---

COLLECTION_CATALOGS: dict[str, dict[str, list[dict]]] = {
    "polka_dot_patrol": {
        "correct": [
            {"id": "spotted_mushroom", "label": "Spotted mushroom", "image": "/icons/spotted_mushroom.png"},
            {"id": "dotted_pebble", "label": "Dotted pebble", "image": "/icons/dotted_pebble.png"},
            {"id": "speckled_leaf", "label": "Speckled leaf", "image": "/icons/speckled_leaf.png"},
            {"id": "circle_flower", "label": "Flower with circles", "image": "/icons/circle_flower.png"},
        ],
        "distractors": [
            {"id": "straight_stick", "label": "Straight stick", "image": "/icons/straight_stick.png"},
            {"id": "plain_bark", "label": "Plain bark", "image": "/icons/plain_bark.png"},
            {"id": "long_grass", "label": "Long grass blade", "image": "/icons/long_grass.png"},
            {"id": "smooth_stone", "label": "Smooth stone", "image": "/icons/smooth_stone.png"},
            {"id": "pine_needle", "label": "Pine needles", "image": "/icons/pine_needle.png"},
            {"id": "plain_leaf", "label": "Plain leaf", "image": "/icons/plain_leaf.png"},
            {"id": "forked_twig", "label": "Forked twig", "image": "/icons/forked_twig.png"},
            {"id": "acorn_cap", "label": "Acorn cap", "image": "/icons/acorn_cap.png"},
        ],
    },
    "fluffy_expedition_dandelion": {
        "correct": [
            {"id": "fuzzy_moss", "label": "Fuzzy moss", "image": "/icons/fuzzy_moss.png"},
            {"id": "fluffy_seed", "label": "Fluffy seed head", "image": "/icons/fluffy_seed.png"},
            {"id": "soft_petal", "label": "Soft petal", "image": "/icons/soft_petal.png"},
            {"id": "woolly_caterpillar", "label": "Woolly caterpillar", "image": "/icons/woolly_caterpillar.png"},
        ],
        "distractors": [
            {"id": "hard_rock", "label": "Hard rock", "image": "/icons/hard_rock.png"},
            {"id": "spiky_pinecone", "label": "Spiky pinecone", "image": "/icons/spiky_pinecone.png"},
            {"id": "rough_bark", "label": "Rough bark", "image": "/icons/rough_bark.png"},
            {"id": "sharp_thorn", "label": "Sharp thorn", "image": "/icons/sharp_thorn.png"},
            {"id": "dry_leaf", "label": "Dry crunchy leaf", "image": "/icons/dry_leaf.png"},
            {"id": "smooth_pebble", "label": "Smooth pebble", "image": "/icons/smooth_pebble.png"},
            {"id": "stiff_branch", "label": "Stiff branch", "image": "/icons/stiff_branch.png"},
            {"id": "brittle_shell", "label": "Brittle shell", "image": "/icons/brittle_shell.png"},
        ],
    },
}


def generate_round_items(activity_type: str, total_rounds: int) -> list[list[dict]]:
    """Generate per-round item sets: 1 correct + 2 distractors per round."""
    catalog = COLLECTION_CATALOGS.get(activity_type)
    if not catalog:
        return []
    correct = list(catalog["correct"])
    distractors = list(catalog["distractors"])
    random.shuffle(correct)
    random.shuffle(distractors)

    rounds: list[list[dict]] = []
    dist_idx = 0
    for r in range(total_rounds):
        correct_item = {**correct[r % len(correct)], "correct": True}
        items: list[dict] = [correct_item]
        items.extend(distractors[dist_idx : dist_idx + 2])
        dist_idx += 2
        random.shuffle(items)
        rounds.append(items)
    return rounds


# --- Endpoints ---


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


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
            first_turn = await _generate_with_retry(script_agent, state)

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

    await log_turn(
        settings.db_path,
        req.session_id,
        state.turn_count,
        "ai",
        result.turn_response.dialogue,
        response_type,
        is_silent=req.is_silent,
        consecutive_silence=state.consecutive_silence,
    )

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
    and returns a binary response: [4-byte JSON length][JSON][PCM audio chunks].

    This eliminates the round-trip between /api/turn and /api/tts, and allows
    TTS generation to overlap with Script Agent completion.
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

        await log_turn(
            settings.db_path,
            req.session_id,
            state.turn_count,
            "ai",
            result.turn_response.dialogue,
            response_type,
            is_silent=req.is_silent,
            consecutive_silence=state.consecutive_silence,
        )

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

        # Stream TTS audio
        async for chunk in synthesize_speech_stream_async(result.turn_response.dialogue, state.tier):
            yield chunk

    return StreamingResponse(
        _stream(),
        media_type="application/octet-stream",
        headers={"X-Sample-Rate": str(SAMPLE_RATE)},
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
    return StreamingResponse(
        synthesize_speech_stream_async(req.text, req.tier),
        media_type="audio/pcm",
        headers={"X-Sample-Rate": str(24000)},
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

    if state.round_items and state.current_step.startswith("STEP_3_COLLECT_"):
        round_idx = _step_round_number(state.current_step) - 1
        if 0 <= round_idx < len(state.round_items):
            result["current_round_items"] = [
                {"id": item["id"], "label": item["label"], "image": item.get("image", "")}
                for item in state.round_items[round_idx]
            ]

    return result
