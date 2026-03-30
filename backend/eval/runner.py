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


def _extract_dialogue(data: dict) -> str:
    if "first_turn" in data:
        return data["first_turn"].get("dialogue", "")
    return data.get("turn", {}).get("dialogue", "")


def _extract_state(data: dict) -> dict:
    return data.get("session_state", {})


def _score_turn(
    dialogue: str,
    step: str,
    tier: str,
    phase: str,
    is_first: bool,
    collected: int,
    total: int,
) -> dict[str, float]:
    return {
        "validation_pass": score_validation_pass(dialogue, step, tier, phase, is_first),
        "item_suggestion_free": score_item_suggestion_free(dialogue),
        "completion_language": score_completion_language(dialogue, collected, total),
        "tier_compliance": score_tier_compliance(dialogue, tier),
    }


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
    assert resp.status_code == 200, f"Start failed: {resp.status_code}"
    data = resp.json()

    session_id = data["session_id"]
    dialogue = _extract_dialogue(data)
    state = _extract_state(data)

    turns: list[TurnRecord] = []
    progress_phrases: list[str] = []
    validation_scores: list[float] = []
    item_scores: list[float] = []
    completion_scores: list[float] = []
    compliance_scores: list[float] = []
    prev_step = ""

    step = state.get("current_step", "STEP_1_HOOK")
    rule = _score_turn(
        dialogue, step, tier, state.get("collection_phase", "photo"), True, 0, state.get("total_rounds", 3)
    )
    turns.append(
        TurnRecord(
            turn_number=0,
            step=step,
            ai_dialogue=dialogue,
            child_input=ChildSimResponse(),
            session_state=state,
            rule_scores=rule,
        )
    )
    validation_scores.append(rule["validation_pass"])
    item_scores.append(rule["item_suggestion_free"])
    completion_scores.append(rule["completion_language"])
    compliance_scores.append(rule["tier_compliance"])
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
            round_items=enriched_items if enriched_items else None,
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
        dialogue = _extract_dialogue(data)
        state = _extract_state(data)
        step = state.get("current_step", "")
        is_first = step != prev_step

        rule = _score_turn(
            dialogue,
            step,
            tier,
            state.get("collection_phase", "photo"),
            is_first,
            len(state.get("collected_photos", [])),
            state.get("total_rounds", 3),
        )

        turns.append(
            TurnRecord(
                turn_number=turn_num,
                step=step,
                ai_dialogue=dialogue,
                child_input=child_resp,
                session_state=state,
                rule_scores=rule,
            )
        )
        validation_scores.append(rule["validation_pass"])
        item_scores.append(rule["item_suggestion_free"])
        completion_scores.append(rule["completion_language"])
        compliance_scores.append(rule["tier_compliance"])

        if step.startswith("STEP_3_COLLECT_"):
            progress_phrases.append(dialogue)

        prev_step = step

    variety = score_phrasing_variety(progress_phrases) if progress_phrases else 1.0
    composite = compute_composite_score(validation_scores, item_scores, completion_scores, compliance_scores, variety)

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
