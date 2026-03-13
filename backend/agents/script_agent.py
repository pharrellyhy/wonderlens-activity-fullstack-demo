"""Script Agent — per-turn dialogue generation using Gemini Flash."""

import json
import re
import time
from functools import lru_cache
from pathlib import Path

import yaml
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import get_step_name
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import get_step_name

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "script_turn.md"
_STEP_INSTRUCTIONS_DIR = Path(__file__).parent.parent / "skills" / "step_instructions"
_TIER_RULES_PATH = Path(__file__).parent.parent / "tier_rules.yaml"

# Regex to extract dialogue value from partial JSON stream
_DIALOGUE_RE = re.compile(r'"dialogue"\s*:\s*"((?:[^"\\]|\\.)*)"')


class ScriptAgentError(Exception):
    """Raised when the Script Agent fails to generate a valid turn."""


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


def _load_tier_constraints(tier: str) -> str:
    """Format tier rules into a readable string for the prompt."""
    if not _TIER_RULES_PATH.exists():
        return f"Tier: {tier}"

    with open(_TIER_RULES_PATH) as f:
        all_rules = yaml.safe_load(f) or {}

    rules = all_rules.get("tiers", {}).get(tier, {})
    if not rules:
        return f"Tier: {tier}"

    return (
        f"Tier: {tier} ({rules.get('label', '')})\n"
        f"Ages: {rules.get('ages', '')}\n"
        f"Words per sentence: {rules.get('words_per_sentence', '')}\n"
        f"Max sentences per turn: {rules.get('max_sentences', '')}\n"
        f"Hook rule: {rules.get('hook_rule', '')} — {rules.get('hook_description', '')}\n"
        f"Closing: {rules.get('closing_speech', '')} — {rules.get('closing_description', '')}\n"
        f"Tone: {rules.get('tone', '')}\n"
        f"Response style: {rules.get('response_style', '')}\n"
        f"Round count range: {rules.get('pathway_rounds', '')}\n"
        f"Available concepts: {rules.get('available_key_concepts', '')}\n"
        f"Max concept badges: {rules.get('max_concept_badges', '')}\n"
        f"Good hook example: {rules.get('example_good_hook', '')}\n"
        f"Bad hook example: {rules.get('example_bad_hook', '')}"
    )


def _load_step_instructions(state: SessionStateModel) -> str:
    """Load the step-specific instruction file and fill in template variables."""
    step = state.current_step
    template_type = state.template_type
    slots = state.creative_slots

    # Map step to instruction file
    file_map: dict[str, str] = {
        "STEP_1_HOOK": f"{template_type}_step1_hook.md",
        "STEP_2_RULES": "cat1_step2_rules.md",
        "STEP_2_MISSION": "cat5_step2_mission.md",
        "STEP_4_CELEBRATE": "cat1_step4_celebrate.md",
        "STEP_4_SYNTHESIS": "cat5_step4_synthesis.md",
        "STEP_5_CELEBRATE": "cat5_step5_celebrate.md",
        "STEP_5_CLOSING": "cat1_step5_closing.md",
        "STEP_6_CLOSING": "cat5_step6_closing.md",
        "EARLY_EXIT": "early_exit.md",
    }

    filename = None
    if step in file_map:
        filename = file_map[step]
    elif step.startswith("STEP_3_ROUND_"):
        filename = "cat1_step3_round.md"
    elif step.startswith("STEP_3_COLLECT_"):
        filename = "cat5_step3_collect.md"

    if not filename:
        return f"Current step: {step}. Generate an appropriate response."

    path = _STEP_INSTRUCTIONS_DIR / filename
    if not path.exists():
        return f"Current step: {step}. Generate an appropriate response."

    text = path.read_text()

    # Fill template variables from creative slots
    replacements: dict[str, str] = {
        "{round_number}": str(state.current_round),
        "{total_rounds}": str(state.total_rounds),
        "{ib_key_concepts}": ", ".join(state.ib_key_concepts),
    }

    if isinstance(slots, Cat1CreativeSlots):
        replacements.update(
            {
                "{game_mechanic}": slots.game_mechanic,
                "{metaphor}": slots.metaphor,
                "{role_title}": slots.role_title,
                "{escalation_axis}": slots.escalation_axis,
                "{observation_detail}": slots.observation_detail,
            }
        )
        # Fill round scenario if available
        round_idx = max(0, state.current_round - 1)
        if round_idx < len(slots.round_scenarios):
            replacements["{round_scenario}"] = slots.round_scenarios[round_idx]
        else:
            replacements["{round_scenario}"] = "Continue the game with an appropriate challenge."

    elif isinstance(slots, Cat5CreativeSlots):
        replacements.update(
            {
                "{observation_angle}": slots.observation_angle,
                "{collection_criterion}": slots.collection_criterion,
                "{collection_count}": str(slots.collection_count),
                "{mission_metaphor}": slots.mission_metaphor,
                "{role_title}": slots.role_title,
                "{synthesis_type}": slots.synthesis_type,
                "{stuck_hint}": slots.stuck_hint,
                "{naming_prompt}": slots.naming_prompt,
                "{observation_detail}": f"the {slots.observation_angle} of this {state.entity_name}",
            }
        )

    for key, value in replacements.items():
        text = text.replace(key, value)

    return text


def _build_conversation_context(state: SessionStateModel) -> str:
    """Format recent conversation history for the prompt (last 6 entries)."""
    history = state.conversation_history[-6:]
    if not history:
        return "(No conversation yet — this is the first turn.)"

    lines = []
    for turn in history:
        prefix = "Kido" if turn.role == "ai" else "Child"
        step_label = get_step_name(turn.step)
        lines.append(f"[{step_label}] {prefix}: {turn.text}")
    return "\n".join(lines)


def _build_creative_slots_text(slots: Cat1CreativeSlots | Cat5CreativeSlots) -> str:
    """Format creative slots as readable text for the prompt."""
    data = slots.model_dump()
    lines = []
    for key, value in data.items():
        label = key.replace("_", " ").title()
        display = ", ".join(str(v) for v in value) if isinstance(value, list) else value
        lines.append(f"- {label}: {display}")
    return "\n".join(lines)


def _build_system_prompt(state: SessionStateModel) -> str:
    """Assemble the full system prompt from template + injections."""
    template = _SKILL_PATH.read_text() if _SKILL_PATH.exists() else ""

    replacements = {
        "{tier_constraints}": _load_tier_constraints(state.tier),
        "{step_instructions}": _load_step_instructions(state),
        "{creative_slots}": _build_creative_slots_text(state.creative_slots),
        "{entity_name}": state.entity_name,
        "{entity_category}": state.entity_category,
        "{entity_attributes}": ", ".join(state.entity_attributes) if state.entity_attributes else "not specified",
        "{scene}": state.scene or "not specified",
        "{template_type}": f"Category {'1' if state.template_type == 'cat1' else '5'} ({state.template_type})",
        "{current_step}": f"{state.current_step} — {get_step_name(state.current_step)}",
        "{current_round}": str(state.current_round),
        "{total_rounds}": str(state.total_rounds),
        "{turn_count}": str(state.turn_count),
        "{status}": state.status,
        "{conversation_history}": _build_conversation_context(state),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


class ScriptAgent:
    """Generates per-turn dialogue using Gemini Flash."""

    async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
        """Generate the next dialogue turn (non-streaming fallback).

        Args:
            state: Full session state including creative slots and conversation history.

        Returns:
            TurnResponse with dialogue, tone, and screen instructions.

        Raises:
            ScriptAgentError: If generation fails.
        """
        settings = get_settings()
        start = time.perf_counter()

        system_prompt = _build_system_prompt(state)
        user_prompt = self._build_user_prompt(state)

        try:
            client = _get_client()

            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=user_prompt,
                config=GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=settings.script_turn_max_tokens,
                    response_mime_type="application/json",
                    response_schema=TurnResponse,
                    thinking_config=ThinkingConfig(thinking_budget=0),
                ),
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            if not response.text:
                raise ScriptAgentError("Empty response from Gemini")

            turn = TurnResponse.model_validate_json(response.text)

            logger.info(f"Script turn: step={state.current_step}, round={state.current_round}, latency={latency_ms}ms")
            await log_agent_call(state.session_id, "script_turn", latency_ms, True)
            return turn

        except ScriptAgentError:
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Script Agent turn failed ({latency_ms}ms): {e}")
            await log_agent_call(state.session_id, "script_turn", latency_ms, False, error_message=str(e))
            raise ScriptAgentError(f"Turn generation failed: {e}") from e

    async def generate_turn_streaming(self, state: SessionStateModel, on_dialogue: object | None = None) -> TurnResponse:
        """Generate the next dialogue turn using streaming.

        Streams tokens from Gemini Flash, extracting the dialogue value early
        so TTS can start before the full JSON is complete.

        Args:
            state: Full session state.
            on_dialogue: Optional async callable(str) invoked with the dialogue
                text as soon as it's extracted from the partial JSON stream.

        Returns:
            TurnResponse with dialogue, tone, and screen instructions.

        Raises:
            ScriptAgentError: If generation fails.
        """
        settings = get_settings()
        start = time.perf_counter()

        system_prompt = _build_system_prompt(state)
        user_prompt = self._build_user_prompt(state)

        try:
            client = _get_client()

            response_stream = await client.aio.models.generate_content_stream(
                model=settings.gemini_model,
                contents=user_prompt,
                config=GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=settings.script_turn_max_tokens,
                    response_mime_type="application/json",
                    response_schema=TurnResponse,
                    thinking_config=ThinkingConfig(thinking_budget=0),
                ),
            )

            accumulated = ""
            dialogue_sent = False

            async for chunk in response_stream:
                if chunk.text:
                    accumulated += chunk.text

                # Try to extract dialogue from partial JSON as early as possible
                if not dialogue_sent and on_dialogue and accumulated:
                    match = _DIALOGUE_RE.search(accumulated)
                    if match:
                        try:
                            dialogue_text = json.loads(f'"{match.group(1)}"')
                            await on_dialogue(dialogue_text)
                            dialogue_sent = True
                        except json.JSONDecodeError:
                            pass

            if not accumulated:
                raise ScriptAgentError("Empty response from Gemini streaming")

            turn = TurnResponse.model_validate_json(accumulated)

            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                f"Script turn (stream): step={state.current_step}, round={state.current_round}, latency={latency_ms}ms"
            )
            await log_agent_call(state.session_id, "script_turn", latency_ms, True)

            # If dialogue wasn't sent during streaming, send it now
            if not dialogue_sent and on_dialogue:
                await on_dialogue(turn.dialogue)

            return turn

        except ScriptAgentError:
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Script Agent streaming failed ({latency_ms}ms): {e}")
            await log_agent_call(state.session_id, "script_turn", latency_ms, False, error_message=str(e))
            raise ScriptAgentError(f"Turn generation failed: {e}") from e

    def _build_user_prompt(self, state: SessionStateModel) -> str:
        """Build the user message that triggers the LLM to generate this turn."""
        step_name = get_step_name(state.current_step)

        # Include the child's last message if there is one
        child_input = ""
        if state.conversation_history:
            last = state.conversation_history[-1]
            if last.role == "child":
                child_input = f'\n\nThe child just said: "{last.text}"'

        return (
            f"Generate the next turn for step: {step_name}.\n"
            f"This is turn {state.turn_count + 1} of the session.\n"
            f"Round {state.current_round} of {state.total_rounds}."
            f"{child_input}\n\n"
            f"Respond with a single JSON object matching the TurnResponse schema."
        )
