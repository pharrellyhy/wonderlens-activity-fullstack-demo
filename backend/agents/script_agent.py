"""Script Agent — per-turn dialogue generation using Qwen via ALI DashScope."""

import json
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable

import httpx
import yaml
from openai import AsyncOpenAI

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.recipe import InstructionRecipe
    from ..schemas.session_state import SessionStateModel
    from ..schemas.step_instruction import RoundInstruction, StepGoal
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import get_step_name
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.recipe import InstructionRecipe
    from schemas.session_state import SessionStateModel
    from schemas.step_instruction import RoundInstruction, StepGoal
    from schemas.turn_response import TurnResponse
    from state_machine import get_step_name

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "script_turn.md"
_STEP_INSTRUCTIONS_DIR = Path(__file__).parent.parent / "skills" / "step_instructions"
_TIER_RULES_PATH = Path(__file__).parent.parent / "tier_rules.yaml"
_FRAGMENTABLE_STEP_PREFIXES = {"STEP_2_RULES", "STEP_3_ROUND", "STEP_3_COLLECT", "STEP_4_SYNTHESIS"}

# Regex to extract dialogue value from partial JSON stream
_DIALOGUE_RE = re.compile(r'"dialogue"\s*:\s*"((?:[^"\\]|\\.)*)"')
# Regex to detect a leading bracket emotion tag like "[excited] "
_EMOTION_TAG_RE = re.compile(r"^\[.+?\] ")


class ScriptAgentError(Exception):
    """Raised when the Script Agent fails to generate a valid turn."""


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.ali_api_key,
        base_url=settings.ali_base_url,
        max_retries=0,
        timeout=httpx.Timeout(60.0, connect=15.0),
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

    lines = [
        f"Tier: {tier} ({rules.get('label', '')})",
        f"Ages: {rules.get('ages', '')}",
        f"Words per sentence: {rules.get('words_per_sentence', '')}",
        f"Max sentences per turn: {rules.get('max_sentences', '')}",
        f"Hook rule: {rules.get('hook_rule', '')} — {rules.get('hook_description', '')}",
        f"Closing: {rules.get('closing_speech', '')} — {rules.get('closing_description', '')}",
        f"Tone: {rules.get('tone', '')}",
        f"Response style: {rules.get('response_style', '')}",
        f"Round count range: {rules.get('pathway_rounds', '')}",
        f"Available concepts: {rules.get('available_key_concepts', '')}",
        f"Max concept badges: {rules.get('max_concept_badges', '')}",
        f"Good hook example: {rules.get('example_good_hook', '')}",
        f"Bad hook example: {rules.get('example_bad_hook', '')}",
    ]

    invitational = rules.get("invitational_patterns", [])
    if invitational:
        lines.append(f"Invitational patterns: {', '.join(invitational)}")

    forbidden = rules.get("forbidden_directives", [])
    if forbidden:
        lines.append(f"FORBIDDEN directives: {', '.join(forbidden)}")

    return "\n".join(lines)


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

    fragment_prefix = step
    if step.startswith(("STEP_3_ROUND_", "STEP_3_COLLECT_")):
        fragment_prefix = step.rsplit("_", maxsplit=1)[0]

    if fragment_prefix in _FRAGMENTABLE_STEP_PREFIXES:
        style_key: str | None = None
        if isinstance(slots, Cat1CreativeSlots):
            style_key = slots.game_mechanic
        elif isinstance(slots, Cat5CreativeSlots):
            style_key = slots.synthesis_type
        if style_key:
            base_name = filename.removesuffix(".md")
            fragment_path = _STEP_INSTRUCTIONS_DIR / f"{base_name}__{style_key}.md"
            if fragment_path.exists():
                text += "\n\n" + fragment_path.read_text()

    # Fill template variables from creative slots
    replacements: dict[str, str] = {
        "{entity_name}": state.entity_name,
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
        collected_count = len(state.collected_photos)
        remaining_count = max(0, state.total_rounds - collected_count)
        replacements.update(
            {
                "{observation_angle}": slots.observation_angle,
                "{collection_criterion}": slots.collection_criterion,
                "{collection_count}": str(slots.collection_count),
                "{collected_count}": str(collected_count),
                "{remaining_count}": str(remaining_count),
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

    # Append activity-specific overlay from instruction recipe
    overlay = _build_instruction_overlay(state)
    if overlay:
        text += f"\n\n{overlay}"

    return text


def _build_instruction_overlay(state: SessionStateModel) -> str:
    """Build activity-specific instruction overlay from the instruction recipe."""
    recipe = state.instruction_recipe
    if not recipe:
        return ""

    step = state.current_step
    instructions = recipe.step_instructions

    goal_source: StepGoal | RoundInstruction | None = None

    if step == "STEP_1_HOOK":
        goal_source = instructions.hook
    elif step in ("STEP_2_RULES", "STEP_2_MISSION"):
        goal_source = instructions.transition
    elif step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        round_num = int(step.rsplit("_", maxsplit=1)[-1])
        round_idx = round_num - 1
        if 0 <= round_idx < len(instructions.rounds):
            goal_source = instructions.rounds[round_idx]
    elif step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        goal_source = instructions.celebrate
    elif step == "STEP_4_SYNTHESIS":
        goal_source = instructions.synthesis
    elif step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        goal_source = instructions.closing
    elif step == "EARLY_EXIT":
        goal_source = instructions.early_exit

    if not goal_source:
        return ""

    lines = [
        "### Activity-Specific Instructions:",
        f"Goal: {goal_source.goal}",
        f"Constraint: {goal_source.constraint}",
        f"Suggested emotion tag: [{goal_source.emotion_tag}]",
    ]

    if isinstance(goal_source, RoundInstruction):
        lines.append(f"Scenario: {goal_source.scenario}")
        if goal_source.acceptable_themes:
            lines.append(f"Acceptable themes: {', '.join(goal_source.acceptable_themes)}")
        if goal_source.escalation_note:
            lines.append(f"Escalation: {goal_source.escalation_note}")

    # For Cat5 collection rounds, add explicit progress context to prevent hallucination
    if isinstance(state.creative_slots, Cat5CreativeSlots) and (
        step.startswith("STEP_3_COLLECT_") or step.startswith("STEP_3_ROUND_")
    ):
        collected = len(state.collected_photos)
        remaining = max(0, state.total_rounds - collected)
        lines.append("\n**PROGRESS — ACTUAL COUNT (NON-NEGOTIABLE):**")
        lines.append(f"- Items collected so far: **{collected}**")
        lines.append(f"- Items still needed: **{remaining}**")
        lines.append(f"- Total required: **{state.total_rounds}**")
        lines.append(
            f"- The original {state.entity_name} does NOT count — it was the inspiration, "
            f"not a collected item. All {state.total_rounds} items must be different things."
        )
        if remaining > 0:
            lines.append(
                "\n The mission is NOT complete — DO NOT say 'all done', 'found them all', "
                "'mission complete', 'collection is complete', or anything similar. "
                "You MUST end with an invitational question about finding the NEXT item."
            )
        else:
            lines.append(
                "\n The mission IS complete — all items found! Celebrate this final find. Do NOT ask any questions."
            )

    return "\n".join(lines)


def _get_suggested_emotion_tag(state: SessionStateModel) -> str:
    """Get the suggested emotion tag for the current step from the instruction recipe."""
    recipe = state.instruction_recipe
    if not recipe:
        return "gentle"

    step = state.current_step
    instructions = recipe.step_instructions

    if step == "STEP_1_HOOK":
        return instructions.hook.emotion_tag
    if step in ("STEP_2_RULES", "STEP_2_MISSION"):
        return instructions.transition.emotion_tag
    if step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        round_num = int(step.rsplit("_", maxsplit=1)[-1])
        round_idx = round_num - 1
        if 0 <= round_idx < len(instructions.rounds):
            return instructions.rounds[round_idx].emotion_tag
    if step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        return instructions.celebrate.emotion_tag
    if step == "STEP_4_SYNTHESIS" and instructions.synthesis:
        return instructions.synthesis.emotion_tag
    if step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        return instructions.closing.emotion_tag
    if step == "EARLY_EXIT":
        return instructions.early_exit.emotion_tag

    return "gentle"


def _ensure_emotion_tag(turn: TurnResponse, state: SessionStateModel) -> None:
    """Ensure dialogue starts with a bracketed emotion tag; prepend one if missing."""
    if not _EMOTION_TAG_RE.match(turn.dialogue):
        tag = _get_suggested_emotion_tag(state)
        turn.dialogue = f"[{tag}] {turn.dialogue}"


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

    # Build photo feature anchors section
    photo_feature_anchors = ""
    recipe = state.instruction_recipe
    if recipe and recipe.photo_features:
        features = ", ".join(recipe.photo_features)
        photo_feature_anchors = (
            f"### Photo Feature Anchors:\n"
            f"Only reference these visible features: {features}\n"
            f"Do NOT invent features not in this list."
        )

    replacements = {
        "{tier_constraints}": _load_tier_constraints(state.tier),
        "{step_instructions}": _load_step_instructions(state),
        "{creative_slots}": _build_creative_slots_text(state.creative_slots),
        "{entity_name}": state.entity_name,
        "{entity_category}": state.entity_category,
        "{entity_attributes}": ", ".join(state.entity_attributes) if state.entity_attributes else "not specified",
        "{scene}": state.scene or "not specified",
        "{photo_feature_anchors}": photo_feature_anchors,
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
    """Generates per-turn dialogue using Qwen via ALI DashScope."""

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

            response = await client.chat.completions.create(
                model=settings.ali_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=settings.script_turn_max_tokens,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            text = response.choices[0].message.content or ""
            if not text:
                raise ScriptAgentError("Empty response from LLM")

            logger.info(
                f"Script LLM response: step={state.current_step}, round={state.current_round}, "
                f"activity={state.activity_type}\n--- LLM RAW ---\n{text}\n--- END ---"
            )

            turn = TurnResponse.model_validate_json(text)
            _ensure_emotion_tag(turn, state)

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

    async def generate_turn_streaming(
        self, state: SessionStateModel, on_dialogue: Callable | None = None
    ) -> TurnResponse:
        """Generate the next dialogue turn using streaming.

        Streams tokens from the LLM, extracting the dialogue value early
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

            response_stream = await client.chat.completions.create(
                model=settings.ali_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=settings.script_turn_max_tokens,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
                stream=True,
            )

            accumulated = ""
            dialogue_sent = False

            async for chunk in response_stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    accumulated += delta.content

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
                raise ScriptAgentError("Empty response from LLM streaming")

            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                f"Script LLM response (stream): step={state.current_step}, round={state.current_round}, "
                f"activity={state.activity_type}\n--- LLM RAW ---\n{accumulated}\n--- END ---"
            )

            turn = TurnResponse.model_validate_json(accumulated)
            _ensure_emotion_tag(turn, state)

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

        # Include child_intent field for STEP_2 invitation handling
        child_intent_field = ""
        if state.current_step in ("STEP_2_RULES", "STEP_2_MISSION"):
            child_intent_field = '  "child_intent": "accepted|declined|off_topic|null",\n'

        # Include stay_on_step for round and synthesis steps where child might need help
        stay_on_step_field = ""
        if (
            state.current_step.startswith("STEP_3_ROUND_")
            or state.current_step.startswith("STEP_3_COLLECT_")
            or state.current_step == "STEP_4_SYNTHESIS"
        ):
            stay_on_step_field = (
                '  "stay_on_step": true/false,  // Set true if child said "I don\'t know", '
                "is confused, or needs a hint before moving on\n"
            )

        return (
            f"Generate the next turn for step: {step_name}.\n"
            f"This is turn {state.turn_count + 1} of the session.\n"
            f"Round {state.current_round} of {state.total_rounds}."
            f"{child_input}\n\n"
            f"Respond with EXACTLY this JSON structure (all fields required):\n"
            f"{{\n"
            f'  "dialogue": "[emotion_tag] Your dialogue text here",\n'
            f'  "tone_marker": "excited|curious|mysterious|encouraging|impressed|gentle|celebrating|adventurous",\n'
            f'  "screen_widget": "photo_display|character_display|progress_tracker|badge_award|photo_grid",\n'
            f'  "screen_widget_params": {{}},\n'
            f'  "screen_animation": "sparkle_highlight|celebration_burst|appear|gentle_pulse|scene_transition|badge_reveal|null",\n'
            f'  "sfx_cue": "wonder_chime|celebration_fanfare|badge_awarded|game_start_chime|null",\n'
            f"{child_intent_field}"
            f"{stay_on_step_field}"
            f"}}"
        )
