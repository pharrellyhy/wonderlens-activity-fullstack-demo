"""FastAPI server for the WonderLens Activity Demo."""

import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

try:
    from .agents.pipeline import generate_recipe
    from .config import get_settings
    from .db import init_db, log_session, log_turn, update_session_status
    from .logger import setup_logger
    from .scenarios import load_scenario, match_scenario
    from .schemas import ActivityRecipe
    from .stt import transcribe_audio
    from .tts import synthesize_speech
    from .vision import analyze_image
except ImportError:
    from agents.pipeline import generate_recipe
    from config import get_settings
    from db import init_db, log_session, log_turn, update_session_status
    from logger import setup_logger
    from scenarios import load_scenario, match_scenario
    from schemas import ActivityRecipe
    from stt import transcribe_audio
    from tts import synthesize_speech
    from vision import analyze_image

logger = setup_logger(__name__)


@dataclass
class SessionState:
    session_id: str
    recipe: ActivityRecipe
    tier: str
    activity_type: str
    current_round: int = 0
    consecutive_silence: int = 0
    status: str = "active"
    turn_count: int = 0
    photo_url: str = ""
    vision_result: dict = field(default_factory=dict)


_sessions: dict[str, SessionState] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
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
)


# --- Request models ---


class TurnRequest(BaseModel):
    session_id: str
    text: str = ""
    is_silent: bool = False


class TTSRequest(BaseModel):
    text: str
    tier: str = "T0"


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

        # 2. Vision analysis
        vision_result = await analyze_image(image_bytes, mime_type)

        # 3. Match scenario
        activity_type = match_scenario(
            vision_result.get("entity", "unknown"),
            vision_result.get("features", []),
        )
        scenario = load_scenario(activity_type)

        # 4. Build pipeline context
        context = {
            "entity": vision_result.get("entity", "unknown"),
            "tier": tier,
            "activity_type": activity_type,
            "scene": vision_result.get("scene", ""),
            "features": vision_result.get("features", []),
            "key_concepts": scenario.get("key_concepts", []),
            "ib_theme": "Who We Are",
        }

        # 5. Run pipeline
        recipe = await generate_recipe(context, session_id)

        # 6. Log session to DB
        await log_session(settings.db_path, session_id, tier, activity_type)

        # 7. Build first turn from recipe
        first_screen_frame = recipe.screen_frames[0].model_dump() if recipe.screen_frames else None
        first_turn = {
            "dialogue": recipe.voice_script.hook_line,
            "screen_frame": first_screen_frame,
            "audio": {"sfx": "wonder_chime"},
            "response_type": "hook",
        }

        # 8. Create session state
        state = SessionState(
            session_id=session_id,
            recipe=recipe,
            tier=tier,
            activity_type=activity_type,
            vision_result=vision_result,
        )
        _sessions[session_id] = state

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"Session started: {session_id}, activity={activity_type}, tier={tier}, latency={latency_ms}ms")

        return JSONResponse(
            {
                "session_id": session_id,
                "vision_result": vision_result,
                "recipe": recipe.model_dump(),
                "first_turn": first_turn,
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

    recipe = state.recipe
    rounds = recipe.voice_script.rounds
    current_round = state.current_round

    # Handle consecutive silence → graceful exit
    if req.is_silent:
        state.consecutive_silence += 1
    else:
        state.consecutive_silence = 0

    if state.consecutive_silence >= 2:
        # Graceful exit
        state.status = "exited"
        dialogue = "That was so fun! Your friend will be here whenever you want to play again. See you next time!"
        screen_frame = recipe.celebration_frame.model_dump() if recipe.celebration_frame else None
        response_type = "graceful_exit"

        await update_session_status(settings.db_path, req.session_id, "exited", "consecutive_silence", state.turn_count)
        await log_turn(
            settings.db_path,
            req.session_id,
            state.turn_count,
            "ai",
            dialogue,
            response_type,
            is_silent=req.is_silent,
            consecutive_silence=state.consecutive_silence,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return JSONResponse(
            {
                "turn": {
                    "dialogue": dialogue,
                    "screen_frame": screen_frame,
                    "audio": {"sfx": "badge_awarded"},
                    "response_type": response_type,
                },
                "session_state": _session_state_dict(state),
                "latency_ms": latency_ms,
            }
        )

    # Normal turn processing
    if current_round >= len(rounds):
        # All rounds complete → closing
        state.status = "completed"
        dialogue = recipe.voice_script.closing_speech
        screen_frame = recipe.celebration_frame.model_dump() if recipe.celebration_frame else None
        response_type = "closing"

        await update_session_status(settings.db_path, req.session_id, "completed", "all_rounds_done", state.turn_count)
    else:
        rnd = rounds[current_round]

        # Match response to branching path
        if req.is_silent:
            dialogue = rnd.on_silence
            response_type = "on_silence"
        elif _matches_correct(req.text, rnd.correct_responses):
            dialogue = rnd.on_correct
            response_type = "on_correct"
            state.current_round += 1
        else:
            dialogue = rnd.on_incorrect
            response_type = "on_incorrect"
            state.current_round += 1  # Advance even on incorrect in demo

        # Get corresponding screen frame (offset by 1 for the initial photo frame)
        frame_idx = min(state.current_round, len(recipe.screen_frames) - 1)
        screen_frame = recipe.screen_frames[frame_idx].model_dump() if recipe.screen_frames else None

        # Check if this was the last round
        if state.current_round >= len(rounds):
            # Next turn will be closing
            pass

    state.turn_count += 1

    await log_turn(
        settings.db_path,
        req.session_id,
        state.turn_count,
        "ai",
        dialogue,
        response_type,
        is_silent=req.is_silent,
        consecutive_silence=state.consecutive_silence,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return JSONResponse(
        {
            "turn": {
                "dialogue": dialogue,
                "screen_frame": screen_frame,
                "audio": {
                    "sfx": rounds[current_round].sfx_cue if current_round < len(rounds) else "celebration_fanfare"
                },
                "response_type": response_type,
            },
            "session_state": _session_state_dict(state),
            "latency_ms": latency_ms,
        }
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
    wav_data = await synthesize_speech(req.text, req.tier)
    if wav_data is None:
        return Response(status_code=204)
    return Response(content=wav_data, media_type="audio/wav")


# --- Helpers ---


def _matches_correct(text: str, correct_responses: list[str]) -> bool:
    """Check if the child's text matches any correct response (case-insensitive substring)."""
    if not correct_responses:
        return True  # Open-ended questions accept everything
    text_lower = text.lower().strip()
    if not text_lower:
        return False
    for response in correct_responses:
        if response.lower() in text_lower or text_lower in response.lower():
            return True
    return False


def _session_state_dict(state: SessionState) -> dict:
    return {
        "status": state.status,
        "current_round": state.current_round,
        "total_rounds": len(state.recipe.voice_script.rounds),
        "consecutive_silence": state.consecutive_silence,
        "turn_count": state.turn_count,
    }
