"""Debug payload helpers for turn handling.

Extracted verbatim from turn_handler.py during package decomposition.
"""

from dataclasses import asdict

try:
    from ..agents.script_agent import ScriptAgent
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import EARLY_EXIT
except ImportError:
    from agents.script_agent import ScriptAgent
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT

from .generation import get_retry_stats
from .helpers import _MAX_DETAIL_EXCHANGES
from .types import GenerationDebugInfo


def _build_step_flow(state: SessionStateModel) -> list[dict]:
    """Build the ordered step flow for the current session, marking each step's status."""
    if state.template_type == "cat1":
        steps = ["STEP_1_HOOK", "STEP_2_RULES"]
        steps += [f"STEP_3_ROUND_{i}" for i in range(1, state.total_rounds + 1)]
        steps += ["STEP_4_CELEBRATE", "STEP_5_CLOSING"]
    else:
        steps = ["STEP_1_HOOK", "STEP_2_MISSION"]
        steps += [f"STEP_3_COLLECT_{i}" for i in range(1, state.total_rounds + 1)]
        steps += ["STEP_4_SYNTHESIS", "STEP_5_CELEBRATE", "STEP_6_CLOSING"]

    # Terminal states: mark all steps done and append the terminal marker
    if state.current_step in (EARLY_EXIT, "ENDED"):
        flow = [{"step": s, "status": "done"} for s in steps]
        flow.append({"step": state.current_step, "status": "current"})
        return flow

    flow: list[dict] = []
    found_current = False
    for s in steps:
        if s == state.current_step:
            flow.append({"step": s, "status": "current"})
            found_current = True
        elif not found_current:
            flow.append({"step": s, "status": "done"})
        else:
            flow.append({"step": s, "status": "pending"})
    return flow


def _build_phase_timeline(state: SessionStateModel) -> list[dict] | None:
    """Build a sub-step phase timeline for steps with internal state machines."""
    step = state.current_step

    if state.template_type == "cat5" and step.startswith("STEP_3_COLLECT"):
        return _phase_timeline_cat5_collection(state)

    if state.template_type == "cat5" and step == "STEP_4_SYNTHESIS":
        return _phase_timeline_cat5_synthesis(state)

    if state.template_type == "cat1" and step == "STEP_2_RULES":
        return _phase_timeline_cat1_invitation(state)

    return None


def _phase_timeline_cat5_collection(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 collection loop: photo -> detail(1..max)."""
    max_detail = _MAX_DETAIL_EXCHANGES.get(state.tier, 3)
    in_detail = state.collection_phase == "detail"
    exchange = state.detail_exchange_count
    # cursor = how many detail slots are complete (0 when still on photo)
    cursor = exchange + (1 if state.round_advance_pending else 0) if in_detail else -1

    timeline: list[dict] = [
        {"phase": "photo", "status": "done" if in_detail else "current", "label": "Photo", "meta": None}
    ]

    for i in range(1, max_detail + 1):
        status = "done" if i <= cursor else ("current" if i == cursor + 1 and in_detail else "pending")
        meta = {"round_advance_pending": state.round_advance_pending} if i == max_detail else None
        timeline.append({"phase": "detail", "status": status, "label": f"Detail {i}/{max_detail}", "meta": meta})

    return timeline


def _phase_timeline_cat5_synthesis(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 synthesis loop: invite -> evaluate -> improve? -> generate."""
    ordered = ["invite", "evaluate"]
    if state.tier in ("T1", "T2"):
        ordered.append("improve")
    ordered.append("generate")

    current_idx = ordered.index(state.synthesis_phase) if state.synthesis_phase in ordered else 0

    timeline: list[dict] = []
    for i, phase in enumerate(ordered):
        status = "done" if i < current_idx else ("current" if i == current_idx else "pending")

        meta: dict | None = None
        if i == current_idx and phase != "invite":
            meta = {"prompt_count": state.synthesis_prompt_count}
            if phase in ("evaluate", "improve") and state.synthesis_story_quality:
                meta["story_quality"] = state.synthesis_story_quality

        timeline.append({"phase": phase, "status": status, "label": phase.capitalize(), "meta": meta})

    return timeline


def _phase_timeline_cat1_invitation(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat1 invitation: invite -> decline 1 -> decline 2."""
    if state.invitation_accepted:
        return [{"phase": "invite", "status": "done", "label": "Invite", "meta": {"accepted": True}}]

    declines = state.invitation_decline_count
    timeline: list[dict] = [
        {"phase": "invite", "status": "current" if declines == 0 else "done", "label": "Invite", "meta": None}
    ]
    for i in range(1, declines + 1):
        timeline.append(
            {
                "phase": "decline",
                "status": "current" if i == declines else "done",
                "label": f"Decline {i}",
                "meta": None,
            }
        )
    return timeline


def _build_debug_payload(
    state: SessionStateModel,
    gen_debug: GenerationDebugInfo | None,
    script_agent: ScriptAgent | None = None,
    turn_response: TurnResponse | None = None,
) -> dict:
    """Assemble the debug payload dict for a turn response.

    script_agent is optional: deterministic turn paths (loading screens,
    scene delivery, deterministic invites) don't run the ScriptAgent but
    still need to emit a debug payload so the turn shows up in the History
    tab with correct step_flow / phase_timeline / synthesis state.
    """
    debug: dict = {}

    if gen_debug:
        debug["generation"] = asdict(gen_debug)

    if script_agent is not None:
        plan = script_agent.last_plan
        if plan:
            debug["planner"] = {
                "do_not_suggest_items": plan.do_not_suggest_items,
                "offer_binary_choice": plan.offer_binary_choice,
                "must_model_first": plan.must_model_first,
                "do_not_ask_question": plan.do_not_ask_question,
                "emotion_tag": plan.emotion_tag,
                "question_type": plan.question_type,
            }
        if script_agent.last_best_of_n:
            debug["best_of_n"] = script_agent.last_best_of_n

    if turn_response:
        debug["llm_output"] = {
            "tone_marker": turn_response.tone_marker,
            "stay_on_step": turn_response.stay_on_step,
            "screen_widget": turn_response.screen_widget,
            "sfx_cue": turn_response.sfx_cue,
        }

    # Synthesis loop counters (only when in or past synthesis)
    if state.synthesis_prompt_count > 0 or state.current_step == "STEP_4_SYNTHESIS":
        debug["synthesis"] = {
            "phase": state.synthesis_phase,
            "prompt_count": state.synthesis_prompt_count,
            "story_attempts": state.synthesis_story_attempts,
            "declines": state.synthesis_declines,
            "silences": state.synthesis_silences,
            "unrelated": state.synthesis_unrelated,
            "child_story": state.synthesis_child_story[:100] if state.synthesis_child_story else None,
        }

    debug["retry_stats"] = get_retry_stats()
    debug["step_flow"] = _build_step_flow(state)

    timeline = _build_phase_timeline(state)
    if timeline:
        debug["phase_timeline"] = timeline

    return debug
