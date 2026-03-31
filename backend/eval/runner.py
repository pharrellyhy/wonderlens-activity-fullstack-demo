"""Eval runner — orchestrates sessions against the live API."""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

_SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from scoring import (
    compute_composite_score,
    score_completion_language,
    score_item_suggestion_free,
    score_phrasing_variety,
    score_tier_compliance,
    score_validation_pass,
)

from eval.child_sim import ChildSimContext, ChildSimulator
from eval.rubrics import (
    ChildSimResponse,
    EvalConfig,
    SessionTranscript,
    TurnRecord,
)

logger = logging.getLogger("wonderlens")

MAX_TURNS = 20


def _extract_turn_data(data: dict) -> tuple[str, dict, bool]:
    """Extract dialogue, session state, and auto_advance from an API response."""
    turn = data.get("first_turn") or data.get("turn", {})
    dialogue = turn.get("dialogue", "")
    auto_advance = turn.get("auto_advance", False)
    state = data.get("session_state", {})
    return dialogue, state, auto_advance


def _score_turn(dialogue: str, step: str, tier: str, state: dict, is_first: bool) -> dict[str, float]:
    """Compute rule-based scores for a single turn's dialogue."""
    return {
        "validation_pass": score_validation_pass(
            dialogue, step, tier, state.get("collection_phase", "photo"), is_first
        ),
        "item_suggestion_free": score_item_suggestion_free(dialogue),
        "completion_language": score_completion_language(
            dialogue, len(state.get("collected_photos", [])), state.get("total_rounds", 3)
        ),
        "tier_compliance": score_tier_compliance(dialogue, tier),
    }


def _record_turn(
    turns: list[TurnRecord],
    turn_num: int,
    step: str,
    dialogue: str,
    tier: str,
    state: dict,
    child_input: ChildSimResponse,
    is_first_on_step: bool = False,
) -> None:
    """Score and append a TurnRecord to the running list."""
    rule = _score_turn(dialogue, step, tier, state, is_first_on_step)
    turns.append(
        TurnRecord(
            turn_number=turn_num,
            step=step,
            ai_dialogue=dialogue,
            child_input=child_input,
            session_state=state,
            rule_scores=rule,
        )
    )


async def run_single_session(
    client: httpx.AsyncClient,
    child_sim: ChildSimulator,
    activity: str,
    tier: str,
    persona_name: str,
    correct_items_by_round: list[list[str]],
    config: EvalConfig,
) -> SessionTranscript:
    """Run one full game session and return the transcript."""
    resp = await client.post(
        f"{config.server_url}/api/start-deep-link",
        json={"entity": activity, "tier": tier},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Start failed: {resp.status_code}")
    data = resp.json()

    session_id = data["session_id"]
    dialogue, state, auto_advance = _extract_turn_data(data)

    turns: list[TurnRecord] = []
    prev_step = ""
    step = state.get("current_step", "STEP_1_HOOK")
    _record_turn(turns, 0, step, dialogue, tier, state, ChildSimResponse(), is_first_on_step=True)
    prev_step = step

    for turn_num in range(1, MAX_TURNS + 1):
        if state.get("status") in ("completed", "exited", "error"):
            break

        api_items = state.get("current_round_items", [])
        round_idx = max(0, len(state.get("collected_photos", [])))
        correct_ids = set(correct_items_by_round[round_idx]) if round_idx < len(correct_items_by_round) else set()
        enriched_items = [{**item, "correct": item["id"] in correct_ids} for item in api_items]

        ctx = ChildSimContext(
            persona=persona_name,
            tier=tier,
            activity_name=activity,
            collection_criterion="",
            current_step=state.get("current_step", ""),
            collection_phase=state.get("collection_phase"),
            round_items=enriched_items or None,
            last_ai_dialogue=dialogue,
            collected_names=state.get("collected_names", []),
            turn_number=turn_num,
        )

        child_resp = await child_sim.generate(ctx)

        body: dict = {"session_id": session_id, "text": child_resp.text, "is_silent": child_resp.is_silent}
        if child_resp.photo_id:
            body["photo_id"] = child_resp.photo_id

        resp = await client.post(f"{config.server_url}/api/turn", json=body)
        if resp.status_code != 200:
            logger.warning("Turn %d failed: %d", turn_num, resp.status_code)
            break

        data = resp.json()
        dialogue, state, auto_advance = _extract_turn_data(data)
        step = state.get("current_step", "")
        _record_turn(turns, turn_num, step, dialogue, tier, state, child_resp, is_first_on_step=step != prev_step)
        prev_step = step

        # Handle auto_advance chain: keep sending empty turns until the
        # backend stops signaling auto_advance (e.g. detail->next round,
        # synthesis->celebrate->closing). Cap at 10 to prevent runaway loops.
        auto_advance_count = 0
        while auto_advance and state.get("status") == "active" and auto_advance_count < 10:
            auto_advance_count += 1
            resp = await client.post(
                f"{config.server_url}/api/turn",
                json={"session_id": session_id, "text": "", "is_silent": False},
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            dialogue, state, auto_advance = _extract_turn_data(data)
            step = state.get("current_step", "")
            _record_turn(
                turns, turn_num, step, dialogue, tier, state, ChildSimResponse(), is_first_on_step=step != prev_step
            )
            prev_step = step

    progress_phrases = [t.ai_dialogue for t in turns if t.step.startswith("STEP_3_COLLECT_")]
    variety = score_phrasing_variety(progress_phrases) if progress_phrases else 1.0
    composite = compute_composite_score(
        [t.rule_scores["validation_pass"] for t in turns],
        [t.rule_scores["item_suggestion_free"] for t in turns],
        [t.rule_scores["completion_language"] for t in turns],
        [t.rule_scores["tier_compliance"] for t in turns],
        variety,
    )

    return SessionTranscript(
        session_id=session_id,
        activity=activity,
        tier=tier,
        persona=persona_name,
        model=config.child_sim_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        correct_items_by_round=correct_items_by_round,
        turns=turns,
        final_status=state.get("status", "unknown"),
        total_turns=len(turns),
        rule_score=composite,
        variety_score=variety,
    )
