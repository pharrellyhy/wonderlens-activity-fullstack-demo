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
    from .agents.script_agent import ScriptAgent, ScriptAgentError
    from .config import get_settings
    from .db import init_db, log_session, log_turn, update_session_status
    from .logger import setup_logger
    from .recipe_loader import (
        is_demo_entity,
        load_demo_recipe,
        recipe_to_session_state,
        resolve_turn_from_recipe,
        resolve_wrong_photo_turn,
    )
    from .scenarios import load_scenario, match_scenario
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.turn_response import TurnResponse
    from .state_machine import EARLY_EXIT, get_screen_frame, is_terminal, next_step, step_needs_user_input
    from .stt import transcribe_audio
    from .tts import SAMPLE_RATE, synthesize_speech_stream_async
    from .vision import analyze_image
except ImportError:
    from agents.pipeline import initialize_session
    from agents.script_agent import ScriptAgent, ScriptAgentError
    from config import get_settings
    from db import init_db, log_session, log_turn, update_session_status
    from logger import setup_logger
    from recipe_loader import (
        is_demo_entity,
        load_demo_recipe,
        recipe_to_session_state,
        resolve_turn_from_recipe,
        resolve_wrong_photo_turn,
    )
    from scenarios import load_scenario, match_scenario
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT, ENDED, get_screen_frame, is_terminal, next_step, step_needs_user_input
    from stt import transcribe_audio
    from tts import SAMPLE_RATE, synthesize_speech_stream, synthesize_speech_stream_async
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
            {"id": "spotted_mushroom", "label": "Spotted mushroom"},
            {"id": "dotted_pebble", "label": "Dotted pebble"},
            {"id": "speckled_leaf", "label": "Speckled leaf"},
            {"id": "circle_flower", "label": "Flower with circles"},
        ],
        "distractors": [
            {"id": "straight_stick", "label": "Straight stick"},
            {"id": "plain_bark", "label": "Plain bark"},
            {"id": "long_grass", "label": "Long grass blade"},
            {"id": "smooth_stone", "label": "Smooth stone"},
            {"id": "pine_needle", "label": "Pine needles"},
            {"id": "plain_leaf", "label": "Plain leaf"},
            {"id": "forked_twig", "label": "Forked twig"},
            {"id": "acorn_cap", "label": "Acorn cap"},
        ],
    },
    "fluffy_expedition_dandelion": {
        "correct": [
            {"id": "fuzzy_moss", "label": "Fuzzy moss"},
            {"id": "fluffy_seed", "label": "Fluffy seed head"},
            {"id": "soft_petal", "label": "Soft petal"},
            {"id": "woolly_caterpillar", "label": "Woolly caterpillar"},
        ],
        "distractors": [
            {"id": "hard_rock", "label": "Hard rock"},
            {"id": "spiky_pinecone", "label": "Spiky pinecone"},
            {"id": "rough_bark", "label": "Rough bark"},
            {"id": "sharp_thorn", "label": "Sharp thorn"},
            {"id": "dry_leaf", "label": "Dry crunchy leaf"},
            {"id": "smooth_pebble", "label": "Smooth pebble"},
            {"id": "stiff_branch", "label": "Stiff branch"},
            {"id": "brittle_shell", "label": "Brittle shell"},
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


def _is_correct_collection_photo(state: SessionStateModel, photo_id: str) -> bool:
    """Check if the selected photo matches the current round's correct item."""
    round_num = _step_round_number(state.current_step)
    round_idx = round_num - 1
    if round_idx < 0 or round_idx >= len(state.round_items):
        return True  # no round items — accept anything
    return any(item["id"] == photo_id and item.get("correct", False) for item in state.round_items[round_idx])


def _get_item_label(state: SessionStateModel, photo_id: str) -> str:
    """Look up the display label for a photo_id in the current round's items."""
    round_num = _step_round_number(state.current_step)
    round_idx = round_num - 1
    if 0 <= round_idx < len(state.round_items):
        for item in state.round_items[round_idx]:
            if item["id"] == photo_id:
                return item["label"]
    return photo_id.replace("_", " ")


def _append_child_turn(state: SessionStateModel, text: str, *, include_round_number: bool = True) -> None:
    round_number = state.current_round if include_round_number and state.current_round > 0 else None
    state.conversation_history.append(
        ConversationTurn(
            role="child",
            text=text,
            step=state.current_step,
            round_number=round_number,
        )
    )


def _record_correct_collection_pick(state: SessionStateModel, photo_id: str) -> None:
    state.collected_photos.append(photo_id)
    state.consecutive_wrong = 0
    _append_child_turn(state, f"[collected correct item: {_get_item_label(state, photo_id)}]")


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

        # --- Pre-generated recipe path (demo entities) ---
        if is_demo_entity(filename):
            recipe = load_demo_recipe(activity_type)
            state, first_turn = recipe_to_session_state(recipe, session_id, tier, filename)

            if state.template_type == "cat5":
                state.round_items = generate_round_items(state.activity_type, state.total_rounds)

            await log_session(settings.db_path, session_id, tier, activity_type)
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
                f"Pre-gen session started: {session_id}, activity={activity_type}, "
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

    # Handle consecutive silence → graceful exit
    if req.is_silent:
        state.consecutive_silence += 1
    else:
        state.consecutive_silence = 0

    if state.consecutive_silence >= 2:
        state.current_step = EARLY_EXIT
        if state.is_pregenerated:
            turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
        else:
            turn_response = await _generate_turn_with_retry(script_agent, state)
        state.status = "exited"

        screen_frame = get_screen_frame(
            EARLY_EXIT,
            state.template_type,
            state.creative_slots,
            _state_context(state),
            visual_frames=state.visual_frames or None,
            celebration_frame=state.celebration_frame,
        )

        state.conversation_history.append(ConversationTurn(role="ai", text=turn_response.dialogue, step=EARLY_EXIT))

        await update_session_status(settings.db_path, req.session_id, "exited", "consecutive_silence", state.turn_count)
        await log_turn(
            settings.db_path,
            req.session_id,
            state.turn_count,
            "ai",
            turn_response.dialogue,
            "graceful_exit",
            is_silent=req.is_silent,
            consecutive_silence=state.consecutive_silence,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return JSONResponse(
            {
                "turn": _build_turn_response(turn_response, screen_frame, "graceful_exit"),
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        )

    # Record child input in conversation history
    if req.text or req.is_silent:
        child_text = req.text if req.text else "..."
        _append_child_turn(state, child_text)

    # For Cat 5 collection: validate photo_id before advancing
    collection_wrong = False
    if req.photo_id and state.current_step.startswith("STEP_3_COLLECT_"):
        if _is_correct_collection_photo(state, req.photo_id):
            _record_correct_collection_pick(state, req.photo_id)
        else:
            collection_wrong = True
            state.consecutive_wrong += 1

    # 2 consecutive wrong picks → graceful exit
    if state.consecutive_wrong >= 2:
        state.current_step = EARLY_EXIT
        if state.is_pregenerated:
            turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
        else:
            turn_response = await _generate_turn_with_retry(script_agent, state)
        state.status = "exited"
        screen_frame = get_screen_frame(
            EARLY_EXIT,
            state.template_type,
            state.creative_slots,
            _state_context(state),
            visual_frames=state.visual_frames or None,
            celebration_frame=state.celebration_frame,
        )
        state.conversation_history.append(ConversationTurn(role="ai", text=turn_response.dialogue, step=EARLY_EXIT))
        await update_session_status(settings.db_path, req.session_id, "exited", "wrong_photos", state.turn_count)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return JSONResponse(
            {
                "turn": _build_turn_response(turn_response, screen_frame, "graceful_exit"),
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        )

    # Wrong pick but not exit yet — stay on same step, generate "try again" response
    if collection_wrong:
        _append_child_turn(state, f"[selected wrong photo: {req.photo_id}]", include_round_number=False)
        if state.is_pregenerated:
            turn_response = resolve_wrong_photo_turn(state, req.photo_id)
        else:
            turn_response = await _generate_turn_with_retry(script_agent, state)
        screen_frame = get_screen_frame(
            state.current_step,
            state.template_type,
            state.creative_slots,
            _state_context(state),
            visual_frames=state.visual_frames or None,
            celebration_frame=state.celebration_frame,
        )
        state.conversation_history.append(
            ConversationTurn(role="ai", text=turn_response.dialogue, step=state.current_step)
        )
        state.turn_count += 1
        await log_turn(
            settings.db_path,
            req.session_id,
            state.turn_count,
            "ai",
            turn_response.dialogue,
            "wrong_photo",
            is_silent=False,
        )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        turn_data = _build_turn_response(turn_response, screen_frame, "wrong_photo")
        turn_data["auto_advance"] = False
        return JSONResponse(
            {
                "turn": turn_data,
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        )

    # Advance the state machine and keep round display/prompt state aligned with the active step.
    state.current_step = next_step(state.current_step, state.template_type, state.current_round, state.total_rounds)
    _sync_round_from_step(state)

    # Check if session ended
    if is_terminal(state.current_step):
        state.status = "completed"
        await update_session_status(settings.db_path, req.session_id, "completed", "all_steps_done", state.turn_count)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return JSONResponse(
            {
                "turn": {
                    "dialogue": "",
                    "response_type": "ended",
                    "screen_frame": None,
                    "audio": {},
                },
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        )

    # Generate AI response for current step
    if state.is_pregenerated:
        turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
    else:
        turn_response = await _generate_turn_with_retry(script_agent, state)

    # Get screen frame from state machine (with Visual Agent frames if available)
    screen_frame = get_screen_frame(
        state.current_step,
        state.template_type,
        state.creative_slots,
        _state_context(state),
        visual_frames=state.visual_frames or None,
        celebration_frame=state.celebration_frame,
    )

    error_exit = state.status == "error"
    response_type = "error" if error_exit else _get_response_type(state.current_step)

    # Record AI response in conversation history
    state.conversation_history.append(
        ConversationTurn(
            role="ai",
            text=turn_response.dialogue,
            step=state.current_step,
            round_number=state.current_round if state.current_round > 0 else None,
        )
    )

    # Trim history to last 6 entries for prompt management
    if len(state.conversation_history) > 6:
        state.conversation_history = state.conversation_history[-6:]

    state.turn_count += 1

    if _is_closing_step(state.current_step) and not error_exit:
        state.status = "completed"
        await update_session_status(
            settings.db_path, req.session_id, "completed", "closing_delivered", state.turn_count
        )

    # Determine if this is an auto-advance step (frontend should auto-send next turn)
    auto_advance = _should_auto_advance(state, error_exit)

    await log_turn(
        settings.db_path,
        req.session_id,
        state.turn_count,
        "ai",
        turn_response.dialogue,
        response_type,
        is_silent=req.is_silent,
        consecutive_silence=state.consecutive_silence,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    turn_data = _build_turn_response(turn_response, screen_frame, response_type, error_exit)
    turn_data["auto_advance"] = auto_advance

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

        # --- State management (same as /api/turn) ---

        if req.is_silent:
            state.consecutive_silence += 1
        else:
            state.consecutive_silence = 0

        # Handle consecutive silence → graceful exit
        if state.consecutive_silence >= 2:
            state.current_step = EARLY_EXIT
            if state.is_pregenerated:
                turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
            else:
                turn_response = await _generate_turn_with_retry(script_agent, state)
            state.status = "exited"
            screen_frame = get_screen_frame(
                EARLY_EXIT,
                state.template_type,
                state.creative_slots,
                _state_context(state),
                visual_frames=state.visual_frames or None,
                celebration_frame=state.celebration_frame,
            )
            state.conversation_history.append(ConversationTurn(role="ai", text=turn_response.dialogue, step=EARLY_EXIT))
            await update_session_status(
                settings.db_path, req.session_id, "exited", "consecutive_silence", state.turn_count
            )
            await log_turn(
                settings.db_path,
                req.session_id,
                state.turn_count,
                "ai",
                turn_response.dialogue,
                "graceful_exit",
                is_silent=req.is_silent,
                consecutive_silence=state.consecutive_silence,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            turn_data = _build_turn_response(turn_response, screen_frame, "graceful_exit")
            response_json = json.dumps(
                {"turn": turn_data, "session_state": _session_state_dict(state), "latency_ms": latency_ms}
            ).encode()
            yield struct.pack(">I", len(response_json))
            yield response_json
            # Stream TTS audio
            async for chunk in synthesize_speech_stream_async(turn_response.dialogue, state.tier):
                yield chunk
            return

        # Record child input
        if req.text or req.is_silent:
            child_text = req.text if req.text else "..."
            _append_child_turn(state, child_text)

        # Cat 5 collection validation
        collection_wrong = False
        if req.photo_id and state.current_step.startswith("STEP_3_COLLECT_"):
            if _is_correct_collection_photo(state, req.photo_id):
                _record_correct_collection_pick(state, req.photo_id)
            else:
                collection_wrong = True
                state.consecutive_wrong += 1

        # 2 consecutive wrong picks → graceful exit
        if state.consecutive_wrong >= 2:
            state.current_step = EARLY_EXIT
            if state.is_pregenerated:
                turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
            else:
                turn_response = await _generate_turn_with_retry(script_agent, state)
            state.status = "exited"
            screen_frame = get_screen_frame(
                EARLY_EXIT,
                state.template_type,
                state.creative_slots,
                _state_context(state),
                visual_frames=state.visual_frames or None,
                celebration_frame=state.celebration_frame,
            )
            state.conversation_history.append(ConversationTurn(role="ai", text=turn_response.dialogue, step=EARLY_EXIT))
            await update_session_status(settings.db_path, req.session_id, "exited", "wrong_photos", state.turn_count)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            turn_data = _build_turn_response(turn_response, screen_frame, "graceful_exit")
            response_json = json.dumps(
                {"turn": turn_data, "session_state": _session_state_dict(state), "latency_ms": latency_ms}
            ).encode()
            yield struct.pack(">I", len(response_json))
            yield response_json
            async for chunk in synthesize_speech_stream_async(turn_response.dialogue, state.tier):
                yield chunk
            return

        # Wrong pick but not exit yet — stay on same step
        if collection_wrong:
            _append_child_turn(state, f"[selected wrong photo: {req.photo_id}]", include_round_number=False)
            if state.is_pregenerated:
                turn_response = resolve_wrong_photo_turn(state, req.photo_id)
            else:
                turn_response = await _generate_turn_with_retry(script_agent, state)
            screen_frame = get_screen_frame(
                state.current_step,
                state.template_type,
                state.creative_slots,
                _state_context(state),
                visual_frames=state.visual_frames or None,
                celebration_frame=state.celebration_frame,
            )
            state.conversation_history.append(
                ConversationTurn(role="ai", text=turn_response.dialogue, step=state.current_step)
            )
            state.turn_count += 1
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            turn_data = _build_turn_response(turn_response, screen_frame, "wrong_photo")
            turn_data["auto_advance"] = False
            response_json = json.dumps(
                {"turn": turn_data, "session_state": _session_state_dict(state), "latency_ms": latency_ms}
            ).encode()
            yield struct.pack(">I", len(response_json))
            yield response_json
            async for chunk in synthesize_speech_stream_async(turn_response.dialogue, state.tier):
                yield chunk
            return

        state.current_step = next_step(state.current_step, state.template_type, state.current_round, state.total_rounds)
        _sync_round_from_step(state)

        # Terminal check
        if is_terminal(state.current_step):
            state.status = "completed"
            await update_session_status(
                settings.db_path, req.session_id, "completed", "all_steps_done", state.turn_count
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            response_json = json.dumps(
                {
                    "turn": {"dialogue": "", "response_type": "ended", "screen_frame": None, "audio": {}},
                    "session_state": _session_state_dict(state),
                    "latency_ms": latency_ms,
                }
            ).encode()
            yield struct.pack(">I", len(response_json))
            yield response_json
            return

        # --- Pre-generated recipe: skip streaming, go straight to TTS ---
        if state.is_pregenerated:
            turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)

            screen_frame = get_screen_frame(
                state.current_step,
                state.template_type,
                state.creative_slots,
                _state_context(state),
                visual_frames=state.visual_frames or None,
                celebration_frame=state.celebration_frame,
            )
            error_exit = state.status == "error"
            response_type = "error" if error_exit else _get_response_type(state.current_step)

            state.conversation_history.append(
                ConversationTurn(
                    role="ai",
                    text=turn_response.dialogue,
                    step=state.current_step,
                    round_number=state.current_round if state.current_round > 0 else None,
                )
            )
            if len(state.conversation_history) > 6:
                state.conversation_history = state.conversation_history[-6:]

            state.turn_count += 1

            if _is_closing_step(state.current_step) and not error_exit:
                state.status = "completed"
                await update_session_status(
                    settings.db_path, req.session_id, "completed", "closing_delivered", state.turn_count
                )

            auto_advance = _should_auto_advance(state, error_exit)

            await log_turn(
                settings.db_path,
                req.session_id,
                state.turn_count,
                "ai",
                turn_response.dialogue,
                response_type,
                is_silent=req.is_silent,
                consecutive_silence=state.consecutive_silence,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            turn_data = _build_turn_response(turn_response, screen_frame, response_type, error_exit)
            turn_data["auto_advance"] = auto_advance

            response_json = json.dumps(
                {"turn": turn_data, "session_state": _session_state_dict(state), "latency_ms": latency_ms}
            ).encode()
            yield struct.pack(">I", len(response_json))
            yield response_json
            async for chunk in synthesize_speech_stream_async(turn_response.dialogue, state.tier):
                yield chunk
            return

        # --- Streaming Script Agent + pipelined TTS ---

        dialogue_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1)
        tts_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

        async def on_dialogue(text: str) -> None:
            await dialogue_queue.put(text)

        async def tts_producer(dialogue_text: str, audio_queue: asyncio.Queue[bytes | None]) -> None:
            """Produce TTS audio chunks into the queue."""
            try:
                async for chunk in synthesize_speech_stream_async(dialogue_text, state.tier):
                    await audio_queue.put(chunk)
            except Exception as e:
                logger.error(f"TTS producer failed: {e}")
            await audio_queue.put(None)  # sentinel

        # Start Script Agent streaming (extracts dialogue early via callback)
        script_task = asyncio.create_task(script_agent.generate_turn_streaming(state, on_dialogue=on_dialogue))

        # Wait for early dialogue extraction OR script completion
        tts_task = None
        tts_text = None
        try:
            dialogue_text = await asyncio.wait_for(dialogue_queue.get(), timeout=30)
            # Start TTS immediately — overlaps with remaining Script Agent generation
            tts_text = dialogue_text
            tts_task = asyncio.create_task(tts_producer(dialogue_text, tts_queue))
        except (asyncio.TimeoutError, Exception):
            pass

        # Wait for Script Agent to finish
        try:
            turn_response = await script_task
        except ScriptAgentError:
            logger.warning(f"Streaming Script Agent failed for {state.current_step}, retrying non-streaming")
            try:
                turn_response = await script_agent.generate_turn(state)
            except ScriptAgentError:
                logger.error(f"Script Agent retry failed for {state.current_step}, using fallback")
                state.status = "error"
                turn_response = TurnResponse(
                    dialogue="(gentle) That was so much fun! Let's play again next time. See you soon!",
                    tone_marker="gentle",
                    screen_widget="badge_award",
                    screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
                    screen_animation="badge_reveal",
                    sfx_cue="badge_awarded",
                )

        # If early dialogue differs from the final turn, restart TTS with the canonical text.
        if tts_task is not None and tts_text != turn_response.dialogue:
            tts_task.cancel()
            try:
                await tts_task
            except asyncio.CancelledError:
                pass
            tts_queue = asyncio.Queue()
            tts_task = None

        # If TTS wasn't started yet, or we canceled a stale early stream, start it now.
        if tts_task is None:
            tts_text = turn_response.dialogue
            tts_task = asyncio.create_task(tts_producer(turn_response.dialogue, tts_queue))

        # --- Post-processing ---

        screen_frame = get_screen_frame(
            state.current_step,
            state.template_type,
            state.creative_slots,
            _state_context(state),
            visual_frames=state.visual_frames or None,
            celebration_frame=state.celebration_frame,
        )
        error_exit = state.status == "error"
        response_type = "error" if error_exit else _get_response_type(state.current_step)

        state.conversation_history.append(
            ConversationTurn(
                role="ai",
                text=turn_response.dialogue,
                step=state.current_step,
                round_number=state.current_round if state.current_round > 0 else None,
            )
        )
        if len(state.conversation_history) > 6:
            state.conversation_history = state.conversation_history[-6:]

        state.turn_count += 1

        if _is_closing_step(state.current_step) and not error_exit:
            state.status = "completed"
            await update_session_status(
                settings.db_path, req.session_id, "completed", "closing_delivered", state.turn_count
            )

        auto_advance = _should_auto_advance(state, error_exit)

        await log_turn(
            settings.db_path,
            req.session_id,
            state.turn_count,
            "ai",
            turn_response.dialogue,
            response_type,
            is_silent=req.is_silent,
            consecutive_silence=state.consecutive_silence,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        turn_data = _build_turn_response(turn_response, screen_frame, response_type, error_exit)
        turn_data["auto_advance"] = auto_advance

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

        # Yield TTS audio chunks (already being produced in background)
        while True:
            chunk = await tts_queue.get()
            if chunk is None:
                break
            yield chunk

        await tts_task

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


async def _generate_turn_with_retry(script_agent: ScriptAgent, state: SessionStateModel) -> TurnResponse:
    """Generate a turn response with one retry on failure, then graceful exit."""
    try:
        return await script_agent.generate_turn(state)
    except ScriptAgentError:
        logger.warning(f"Script Agent failed for step {state.current_step}, retrying")
        try:
            return await script_agent.generate_turn(state)
        except ScriptAgentError:
            logger.error(f"Script Agent failed twice for step {state.current_step}, using fallback")
            state.status = "error"
            return TurnResponse(
                dialogue="(gentle) That was so much fun! Let's play again next time. See you soon!",
                tone_marker="gentle",
                screen_widget="badge_award",
                screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
                screen_animation="badge_reveal",
                sfx_cue="badge_awarded",
            )


def _build_turn_response(
    turn: TurnResponse,
    screen_frame: ScreenFrame,
    response_type: str,
    error_exit: bool = False,
) -> dict:
    """Build the turn response dict for the API."""
    audio: dict = {"sfx": turn.sfx_cue}
    if screen_frame.sfx_label:
        audio["sfx_label"] = screen_frame.sfx_label
    return {
        "dialogue": turn.dialogue,
        "tone_marker": turn.tone_marker,
        "screen_frame": screen_frame.model_dump(),
        "audio": audio,
        "response_type": response_type,
        "error_exit": error_exit,
    }


def _get_response_type(step: str) -> str:
    """Map a step to a response type string."""
    if step == "STEP_1_HOOK":
        return "hook"
    if step in ("STEP_2_RULES", "STEP_2_MISSION"):
        return "rules"
    if step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        return "round"
    if step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        return "celebration"
    if step in ("STEP_4_SYNTHESIS",):
        return "synthesis"
    if step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        return "closing"
    if step == EARLY_EXIT:
        return "graceful_exit"
    return "response"


def _is_closing_step(step: str) -> bool:
    """Return True when the active step is the final closing response."""
    return step in {"STEP_5_CLOSING", "STEP_6_CLOSING"}


def _should_auto_advance(state: SessionStateModel, error_exit: bool = False) -> bool:
    """Auto-advance only active non-closing presentation steps."""
    return (
        state.status == "active"
        and not error_exit
        and not step_needs_user_input(state.current_step)
        and not _is_closing_step(state.current_step)
    )


def _state_context(state: SessionStateModel) -> dict:
    """Build a context dict from session state for screen frame generation."""
    return {
        "entity_name": state.entity_name,
        "entity": state.entity_name,
        "ib_key_concepts": state.ib_key_concepts,
        "key_concepts": state.ib_key_concepts,
    }


def _sync_round_from_step(state: SessionStateModel) -> None:
    """Keep current_round aligned with the active round/collect step."""
    if state.current_step.startswith("STEP_3_ROUND_") or state.current_step.startswith("STEP_3_COLLECT_"):
        state.current_round = _step_round_number(state.current_step)


def _step_round_number(step: str) -> int:
    """Extract a 1-based round number from a round/collect step."""
    return int(step.rsplit("_", maxsplit=1)[-1])


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
                {"id": item["id"], "label": item["label"]} for item in state.round_items[round_idx]
            ]

    return result
