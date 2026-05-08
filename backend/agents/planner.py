"""Planner Agent — structured turn planning using Qwen via DashScope.

The Planner is the first pass in the two-pass generation architecture.
It sees full context (conversation history, state, child's words, collected
characters) and outputs a structured TurnPlan JSON describing WHAT the
response should contain. The Speaker (second pass) then converts the plan
into natural child-facing dialogue.
"""

import time
from pathlib import Path

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_plan import TurnPlan
    from .script_agent import (
        _build_conversation_context,
        _build_creative_slots_text,
        _get_client,
        _load_step_instructions,
        _load_tier_constraints,
    )
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_plan import TurnPlan

    from agents.script_agent import (
        _build_conversation_context,
        _build_creative_slots_text,
        _get_client,
        _load_step_instructions,
        _load_tier_constraints,
    )

logger = setup_logger(__name__)

_PLANNER_PROMPT_PATH = Path(__file__).parent.parent / "skills" / "planner_system.md"


class PlannerError(Exception):
    """Raised when the Planner Agent fails to produce a valid TurnPlan."""


def _build_state_context(state: SessionStateModel) -> str:
    """Build a compact state summary for the planner prompt.

    Args:
        state: Full session state.

    Returns:
        Multi-line string with current step, phase, round, tier, collected
        characters, and game-specific context.
    """
    lines = [
        f"Step: {state.current_step}",
        f"Tier: {state.tier}",
        f"Template: {state.template_type}",
        f"Round: {state.current_round} of {state.total_rounds}",
        f"Turn count: {state.turn_count}",
        f"Entity: {state.entity_name} ({state.entity_category})",
        f"Consecutive silence: {state.consecutive_silence}",
    ]

    # Tier constraints
    lines.append("")
    lines.append(_load_tier_constraints(state.tier))

    # Collected characters and details (Cat5)
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        collected_count = len(state.collected_photos)
        remaining_count = max(0, state.total_rounds - collected_count)
        collected_names_str = ", ".join(state.collected_names) if state.collected_names else "(none yet)"
        collected_details_str = "; ".join(state.collected_details) if state.collected_details else "(none yet)"

        lines.append("")
        lines.append(f"Collection phase: {state.collection_phase}")
        lines.append(f"Collected: {collected_count} of {state.total_rounds}")
        lines.append(f"Remaining: {remaining_count}")
        lines.append(f"Named characters: {collected_names_str}")
        lines.append(f"Collected details: {collected_details_str}")
        lines.append(f"Observation angle: {state.creative_slots.observation_angle}")
        lines.append(f"Collection criterion: {state.creative_slots.collection_criterion}")
        lines.append(f"Naming prompt: {state.creative_slots.naming_prompt}")

    # Creative slots summary
    lines.append("")
    lines.append("Creative Slots:")
    lines.append(_build_creative_slots_text(state.creative_slots))

    # Step instructions — tells the planner what this step is about
    lines.append("")
    lines.append("## Step Instructions")
    lines.append(_load_step_instructions(state))

    return "\n".join(lines)


def _build_planner_system_prompt(state: SessionStateModel) -> str:
    """Load the planner template and fill in state context and conversation history.

    Args:
        state: Full session state.

    Returns:
        Completed system prompt string.
    """
    template = _PLANNER_PROMPT_PATH.read_text() if _PLANNER_PROMPT_PATH.exists() else ""

    replacements = {
        "{state_context}": _build_state_context(state),
        "{conversation_history}": _build_conversation_context(state),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


def _build_planner_user_prompt(state: SessionStateModel) -> str:
    """Build the user message that triggers the planner LLM to produce a TurnPlan.

    Args:
        state: Full session state.

    Returns:
        User prompt string requesting a structured plan.
    """
    child_input = "(silence — no input)"
    if state.conversation_history:
        last = state.conversation_history[-1]
        if last.role == "child":
            child_input = f'"{last.text}"'

    return (
        f"The child said: {child_input}\n\n"
        f"Plan the next turn for step {state.current_step}, "
        f"round {state.current_round} of {state.total_rounds}.\n\n"
        f"Output a JSON object matching the TurnPlan schema."
    )


class Planner:
    """Plans structured turn content using Qwen via DashScope.

    The Planner outputs a TurnPlan JSON that describes what the AI response
    should contain — items to celebrate, question types, characters to
    reference, constraints to enforce — without generating any child-facing
    language.
    """

    async def plan_turn(self, state: SessionStateModel) -> TurnPlan:
        """Generate a structured TurnPlan from session state.

        Args:
            state: Full session state including creative slots, conversation
                history, and collection progress.

        Returns:
            TurnPlan with content decisions and constraints.

        Raises:
            PlannerError: If the planner LLM call fails or returns invalid JSON.
        """
        settings = get_settings()
        start = time.perf_counter()

        system_prompt = _build_planner_system_prompt(state)
        user_prompt = _build_planner_user_prompt(state)

        try:
            client = _get_client()

            response = await client.chat.completions.create(
                model=settings.dashscope_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.planner_temperature,
                max_tokens=settings.planner_max_tokens,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            text = response.choices[0].message.content or ""
            if not text:
                raise PlannerError("Empty response from Planner LLM")

            logger.info(
                f"Planner LLM response: step={state.current_step}, round={state.current_round}, "
                f"activity={state.activity_type}\n--- PLANNER RAW ---\n{text}\n--- END ---"
            )

            plan = TurnPlan.model_validate_json(text)

            logger.info(f"Planner turn: step={state.current_step}, round={state.current_round}, latency={latency_ms}ms")
            await log_agent_call(state.session_id, "planner", latency_ms, True)
            return plan

        except PlannerError:
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Planner Agent failed ({latency_ms}ms): {e}")
            await log_agent_call(state.session_id, "planner", latency_ms, False, error_message=str(e))
            raise PlannerError(f"Plan generation failed: {e}") from e
