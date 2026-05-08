"""Script Agent — per-turn dialogue generation using Qwen via DashScope."""

import asyncio
import json
import random
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable

import httpx
import yaml
from openai import AsyncOpenAI

try:
    from ..character_sounds import get_sound_list_for_prompt
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.step_instruction import RoundInstruction, StepGoal
    from ..schemas.turn_directive import TurnDirective
    from ..schemas.turn_plan import TurnPlan
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import get_step_name
except ImportError:
    from character_sounds import get_sound_list_for_prompt
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.step_instruction import RoundInstruction, StepGoal
    from schemas.turn_directive import TurnDirective
    from schemas.turn_plan import TurnPlan
    from schemas.turn_response import TurnResponse
    from state_machine import get_step_name

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "script_turn.md"
_SPEAKER_PROMPT_PATH = Path(__file__).parent.parent / "skills" / "speaker_system.md"
_SPEAKER_DIRECTIVE_PROMPT_PATH = Path(__file__).parent.parent / "skills" / "speaker_directive_system.md"
_STEP_INSTRUCTIONS_DIR = Path(__file__).parent.parent / "skills" / "step_instructions"
_TIER_RULES_PATH = Path(__file__).parent.parent / "tier_rules.yaml"
_FRAGMENTABLE_STEP_PREFIXES = {"STEP_2_RULES", "STEP_3_ROUND", "STEP_3_COLLECT", "STEP_4_SYNTHESIS"}
_EXAMPLES_DIR = Path(__file__).parent.parent / "skills" / "examples"

# Synthesis stories need more sentences than normal turns; shared by both speaker paths.
_STORY_SENTENCES: dict[str, int] = {"T0": 8, "T1": 11, "T2": 14}

# --- Dynamic example library ---


@lru_cache(maxsize=8)
def _load_example_library(step_group: str) -> list[dict]:
    """Load examples from YAML file for the given step group. Cached."""
    path = _EXAMPLES_DIR / f"{step_group}.yaml"
    if not path.exists():
        logger.warning("example library not found: %s", path)
        return []
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("examples", [])


def _sample_examples(
    step_group: str,
    tier: str,
    n: int = 3,
    phase: str | None = None,
    style: str | None = None,
) -> str:
    """Randomly sample N examples matching the filters, formatted as markdown."""
    examples = _load_example_library(step_group)
    filtered = [e for e in examples if e.get("tier") == tier]
    if phase:
        filtered = [e for e in filtered if e.get("phase") == phase]
    if style and style != "default":
        styled = [e for e in filtered if e.get("style") == style]
        if styled:
            filtered = styled

    if len(filtered) < n:
        fallback = [e for e in examples if e.get("tier") == tier and e not in filtered]
        filtered.extend(fallback[: n - len(filtered)])

    selected = random.sample(filtered, min(n, len(filtered)))
    return "\n\n".join(e.get("text", "").strip() for e in selected)


def _map_step_to_example_group(step: str, template_type: str) -> str | None:
    """Map a step name to its example YAML group identifier."""
    if step == "STEP_1_HOOK" and template_type == "cat5":
        return "cat5_hook_mission"
    if step == "STEP_2_MISSION":
        return "cat5_hook_mission"
    if step.startswith("STEP_3_COLLECT_"):
        return "cat5_collect"
    if step.startswith("STEP_3_ROUND_"):
        return "cat1_round"
    if step == "STEP_4_SYNTHESIS":
        return "cat5_synthesis"
    if step in ("STEP_5_CELEBRATE", "STEP_6_CLOSING"):
        return "cat5_celebrate_closing"
    return None


_PERSONALITIES_PATH = Path(__file__).parent.parent / "skills" / "personalities.yaml"


@lru_cache(maxsize=1)
def _load_personalities_map() -> dict[str, dict]:
    """Load personalities indexed by ID for fast lookup."""
    if not _PERSONALITIES_PATH.exists():
        return {}
    with open(_PERSONALITIES_PATH) as f:
        data = yaml.safe_load(f) or {}
    return {p["id"]: p for p in data.get("personalities", [])}


def _format_personality(personality_id: str) -> str:
    """Format a personality as a prompt section."""
    if not personality_id:
        return ""
    personalities = _load_personalities_map()
    p = personalities.get(personality_id)
    if not p:
        return ""
    return (
        f"### Narrator Personality: {personality_id.replace('_', ' ').title()}\n"
        f"Voice: {p['voice']}\n"
        f"Celebration style: {p['celebration_style']}\n"
        f"This is your CHARACTER for this session. Stay in this voice throughout."
    )


# Variety hints injected into the user prompt for early steps where the prompt
# context is identical across sessions.  A random hint nudges the LLM toward a
# different opening/style each time.
_VARIETY_HINTS = [
    "Start with a sound word (Whoosh! Pop! Wow!).",
    "Open with something YOU noticed about the photo first.",
    "Use a metaphor or simile in your opening.",
    "Start with a playful question about how the child is feeling.",
    "Begin by whispering — use a soft, mysterious tone.",
    "Open with an exclamation about the most striking visual detail.",
    "Pretend you just discovered something surprising.",
    "Start by describing what you imagine touching it would feel like.",
    "Open with a silly comparison to something unexpected.",
    "Begin with wonder — 'I wonder...' or 'What if...'",
]
_SYNTHESIS_HINTS = [
    "One friend can't sleep, the others comfort them.",
    "They get caught in the rain and find shelter.",
    "One friend is sad, the others cheer them up.",
    "Someone is scared of the dark, friends bring light.",
    "They find one treat and figure out how to share it.",
    "One friend gets lost, the others search and find them.",
    "It's cold, they figure out how to stay warm together.",
    "It's someone's birthday and the others plan a surprise.",
    "They try to build something but it keeps falling down.",
    "One friend is too small to reach something, others help.",
]
_COLLECT_PHASE_A_HINTS = [
    "Celebrate with a sound word first (Ooh! Wow! Whoa!).",
    "Compare this find to a previous one.",
    "Notice something specific about the texture or color.",
    "React as if you are genuinely surprised by what they found.",
    "Use a simile to describe what you see.",
    "Express curiosity about a specific detail.",
    "Pretend you are touching it alongside them.",
    "Comment on something unexpected about the item.",
    "Make a playful connection to the original entity.",
    "Describe what it might feel like with vivid sensory words.",
    "Celebrate the EFFORT of finding it, not just the find itself.",
    "Ask about one specific sensory quality (soft? bumpy? smooth?).",
    "React with genuine delight, not formulaic praise.",
    "Notice how this one is different from the last.",
    "Use a metaphor from nature or everyday life.",
]
_COLLECT_PHASE_B_HINTS = [
    "Build on the child's exact words in your celebration.",
    "The name should connect to what the child said.",
    "Include the previous characters by name naturally.",
    "Make the naming moment feel like a mini-celebration.",
    "React to the child's observation with genuine interest.",
    "Let the child's description inspire the name.",
    "Connect this character to the growing group.",
    "Celebrate the uniqueness of this character compared to others.",
    "Express wonder about the child's choice of words.",
    "Make the character feel alive in one sentence.",
]
_CELEBRATE_HINTS = [
    "Reference a SPECIFIC moment the child experienced.",
    "Quote something the child actually said.",
    "Recall the funniest or most surprising moment.",
    "Connect the celebration to the child's personality, not just their finds.",
    "Make them feel remembered, not just praised.",
    "Reference a moment where the child was brave or creative.",
    "Celebrate HOW they explored, not just WHAT they found.",
    "Mention a character they named and why it was special.",
    "Recall when they were stuck and how they figured it out.",
    "Connect two different moments from the session.",
]
_CLOSING_HINTS = [
    "Weave the concept into a personal observation.",
    "End with a forward-looking question about tomorrow.",
    "Reference their specific characters one last time.",
    "Make the goodbye feel like a pause, not an ending.",
    "Connect the concept to something they discovered today.",
    "End with warmth and a hint of mystery about next time.",
    "Frame the concept as something THEY figured out, not something taught.",
    "Express genuine gratitude for the adventure together.",
    "Make them feel like they taught YOU something.",
    "End with a tiny story seed for next time.",
]
_STEP_HINT_MAP: dict[str, list[str]] = {
    "STEP_1_HOOK": _VARIETY_HINTS,
    "STEP_2_RULES": _VARIETY_HINTS,
    "STEP_2_MISSION": _VARIETY_HINTS,
    "STEP_4_CELEBRATE": _CELEBRATE_HINTS,
    "STEP_5_CELEBRATE": _CELEBRATE_HINTS,
    "STEP_5_CLOSING": _CLOSING_HINTS,
    "STEP_6_CLOSING": _CLOSING_HINTS,
}

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
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        max_retries=0,
        timeout=httpx.Timeout(60.0, connect=15.0),
    )


def _load_tier_constraints(tier: str) -> str:
    """Format tier rules into a compact string for the prompt.

    Produces a concise summary: tier label, sentence limits, tone, and the
    single most important scaffolding rule per tier.  Detailed tone and
    style guidance now lives in the per-step example transcripts.
    """
    if not _TIER_RULES_PATH.exists():
        return f"Tier: {tier}"

    with open(_TIER_RULES_PATH) as f:
        all_rules = yaml.safe_load(f) or {}

    rules = all_rules.get("tiers", {}).get(tier, {})
    if not rules:
        return f"Tier: {tier}"

    words_per_sentence = rules.get("words_per_sentence", "")
    if isinstance(words_per_sentence, list):
        if len(words_per_sentence) == 2:
            words_per_sentence = f"{words_per_sentence[0]}-{words_per_sentence[1]}"
        else:
            words_per_sentence = ", ".join(str(value) for value in words_per_sentence)

    response_style = rules.get("response_style", "")
    if isinstance(response_style, list):
        response_style = ", ".join(str(value) for value in response_style)

    tier_key_rules = {
        "T0": "Always model your idea first, then offer a choice. Never ask open questions alone.",
        "T1": "Light scaffolding. Can ask guided questions.",
        "T2": "Can invite child to try first. Scaffold only if stuck.",
    }

    lines = [
        f"Tier: {tier} ({rules.get('label', '')}, ages {rules.get('ages', '')})",
        f"Sentences: max {rules.get('max_sentences', '')}, ~{words_per_sentence} words each.",
        f"Style: {rules.get('tone', '')}. {response_style}",
        f"Key rule: {tier_key_rules.get(tier, '')}",
    ]

    return "\n".join(lines)


def _load_tier_rules_raw(tier: str) -> dict:
    """Load raw tier rules dict from tier_rules.yaml for a given tier.

    Args:
        tier: Tier key, e.g. "T0", "T1", "T2".

    Returns:
        Dict of tier rule values (label, ages, max_sentences, words_per_sentence, etc.).
        Returns empty dict if the tier or file is not found.
    """
    if not _TIER_RULES_PATH.exists():
        return {}

    with open(_TIER_RULES_PATH) as f:
        all_rules = yaml.safe_load(f) or {}

    return all_rules.get("tiers", {}).get(tier, {})


def _format_words_per_sentence(words_per_sentence: object) -> str:
    """Format tier word-count guidance for prompts."""
    if isinstance(words_per_sentence, list):
        if len(words_per_sentence) == 2:
            return f"{words_per_sentence[0]}-{words_per_sentence[1]}"
        return ", ".join(str(value) for value in words_per_sentence)
    return str(words_per_sentence)


def _build_speaker_prompt(state: SessionStateModel, plan: TurnPlan) -> str:
    """Build the speaker system prompt from tier rules and the current plan."""
    tier_rules = _load_tier_rules_raw(state.tier)
    template = _SPEAKER_PROMPT_PATH.read_text() if _SPEAKER_PROMPT_PATH.exists() else ""

    max_sentences = tier_rules.get("max_sentences", 2)
    if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "generate":
        max_sentences = _STORY_SENTENCES.get(state.tier, 11)

    replacements = {
        "{tier}": state.tier,
        "{tier_label}": str(tier_rules.get("label", "")),
        "{tier_ages}": str(tier_rules.get("ages", "")),
        "{max_sentences}": str(max_sentences),
        "{words_per_sentence}": _format_words_per_sentence(tier_rules.get("words_per_sentence", [5, 10])),
        "{turn_plan_json}": plan.model_dump_json(indent=2),
        "{emotion_tag}": plan.emotion_tag,
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


def _build_speaker_user_prompt(corrective_hint: str | None = None) -> str:
    """Build the user message for the speaker pass."""
    prompt = (
        "Generate the dialogue for this plan. "
        'Output valid JSON: {"dialogue": "[emotion_tag] Your text here", "tone_marker": "..."}'
    )
    if corrective_hint:
        prompt += f"\n\n{corrective_hint}"
    return prompt


def _build_directive_speaker_prompt(state: SessionStateModel, directive: TurnDirective) -> str:
    """Build the speaker system prompt from a TurnDirective (directive path)."""
    tier_rules = _load_tier_rules_raw(state.tier)
    template = _SPEAKER_DIRECTIVE_PROMPT_PATH.read_text() if _SPEAKER_DIRECTIVE_PROMPT_PATH.exists() else ""

    max_sentences = directive.max_sentences
    words_per_sentence = _format_words_per_sentence(tier_rules.get("words_per_sentence", [5, 10]))
    is_story = "tell a complete" in directive.response_direction.lower() or (
        state.current_step == "STEP_4_SYNTHESIS" and directive.action == "advance"
    )
    # Stories need more sentences and longer sentences than normal turns
    if is_story:
        max_sentences = _STORY_SENTENCES.get(state.tier, 11)
        words_per_sentence = {"T0": "8-12", "T1": "10-15", "T2": "12-18"}.get(state.tier, "10-15")

    # Build constraints list from directive flags — only include rules
    # when the flag is active so the LLM doesn't see inapplicable examples
    constraints: list[str] = []
    if directive.do_not_suggest_items:
        constraints.append("- NEVER name specific objects to find or locations to look.")
    if directive.must_model_first:
        constraints.append(
            "- Model a SOUND or ACTION first (e.g., 'Woof!', 'Splash!'), then ask. "
            "NEVER model an emotion word (never say 'I think it feels happy/surprised')."
        )
    if directive.offer_binary_choice:
        constraints.append(
            "- Ask a simple A-or-B question about SENSORY QUALITIES only "
            "(e.g., 'Is it squishy or smooth?'). Never name specific items."
        )
    if not directive.offer_binary_choice:
        constraints.append(
            "- Do NOT ask binary choice questions (like 'X or Y?') unless the direction explicitly asks for one."
        )

    replacements = {
        "{tier}": state.tier,
        "{tier_label}": str(tier_rules.get("label", "")),
        "{tier_ages}": str(tier_rules.get("ages", "")),
        "{max_sentences}": str(max_sentences),
        "{words_per_sentence}": words_per_sentence,
        "{response_direction}": directive.response_direction,
        "{emotion_tag}": directive.emotion_tag,
        "{constraints}": "\n".join(constraints) if constraints else "(none)",
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


_PHASE_SECTION_RE = re.compile(
    r"### PHASE:\s*(\w+)\s*\([^)]*\)\s*\n(.*?)(?=### |\Z)",
    re.DOTALL,
)


def _filter_synthesis_phase(text: str, active_phase: str) -> str:
    """Strip inactive phase sections from synthesis instructions.

    The synthesis markdown contains ### PHASE: INVITE, ### PHASE: IMPROVE, and
    ### PHASE: GENERATE sections. Only the section matching *active_phase* is
    kept so the LLM doesn't see competing instructions.
    """
    active_key = active_phase.upper()

    def _replace(m: re.Match[str]) -> str:
        phase_name = m.group(1).upper()
        if phase_name == active_key:
            return m.group(0)  # keep the active phase
        return ""  # strip inactive phases

    return _PHASE_SECTION_RE.sub(_replace, text)


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

    # Synthesis instructions contain all phases — strip inactive ones so the
    # LLM only sees the section for the current phase and doesn't fall back
    # to invite-style questions when it should be generating a story.
    if step == "STEP_4_SYNTHESIS":
        text = _filter_synthesis_phase(text, state.synthesis_phase)

    fragment_prefix = step
    if step.startswith(("STEP_3_ROUND_", "STEP_3_COLLECT_")):
        fragment_prefix = step.rsplit("_", maxsplit=1)[0]

    # Synthesis step: load phase-specific fragment instead of synthesis_type fragment
    if step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "generate":
        fragment_path = _STEP_INSTRUCTIONS_DIR / "cat5_step4_synthesis__story_generation.md"
        if fragment_path.exists():
            text += "\n\n" + fragment_path.read_text()
    elif fragment_prefix in _FRAGMENTABLE_STEP_PREFIXES:
        style_key: str | None = None
        if isinstance(slots, Cat1CreativeSlots):
            style_key = slots.game_mechanic
        elif isinstance(slots, Cat5CreativeSlots) and step != "STEP_4_SYNTHESIS":
            style_key = slots.synthesis_type
        if style_key:
            base_name = filename.removesuffix(".md")
            fragment_path = _STEP_INSTRUCTIONS_DIR / f"{base_name}__{style_key}.md"
            if fragment_path.exists():
                text += "\n\n" + fragment_path.read_text()

    # Fill template variables from creative slots
    replacements: dict[str, str] = {
        "{activity_name}": state.activity_type.replace("_", " ").title(),
        "{entity_name}": state.entity_name,
        "{tier}": state.tier,
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
        collected_names_str = ", ".join(state.collected_names) if state.collected_names else "(none yet)"
        collected_details_str = "; ".join(state.collected_details) if state.collected_details else "(none yet)"
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
                "{collection_phase}": state.collection_phase,
                "{detail_question_template}": slots.detail_question_template,
                "{sorting_criterion}": slots.sorting_criterion,
                "{collected_names}": collected_names_str,
                "{collected_details}": collected_details_str,
                "{synthesis_phase}": state.synthesis_phase,
                "{child_story_attempt}": state.synthesis_child_story or "(none)",
                "{story_theme}": random.choice(_SYNTHESIS_HINTS) if step == "STEP_4_SYNTHESIS" else "",
            }
        )

        # Story sentence count by tier
        tier_sentence_counts = {"T0": "7-8", "T1": "9-11", "T2": "12-14"}
        replacements["{story_sentence_count}"] = tier_sentence_counts.get(state.tier, "9-11")

    for key, value in replacements.items():
        text = text.replace(key, value)

    # Resolve {sampled_examples} with dynamically sampled examples,
    # then re-run replacements so {entity_name} etc. in examples get filled.
    if "{sampled_examples}" in text:
        example_group = _map_step_to_example_group(step, template_type)
        if example_group:
            style_key = None
            if isinstance(slots, Cat1CreativeSlots):
                style_key = slots.game_mechanic
            elif isinstance(slots, Cat5CreativeSlots):
                style_key = slots.synthesis_type
            sampled = _sample_examples(step_group=example_group, tier=state.tier, n=3, style=style_key)
            text = text.replace("{sampled_examples}", sampled)
        else:
            text = text.replace("{sampled_examples}", "")
        # Re-run template replacements on injected examples
        for key, value in replacements.items():
            text = text.replace(key, value)

    # Deep link override for shortened hook
    if state.deep_linked and step == "STEP_1_HOOK":
        text += (
            f"\n\n### DEEP LINK OVERRIDE (takes priority over normal hook rules):\n"
            f"This child was just talking with another AI about {state.entity_name}. "
            f"They already know the entity.\n"
            f"Your hook must be SHORTENED:\n"
            f"1. One brief sentence acknowledging what they were just discussing "
            f"(reference a specific detail from the upstream conversation).\n"
            f"2. Immediately transition to the game invitation — frame it as "
            f'"Would you like to...?" using invitational language.\n'
            f"3. Do NOT do the full observation + wonder sequence. The child is already engaged.\n"
            f"4. Maximum 2 sentences total regardless of tier."
        )

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
            lines.append(
                f"Theme examples (for inspiration — any on-topic answer is valid): {', '.join(goal_source.acceptable_themes)}"
            )
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


_AUDIO_DIRECTIVE_RE = re.compile(r"\s*\[AUDIO\][^\]]*(?:\]|$)", re.IGNORECASE)
_ASTERISK_STAGE_DIRECTION_RE = re.compile(r"\*([^*]{1,40})\*")


def _merge_asterisk_directions(dialogue: str) -> str:
    """Move *whispers*, *gasps* etc. into the emotion tag bracket.

    '[curious] *whispers* Shh...' -> '[curious, whispers] Shh...'
    If no emotion tag exists, the directions are stripped (the caller adds a tag after).
    """
    directions = _ASTERISK_STAGE_DIRECTION_RE.findall(dialogue)
    if not directions:
        return dialogue

    # Remove all *...* from the text
    cleaned = _ASTERISK_STAGE_DIRECTION_RE.sub("", dialogue).strip()

    # Merge into existing emotion tag bracket
    tag_match = _EMOTION_TAG_RE.match(cleaned)
    if tag_match:
        old_tag = tag_match.group(0).rstrip()  # e.g. "[curious]"
        inner = old_tag[1:-1]  # "curious"
        merged = ", ".join([inner] + [d.strip() for d in directions])
        cleaned = f"[{merged}] " + cleaned[tag_match.end() :]

    return cleaned


def _clean_dialogue(turn: TurnResponse, state: SessionStateModel) -> None:
    """Post-process dialogue: strip leaked directives and ensure emotion tag."""
    # Strip [AUDIO] sfx/music directives that the LLM copied from step instructions
    turn.dialogue = _AUDIO_DIRECTIVE_RE.sub("", turn.dialogue).rstrip()

    # Move asterisk stage directions into the emotion tag bracket
    turn.dialogue = _merge_asterisk_directions(turn.dialogue)

    # Ensure dialogue starts with a bracketed emotion tag
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
        prefix = "Zigzag" if turn.role == "ai" else "Child"
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

    # Build upstream conversation context for deep-linked sessions
    upstream_context = ""
    if state.deep_linked and state.upstream_conversation:
        upstream_lines = ["### Upstream Conversation Context:", "The child just had this conversation with another AI:"]
        for turn in state.upstream_conversation:
            prefix = "Child" if turn.role == "child" else "Upstream AI"
            upstream_lines.append(f"  {prefix}: {turn.text}")
        upstream_context = "\n".join(upstream_lines)

    replacements = {
        "{personality}": _format_personality(state.narrator_personality),
        "{tier_constraints}": _load_tier_constraints(state.tier),
        "{step_instructions}": _load_step_instructions(state),
        "{creative_slots}": _build_creative_slots_text(state.creative_slots),
        "{entity_name}": state.entity_name,
        "{entity_category}": state.entity_category,
        "{entity_attributes}": ", ".join(state.entity_attributes) if state.entity_attributes else "not specified",
        "{scene}": state.scene or "not specified",
        "{photo_feature_anchors}": photo_feature_anchors,
        "{character_sound_list}": get_sound_list_for_prompt(state.activity_type),
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

    if upstream_context:
        template += f"\n\n{upstream_context}"

    return template


class ScriptAgent:
    """Generates per-turn dialogue using Qwen via DashScope."""

    def __init__(self) -> None:
        self.last_plan: TurnPlan | None = None
        self.last_best_of_n: dict | None = None

    async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
        """Generate the next dialogue turn using two-pass (planner + speaker) with single-pass fallback.

        The two-pass pipeline calls the Planner first to produce a structured TurnPlan,
        then the Speaker to convert that plan into child-facing dialogue. If the two-pass
        path fails for any reason, falls back to the original single-pass generation.

        Args:
            state: Full session state including creative slots and conversation history.

        Returns:
            TurnResponse with dialogue, tone, and screen instructions.

        Raises:
            ScriptAgentError: If both two-pass and single-pass generation fail.
        """
        settings = get_settings()
        self.last_best_of_n = None
        if not settings.two_pass_enabled:
            self.last_plan = None
            # Best-of-N for high-impact steps
            if settings.best_of_n > 1 and (
                state.current_step.startswith("STEP_3_COLLECT_") or state.current_step == "STEP_4_SYNTHESIS"
            ):
                return await self._generate_best_of_n(state, n=settings.best_of_n)
            return await self._generate_turn_single_pass(state)

        try:
            plan = await self._plan_turn(state)
            self.last_plan = plan
            turn = await self._speak_turn(state, plan)

            # Merge plan's screen/audio decisions into the speaker response
            turn.screen_widget = plan.screen_widget
            turn.screen_widget_params = plan.screen_widget_params
            turn.screen_animation = plan.screen_animation
            turn.sfx_cue = plan.sfx_cue
            turn.stay_on_step = plan.stay_on_step
            if plan.character_sfx:
                turn.character_sfx = list(plan.character_sfx)

            return turn

        except Exception as e:
            logger.warning(f"Two-pass generation failed, falling back to single-pass: {e}")
            self.last_plan = None
            return await self._generate_turn_single_pass(state)

    async def _plan_turn(self, state: SessionStateModel) -> TurnPlan:
        """Run the Planner agent to produce a structured TurnPlan.

        Args:
            state: Full session state.

        Returns:
            TurnPlan with content decisions, constraints, and tone guidance.

        Raises:
            PlannerError: If the planner call fails.
        """
        # Lazy import to avoid circular dependency (planner imports from script_agent)
        try:
            from ..agents.planner import Planner  # noqa: PLC0415
        except ImportError:
            from agents.planner import Planner  # noqa: PLC0415

        planner = Planner()
        return await planner.plan_turn(state)

    async def retry_speaker_turn(
        self,
        state: SessionStateModel,
        plan: TurnPlan,
        corrective_hint: str | None = None,
    ) -> TurnResponse:
        """Retry only the speaker pass using an existing planner output."""
        self.last_plan = plan
        return await self._speak_turn(state, plan, corrective_hint=corrective_hint)

    async def generate_turn_from_directive(
        self,
        state: SessionStateModel,
        directive: TurnDirective,
    ) -> TurnResponse:
        """Generate dialogue using a TurnDirective from the Turn Director.

        This is the speaker pass in the directive pipeline (2-call architecture).
        The Turn Director has already decided WHAT to do; the speaker converts
        the response_direction into child-facing dialogue.

        Args:
            state: Full session state.
            directive: TurnDirective with action, reasoning, and response direction.

        Returns:
            TurnResponse with dialogue, tone, and screen instructions.

        Raises:
            ScriptAgentError: If the speaker LLM call fails.
        """
        settings = get_settings()
        start = time.perf_counter()

        system_prompt = _build_directive_speaker_prompt(state, directive)

        # Include conversation context and step instructions for the speaker
        conversation = _build_conversation_context(state)

        # The directive's response_direction is the authoritative instruction.
        # For advance actions, skip step instructions entirely — the direction
        # IS the complete instruction and step instructions add competing context.
        # For stay/need_help actions, include step instructions as background
        # reference (tier rules, scaffolding behavior) but make the directive
        # take explicit priority to prevent the LLM from following step examples
        # instead of the directive (e.g., treating a detail response as a
        # completed naming instead of asking for the name as directed).
        rd_lower = directive.response_direction.lower()
        is_self_contained = (
            directive.action == "advance"
            or "tell a complete" in rd_lower
            or "generate a complete" in rd_lower
            or "name the ib concept" in rd_lower
        )

        if is_self_contained:
            # For story generation, load the dedicated story generation guide
            # which has 5-beat framework, examples, and quality rules.
            story_instructions = ""
            if "tell a complete" in rd_lower:
                story_gen_path = _STEP_INSTRUCTIONS_DIR / "cat5_step4_synthesis__story_generation.md"
                if story_gen_path.exists():
                    raw = story_gen_path.read_text()
                    names_str = ", ".join(state.collected_names) if state.collected_names else ""
                    details_str = "; ".join(state.collected_details) if state.collected_details else ""
                    replacements = {
                        "{collected_names}": names_str,
                        "{collected_details}": details_str,
                        "{tier}": state.tier,
                        "{story_theme}": directive.response_direction,
                        "{child_story_attempt}": state.synthesis_child_story or "(none)",
                        "{sampled_examples}": "",
                    }
                    for k, v in replacements.items():
                        raw = raw.replace(k, v)
                    story_instructions = f"\n\n## Story Generation Guide\n{raw}"

            user_prompt = (
                f"## Conversation History\n{conversation}\n\n"
                f"IMPORTANT: Follow the Direction in the system prompt EXACTLY and COMPLETELY. "
                f"Include ALL parts of the Direction — do not stop early or skip any part. "
                f"{story_instructions}\n\n"
                f'Output valid JSON: {{"dialogue": "[{directive.emotion_tag}] Your text here", "tone_marker": "..."}}'
            )
        else:
            step_instructions = _load_step_instructions(state)
            user_prompt = (
                f"## Conversation History\n{conversation}\n\n"
                f"## Step Instructions (background reference for tone and tier rules)\n"
                f"{step_instructions}\n\n"
                f"## OVERRIDE — Follow This Direction Exactly\n"
                f"The Direction in the system prompt takes ABSOLUTE PRIORITY over the "
                f"step instructions above. Do exactly what the Direction says — do NOT "
                f"skip ahead, do NOT follow examples from step instructions that show a "
                f"different flow. Generate ONLY the response described in the Direction.\n\n"
                f'Output valid JSON: {{"dialogue": "[{directive.emotion_tag}] Your text here", "tone_marker": "..."}}'
            )

        try:
            client = _get_client()

            response = await client.chat.completions.create(
                model=settings.dashscope_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.speaker_temperature,
                max_tokens=settings.script_turn_max_tokens,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            text = response.choices[0].message.content or ""

            logger.info(
                "Directive Speaker response: step=%s, action=%s\n--- SPEAKER RAW ---\n%s\n--- END ---",
                state.current_step,
                directive.action,
                text,
            )

            data = json.loads(text)
            dialogue = data.get("dialogue", "")
            tone = data.get("tone_marker", directive.emotion_tag)

            turn = TurnResponse(
                dialogue=dialogue,
                tone_marker=tone,
                screen_widget=directive.screen_widget,
                screen_widget_params=directive.screen_widget_params,
                screen_animation=directive.screen_animation,
                sfx_cue=directive.sfx_cue,
                stay_on_step=directive.stay_on_step,
            )
            if directive.character_sfx:
                turn.character_sfx = list(directive.character_sfx)
            _clean_dialogue(turn, state)

            logger.info(
                "Directive Speaker: step=%s action=%s latency=%dms",
                state.current_step,
                directive.action,
                latency_ms,
            )
            await log_agent_call(state.session_id, "directive_speaker", latency_ms, True)
            return turn

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error("Directive Speaker failed (%dms): %s", latency_ms, e)
            await log_agent_call(state.session_id, "directive_speaker", latency_ms, False, error_message=str(e))
            raise ScriptAgentError(f"Directive speaker generation failed: {e}") from e

    async def _speak_turn(
        self,
        state: SessionStateModel,
        plan: TurnPlan,
        corrective_hint: str | None = None,
    ) -> TurnResponse:
        """Run the Speaker pass to convert a TurnPlan into child-facing dialogue.

        Loads the speaker prompt template, fills in tier data and the plan JSON,
        calls the LLM at a higher temperature for natural language, and returns
        a TurnResponse with dialogue and tone_marker fields populated.

        Args:
            state: Full session state (used for tier info).
            plan: The structured TurnPlan from the planner pass.

        Returns:
            TurnResponse with dialogue and tone_marker from the speaker LLM.

        Raises:
            ScriptAgentError: If the speaker LLM call fails.
        """
        settings = get_settings()
        start = time.perf_counter()

        speaker_prompt = _build_speaker_prompt(state, plan)
        user_prompt = _build_speaker_user_prompt(corrective_hint)

        try:
            client = _get_client()

            response = await client.chat.completions.create(
                model=settings.dashscope_model,
                messages=[
                    {"role": "system", "content": speaker_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.speaker_temperature,
                max_tokens=settings.script_turn_max_tokens,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            text = response.choices[0].message.content or ""
            if not text:
                raise ScriptAgentError("Empty response from Speaker LLM")

            logger.info(
                f"Speaker LLM response: step={state.current_step}, round={state.current_round}, "
                f"activity={state.activity_type}\n--- SPEAKER RAW ---\n{text}\n--- END ---"
            )

            # Parse the minimal JSON — speaker returns only dialogue + tone_marker
            speaker_data = json.loads(text)
            turn = TurnResponse(
                dialogue=speaker_data.get("dialogue", ""),
                tone_marker=speaker_data.get("tone_marker", "gentle"),
                screen_widget="photo_display",
                screen_widget_params={},
            )
            _clean_dialogue(turn, state)

            logger.info(f"Speaker turn: step={state.current_step}, round={state.current_round}, latency={latency_ms}ms")
            await log_agent_call(state.session_id, "speaker", latency_ms, True)
            return turn

        except ScriptAgentError:
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Speaker pass failed ({latency_ms}ms): {e}")
            await log_agent_call(state.session_id, "speaker", latency_ms, False, error_message=str(e))
            raise ScriptAgentError(f"Speaker generation failed: {e}") from e

    def _score_candidate(self, turn: TurnResponse, state: SessionStateModel) -> float:
        """Score a candidate response using lightweight heuristics.

        Returns a score in [0.0, 1.0]. Higher is better.
        """
        dialogue = turn.dialogue

        # 1. Phrase novelty: Jaccard distance from recent AI turns (50%)
        recent_ai = [t.text for t in state.conversation_history[-3:] if t.role == "ai"]
        if recent_ai:
            current_words = set(dialogue.lower().split())
            similarities = []
            for prev in recent_ai:
                prev_words = set(prev.lower().split())
                union = len(current_words | prev_words)
                similarities.append(len(current_words & prev_words) / max(union, 1))
            novelty = 1.0 - (sum(similarities) / len(similarities))
        else:
            novelty = 1.0

        # 2. Tier compliance: emotion tag + sentence count (30%)
        has_tag = 1.0 if _EMOTION_TAG_RE.match(dialogue) else 0.0
        sentences = [s.strip() for s in re.split(r"[.!?]+\s*", dialogue) if s.strip()]
        tier_max = {"T0": 2, "T1": 3, "T2": 4}.get(state.tier, 3)
        sentence_ok = 1.0 if len(sentences) <= tier_max else 0.0
        tier_score = (has_tag + sentence_ok) / 2.0

        # 3. Structural checks: no item suggestions (20%)
        # For Cat5 collection steps, ANY mention of specific household/outdoor
        # items is a violation — regardless of verb framing (e.g. "I wonder if
        # a pillow is hiding" is just as bad as "find a pillow").
        item_noun_re = re.compile(
            r"(?i)\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
            r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
            r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble"
            r"|rug|carpet|towel|cloth|cushion|teddy|doll|stuffed|berry|berries|petal|petals"
            r"|grass|furniture|acorn|pinecone|mushroom|feather|twig|bark|seed|moss)\b"
        )
        structure_score = 0.0 if item_noun_re.search(dialogue) else 1.0

        return novelty * 0.5 + tier_score * 0.3 + structure_score * 0.2

    async def _generate_best_of_n(self, state: SessionStateModel, n: int = 2) -> TurnResponse:
        """Generate N candidates in parallel and return the highest-scoring one."""
        tasks = [self._generate_turn_single_pass(state) for _ in range(n)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates = [r for r in results if isinstance(r, TurnResponse)]
        errors = [str(r) for r in results if isinstance(r, Exception)]
        if not candidates:
            for r in results:
                if isinstance(r, Exception):
                    raise ScriptAgentError(f"All {n} candidates failed: {r}") from r
            raise ScriptAgentError("No candidates generated")

        if len(candidates) == 1:
            self.last_best_of_n = {
                "n": n,
                "returned": len(candidates),
                "errors": errors,
                "candidates": [{"text": candidates[0].dialogue, "score": None, "picked": True}],
            }
            return candidates[0]

        scored = [(self._score_candidate(c, state), c) for c in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)

        logger.info(
            "best_of_n: step=%s scores=%s picked=%.3f",
            state.current_step,
            [f"{s:.3f}" for s, _ in scored],
            scored[0][0],
        )

        self.last_best_of_n = {
            "n": n,
            "returned": len(candidates),
            "errors": errors,
            "candidates": [
                {
                    "text": c.dialogue,
                    "score": round(s, 3),
                    "picked": i == 0,
                }
                for i, (s, c) in enumerate(scored)
            ],
        }

        return scored[0][1]

    async def _generate_turn_single_pass(self, state: SessionStateModel) -> TurnResponse:
        """Generate the next dialogue turn using the original single-pass LLM call.

        This is the fallback path used when two-pass generation fails.

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
                model=settings.dashscope_model,
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
            _clean_dialogue(turn, state)

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
        """Generate the next dialogue turn using two-pass streaming.

        Calls the Planner (non-streaming — small JSON output), then streams
        the Speaker call to extract dialogue tokens for early TTS delivery.
        Falls back to single-pass streaming if two-pass fails.

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
        if not settings.two_pass_enabled:
            self.last_plan = None
            return await self._generate_turn_streaming_single_pass(state, on_dialogue)

        try:
            # Step 1: Planner (non-streaming — small JSON)
            plan = await self._plan_turn(state)
            self.last_plan = plan

            # Step 2: Speaker (streaming for early TTS)
            turn = await self._speak_turn_streaming(state, plan, on_dialogue)

            # Merge plan's screen/audio decisions into the speaker response
            turn.screen_widget = plan.screen_widget
            turn.screen_widget_params = plan.screen_widget_params
            turn.screen_animation = plan.screen_animation
            turn.sfx_cue = plan.sfx_cue
            turn.stay_on_step = plan.stay_on_step
            if plan.character_sfx:
                turn.character_sfx = list(plan.character_sfx)

            return turn

        except Exception as e:
            logger.warning(f"Two-pass streaming failed, falling back to single-pass streaming: {e}")
            self.last_plan = None
            return await self._generate_turn_streaming_single_pass(state, on_dialogue)

    async def _speak_turn_streaming(
        self,
        state: SessionStateModel,
        plan: TurnPlan,
        on_dialogue: Callable | None = None,
        corrective_hint: str | None = None,
    ) -> TurnResponse:
        """Run the Speaker pass with streaming to extract dialogue early for TTS.

        Args:
            state: Full session state (used for tier info).
            plan: The structured TurnPlan from the planner pass.
            on_dialogue: Optional async callable(str) invoked with the dialogue
                text as soon as it's extracted from the partial stream.

        Returns:
            TurnResponse with dialogue and tone_marker from the speaker LLM.

        Raises:
            ScriptAgentError: If the speaker LLM call fails.
        """
        settings = get_settings()
        start = time.perf_counter()

        speaker_prompt = _build_speaker_prompt(state, plan)
        user_prompt = _build_speaker_user_prompt(corrective_hint)

        try:
            client = _get_client()

            response_stream = await client.chat.completions.create(
                model=settings.dashscope_model,
                messages=[
                    {"role": "system", "content": speaker_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.speaker_temperature,
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

                # Extract dialogue from partial JSON for early TTS
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
                raise ScriptAgentError("Empty response from Speaker LLM streaming")

            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                f"Speaker LLM response (stream): step={state.current_step}, round={state.current_round}, "
                f"activity={state.activity_type}\n--- SPEAKER RAW ---\n{accumulated}\n--- END ---"
            )

            # Parse the minimal JSON — speaker returns only dialogue + tone_marker
            speaker_data = json.loads(accumulated)
            turn = TurnResponse(
                dialogue=speaker_data.get("dialogue", ""),
                tone_marker=speaker_data.get("tone_marker", "gentle"),
                screen_widget="photo_display",
                screen_widget_params={},
            )
            _clean_dialogue(turn, state)

            logger.info(
                f"Speaker turn (stream): step={state.current_step}, round={state.current_round}, latency={latency_ms}ms"
            )
            await log_agent_call(state.session_id, "speaker", latency_ms, True)

            # If dialogue wasn't sent during streaming, send it now
            if not dialogue_sent and on_dialogue:
                await on_dialogue(turn.dialogue)

            return turn

        except ScriptAgentError:
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Speaker streaming failed ({latency_ms}ms): {e}")
            await log_agent_call(state.session_id, "speaker", latency_ms, False, error_message=str(e))
            raise ScriptAgentError(f"Speaker streaming failed: {e}") from e

    async def _generate_turn_streaming_single_pass(
        self, state: SessionStateModel, on_dialogue: Callable | None = None
    ) -> TurnResponse:
        """Fallback: single-pass streaming generation (original path).

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
                model=settings.dashscope_model,
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
            _clean_dialogue(turn, state)

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

    @staticmethod
    def _round_label(state: SessionStateModel) -> str:
        """Short round label for the user prompt (empty if not a round step)."""
        if state.current_step.startswith(("STEP_3_ROUND_", "STEP_3_COLLECT_")):
            return f" Round {state.current_round}/{state.total_rounds}."
        return ""

    def _build_user_prompt(self, state: SessionStateModel) -> str:
        """Build the user message that triggers the LLM to generate this turn."""
        step_name = get_step_name(state.current_step)

        # Include the child's last message if there is one
        child_input = ""
        if state.conversation_history:
            last = state.conversation_history[-1]
            if last.role == "child":
                child_input = f'\n\nThe child just said: "{last.text}"'

        intent_context = ""
        if state.child_intent:
            intent_context = f"\nChild's intent has been classified as: {state.child_intent}."

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

        # Inject a random variety hint — step-specific pools ensure
        # every turn gets a contextually relevant creative nudge.
        variety_line = ""
        if state.current_step == "STEP_4_SYNTHESIS":
            hint = random.choice(_SYNTHESIS_HINTS)
            if state.synthesis_phase == "generate":
                variety_line = f"\nStory theme: {hint}\n"
            else:
                variety_line = f"\nStory direction: {hint} Write a DIFFERENT story than the examples.\n"
        elif state.current_step.startswith("STEP_3_COLLECT_"):
            pool = _COLLECT_PHASE_B_HINTS if state.collection_phase == "detail" else _COLLECT_PHASE_A_HINTS
            hint = random.choice(pool)
            variety_line = f"\nStyle hint: {hint}\n"
        elif state.current_step.startswith("STEP_3_ROUND_"):
            hint = random.choice(_COLLECT_PHASE_A_HINTS)
            variety_line = f"\nStyle hint: {hint}\n"
        elif state.current_step in _STEP_HINT_MAP:
            hint = random.choice(_STEP_HINT_MAP[state.current_step])
            variety_line = f"\nStyle hint: {hint}\n"

        return (
            f"Generate the next turn for step: {step_name}.\n"
            f"This is turn {state.turn_count + 1} of the session."
            f"{self._round_label(state)}"
            f"{child_input}"
            f"{intent_context}"
            f"{variety_line}\n"
            f"Respond with EXACTLY this JSON structure (all fields required):\n"
            f"{{\n"
            f'  "dialogue": "[emotion_tag] Your dialogue text here",\n'
            f'  "tone_marker": "excited|curious|mysterious|encouraging|impressed|gentle|celebrating|adventurous",\n'
            f'  "screen_widget": "photo_display|character_display|progress_tracker|badge_award|photo_grid",\n'
            f'  "screen_widget_params": {{}},\n'
            f'  "screen_animation": "sparkle_highlight|celebration_burst|appear|gentle_pulse|null",\n'
            f'  "sfx_cue": "wonder_chime|celebration_fanfare|badge_awarded|game_start_chime|null",\n'
            f"{stay_on_step_field}"
            f"}}"
        )
