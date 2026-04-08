"""Turn handling package — decomposed from the monolithic turn_handler.py.

Public API:
    resolve_turn      — Process one turn (main entry point)
    TurnInput         — Child turn input dataclass
    TurnResult        — Turn result dataclass
    GenerationDebugInfo — Debug telemetry dataclass
    get_retry_stats   — Retry statistics accessor

Internal symbols are re-exported for backward compatibility with tests
and scripts that import private helpers directly.
"""

from .collection import (
    _is_correct_collection_photo,
    _maybe_record_generated_name,
    _record_collection_detail,
)
from .core import resolve_turn
from .debug import (
    _build_debug_payload,
    _build_phase_timeline,
    _build_step_flow,
)
from .generation import (
    _DIRECTIVE_RE,
    _INVITATIONAL_PREFIX_RE,
    _ITEM_SUGGESTION_RE,
    _classify_child_intent,
    _ends_with_open_question,
    _generate_with_retry,
    _has_completion_language,
    _has_model_phrase,
    get_retry_stats,
)
from .helpers import (
    _should_auto_advance,
    _step_round_number,
)
from .types import GenerationDebugInfo, TurnInput, TurnResult

__all__ = [
    "GenerationDebugInfo",
    "TurnInput",
    "TurnResult",
    "get_retry_stats",
    "resolve_turn",
]
