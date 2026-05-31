"""Shared dataclasses used across the turn-handling package."""

from dataclasses import dataclass

try:
    from ..schemas import ScreenFrame
    from ..schemas.turn_response import TurnResponse
except ImportError:
    from schemas import ScreenFrame
    from schemas.turn_response import TurnResponse


@dataclass
class TurnInput:
    """Encapsulates raw input from one child turn."""

    text: str = ""
    is_silent: bool = False
    photo_id: str | None = None
    is_selection: bool = False


@dataclass
class GenerationDebugInfo:
    """Debug telemetry captured during a single _generate_with_retry call."""

    step: str
    attempt_count: int
    final_verdict: str  # "passed", "exhausted", "error_fallback"
    attempts: list[dict]  # [{attempt, verdict, hint, latency_ms, call_type}]


@dataclass
class TurnResult:
    """The resolved outcome of one turn, ready for the endpoint to serialize."""

    turn_response: TurnResponse
    screen_frame: ScreenFrame
    auto_advance: bool
    response_type: str
    error_exit: bool = False
    debug: dict | None = None
