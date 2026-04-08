"""Turn Director Agent — unified intent classification + turn planning.

Replaces the separate classifier (``_classify_child_intent``) and planner
(``Planner.plan_turn``) when ``turn_director_enabled`` is on.  A single LLM
call decides WHAT HAPPENS NEXT (action) and HOW TO RESPOND (response_direction),
reducing the pipeline from 3 LLM calls to 2 (turn director -> speaker).
"""

import json
import time
from pathlib import Path

import httpx
from openai import AsyncOpenAI

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_directive import StoryElement, TurnDirective
    from .script_agent import (
        _build_conversation_context,
        _build_creative_slots_text,
        _load_tier_constraints,
    )
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_directive import StoryElement, TurnDirective

    from agents.script_agent import (
        _build_conversation_context,
        _build_creative_slots_text,
        _load_tier_constraints,
    )

logger = setup_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "skills" / "turn_director_system.md"

# ---------------------------------------------------------------------------
# Step Phase Rules — compact decision tables embedded in the director prompt
# ---------------------------------------------------------------------------

_CAT5_COLLECTION_RULES = """\
### Cat5 Collection Phases
- Phase=photo, no photo selected yet:
  action=stay, direction="Invite child to find something {observation_angle}. Use invitational language."
- Phase=photo, correct photo (child input contains "[collected correct item"):
  action=stay (stay_on_step=true), direction="Celebrate the find! Ask a detail/harvest question based on the story scaffold strategy for round {round_number}."
  sfx_cue="slot_fill_chime" (or "mission_complete_fanfare" if this is the LAST item)
- Phase=photo, wrong photo (child input contains "[selected wrong photo"):
  action=stay, direction="Acknowledge warmly in ONE short sentence (e.g., 'Ooh, interesting find!'). Then redirect with ONE invitational sentence toward something {observation_angle}. That's it — just two sentences, no questions about the wrong item, no comparisons, no modeling."
- Phase=detail, child gave substantive response (name, description, detail):
  action=advance, harvest a story_element with the child's words and any character name.
  direction="Celebrate the detail. Name the character if synthesis_format is collaborative_story. Reference ALL previous characters."
- Phase=detail, child is off-topic:
  action=stay (stay_on_step=true), direction="Acknowledge, re-ask the detail question with different wording."
- Phase=detail, silence:
  action=need_help, direction="Model an answer. For T0: offer a binary choice about the ALREADY FOUND item (e.g., 'Does it feel squishy or smooth?')."

CRITICAL RULES:
- NEVER suggest specific items to find (no "leaf", "flower", "blanket", "pillow"). You CANNOT see the child's environment.
- NEVER suggest specific locations (no "on the floor", "near you", "over there").
- Binary choices must be about SENSORY QUALITIES of the item already found (e.g., "squishy or smooth?", "fuzzy or silky?"), NOT about specific objects in the environment.
- When redirecting from a wrong photo, say "something {observation_angle}" — do NOT name what to look for.\
"""

_INVITATION_RULES = """\
### Invitation (STEP_2_MISSION / STEP_2_RULES)
- Child confirms (yes, sure, ok, let's go, etc.):
  action=advance, direction="Celebrate acceptance briefly, then invite the child to go find their first {observation_angle} item. Do NOT talk about the original photo/entity — the child is moving on to explore. Focus on encouraging them to find something new that matches the collection criterion."
- Child declines (no, nah, I don't want to) — first decline:
  action=stay, direction="Re-invite warmly with a different framing."
- Child declines — second or more:
  action=exit, direction="Gentle goodbye, no pressure."
- Child says something substantive or off-topic:
  action=stay, direction="Acknowledge what they said, then re-invite."\
"""

_SYNTHESIS_RULES = """\
### Synthesis (STEP_4_SYNTHESIS)
- First visit (synthesis_phase=invite):
  action=stay, direction="Invite child to make up a story about the collected characters using the story scaffold premise. For T0: model the START of a story and ask the child what happens next."
- Child confirms/agrees (synthesis_phase=invite — yes, good, cool, sure, ok, etc.):
  action=stay, direction="The child wants a story! Encourage THEM to try making one up first. Ask: what happens to {characters}? Keep it simple and inviting — they can say anything."
  DO NOT generate the story yet. Give the child a chance to try first.
- Child gave a story contribution (synthesis_phase=child_try — even one word like 'fly' or 'hug'):
  action=advance, direction="Weave a COMPLETE short story (4-8 sentences for T0, 6-11 for T1, 8-14 for T2) using the child's contribution and ALL harvested story elements. Each character should appear by name with their trait. The story must have a beginning, middle, and end."
- Child declines to try (synthesis_phase=child_try — no, you do it, etc.):
  action=stay, direction="Offer two story theme choices for the child to pick from."
- Child chose a theme (synthesis_phase=theme_choice):
  action=advance, direction="Generate a COMPLETE short story using the chosen theme and ALL harvested story elements."
- Child is silent:
  action=advance, direction="Generate a COMPLETE short story using ALL harvested story elements. Each character appears by name with their trait. The story must have a beginning, middle, and end. Then celebrate."\
"""

_CAT1_ROUND_RULES_VOICE_ACTING = """\
### Cat1 Round (Voice Acting)
- First turn on this round (no child answer yet):
  action=stay, direction="Present THIS ROUND'S SCENARIO (from the context above) vividly. Set the scene with sounds and actions, then ask ONE question about how the {entity_name} feels or reacts."
- Child gave a good/creative answer AND this is NOT the last round:
  action=advance, max_sentences=3, direction="Celebrate the child's answer warmly in one sentence. Then use a brief, natural transition before presenting the NEXT round's scenario vividly. End with ONE question about the emotion. Use the EXACT next scenario from the round list — do NOT invent one."
- Child gave a good/creative answer AND this IS the last round (current round = total rounds):
  action=advance, max_sentences=2, direction="Celebrate this answer warmly. Do NOT wrap up, recap, award a title, or say the game is done — the celebration step handles all of that."
- Child gave an unexpected-but-on-topic answer (related to the scenario but not a listed theme — e.g., "hungry" when asked about feelings):
  action=advance, direction="Celebrate their creative take! Echo back their specific word and build on it with wonder before transitioning."
- Child gave an off-topic answer (clearly unrelated to the scenario — e.g., talking about a TV show during a mood scene):
  action=stay, direction="Warmly acknowledge what they said, then gently redirect to the scenario with a SOUND or ACTION and offer a binary choice between two emotions."
- Child is silent:
  action=need_help, direction="Model a SOUND or ACTION for the scenario, then offer a binary choice between two emotions."

CRITICAL Cat1 RULES:
- NEVER say 'I think the {entity_name} feels [emotion]' or tell the child what the answer is. The child must GUESS the feeling — that is the whole game.
- When modeling, only model SOUNDS or ACTIONS (woof!, yawn, splash, tremble, tail wagging) — NEVER model emotion words (happy, sad, surprised, excited).
- Binary choices must be between TWO EMOTIONS (e.g., 'happy or sleepy?', 'brave or scared?'), never actions.\
"""

_CAT1_ROUND_RULES_STORYTELLING = """\
### Cat1 Round (Storytelling Chain)
- First turn on this round (no child answer yet):
  action=stay, direction="Present THIS ROUND'S SCENARIO (from the context above) vividly. Paint the scene with sensory details, then ask ONE question about what the {entity_name} sees, finds, or does in the scene — NOT about how it feels."
- Child gave a good/creative answer AND this is NOT the last round:
  action=advance, max_sentences=3, direction="Celebrate the child's answer warmly in one sentence. Then use a brief, natural transition before presenting the NEXT round's scenario vividly. End with ONE question about what happens in the scene (what the {entity_name} sees, finds, or discovers). Use the EXACT next scenario from the round list — do NOT invent one."
- Child gave a good/creative answer AND this IS the last round (current round = total rounds):
  action=advance, max_sentences=2, direction="Celebrate this answer warmly. Do NOT wrap up, recap dreams, award a title, or say the game/story is done — the celebration step handles all of that."
- Child gave an unexpected-but-on-topic answer (related to the scene but not a listed theme):
  action=advance, direction="Celebrate their creative idea! Echo back their specific word and weave it into the story before transitioning."
- Child gave an off-topic answer (clearly unrelated to the current scene):
  action=stay, direction="Warmly acknowledge, then gently redirect with a binary choice between two concrete things the {entity_name} might see or do in the scene."
- Child is silent:
  action=need_help, direction="Model what the {entity_name} might find in the scene, then offer a binary choice between two concrete discoveries or actions."

CRITICAL Cat1 Storytelling RULES:
- Ask about what the {entity_name} SEES, FINDS, or DOES — never about how it FEELS.
- Binary choices must be between TWO CONCRETE THINGS (objects, actions, discoveries), never emotions.
- Do NOT ask about emotions or feelings (e.g., 'happy or scared?'). Ask about the scene content (e.g., 'a rainbow or some butterflies?').\
"""

_HOOK_RULES = """\
### Hook (STEP_1_HOOK)
- Child responded to the imaginative question:
  action=advance, max_sentences=3, direction="Build on their response with wonder. Introduce the mission invitation naturally from what they said — explain what the explorer does in one sentence. End with ONE invitation question. Do NOT ask about texture or the photo — just invite."
- Child is silent:
  action=need_help, direction="Offer a simpler version of the question, or model a response."\
"""

_CELEBRATE_RULES = """\
### Celebrate (STEP_5_CELEBRATE)
- Any child input or auto-advance:
  action=advance, max_sentences=4, direction="Award the role title ceremonially. Recap ALL characters by name with their traits. Celebrate the entire journey."
- Child is silent (first time):
  action=stay, max_sentences=3, direction="Gently celebrate and award the title. Do NOT exit — give the child a moment."\
"""

_CLOSING_RULES = """\
### Closing (STEP_6_CLOSING)
- Any child input or auto-advance:
  action=advance, direction="Name the IB concept naturally connected to what they discovered. Plant a curiosity seed. Warm goodbye."\
"""


def _select_step_phase_rules(state: SessionStateModel) -> str:
    """Select the appropriate step phase rules for the current step."""
    step = state.current_step

    if step == "STEP_1_HOOK":
        return _HOOK_RULES
    if step in ("STEP_2_MISSION", "STEP_2_RULES"):
        return _INVITATION_RULES
    if step.startswith("STEP_3_COLLECT_"):
        return _CAT5_COLLECTION_RULES
    if step == "STEP_4_SYNTHESIS":
        return _SYNTHESIS_RULES
    if step == "STEP_5_CELEBRATE":
        return _CELEBRATE_RULES
    if step == "STEP_6_CLOSING":
        return _CLOSING_RULES

    # Cat1 rounds (STEP_3_ROUND_*) — mechanic-specific rules
    if step.startswith("STEP_3_ROUND_"):
        if (
            isinstance(state.creative_slots, Cat1CreativeSlots)
            and state.creative_slots.game_mechanic == "storytelling_chain"
        ):
            return _CAT1_ROUND_RULES_STORYTELLING
        return _CAT1_ROUND_RULES_VOICE_ACTING

    return ""


def _build_state_context(state: SessionStateModel) -> str:
    """Build a compact state summary for the director prompt."""
    lines = [
        f"Step: {state.current_step} | Tier: {state.tier} | Template: {state.template_type}",
        f"Round: {state.current_round} of {state.total_rounds} | Turn count: {state.turn_count}",
        f"Entity: {state.entity_name} ({state.entity_category})",
        f"Consecutive silence: {state.consecutive_silence}",
    ]

    # Tier constraints
    lines.append("")
    lines.append(_load_tier_constraints(state.tier))

    # Cat5 collection state
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        collected_count = len(state.collected_photos)
        remaining_count = max(0, state.total_rounds - collected_count)
        names_str = ", ".join(state.collected_names) if state.collected_names else "(none yet)"

        lines.append("")
        lines.append(f"Collection phase: {state.collection_phase}")
        lines.append(f"Collected: {collected_count} of {state.total_rounds} | Remaining: {remaining_count}")
        lines.append(f"Named characters: {names_str}")
        lines.append(f"Detail exchanges this phase: {state.detail_exchange_count}")
        lines.append(f"Observation angle: {state.creative_slots.observation_angle}")
        lines.append(f"Collection criterion: {state.creative_slots.collection_criterion}")

        # Story elements harvested so far
        if state.story_elements:
            lines.append("")
            lines.append("Story elements harvested:")
            for elem in state.story_elements:
                name_part = f" ({elem.character_name})" if elem.character_name else ""
                trait_part = f" — {elem.trait_or_detail}" if elem.trait_or_detail else ""
                words_part = f' [child said: "{elem.child_words}"]' if elem.child_words else ""
                lines.append(f"  Round {elem.round_number}{name_part}{trait_part}{words_part}")

        # Story scaffold
        scaffold = state.creative_slots.story_scaffold
        if scaffold:
            lines.append("")
            lines.append("## Story Scaffold")
            lines.append(f"Premise: {scaffold.premise}")
            lines.append(f"Harvest per round: {scaffold.harvest_per_round}")
            lines.append(f"Strategy: {scaffold.harvest_question_strategy}")
            lines.append(f"Synthesis goal: {scaffold.synthesis_goal}")
            lines.append(f"Synthesis format: {scaffold.synthesis_format}")
            if scaffold.story_themes:
                lines.append(f"Themes: {'; '.join(scaffold.story_themes)}")

    # Cat1 round scenarios — prefer the instruction recipe's rich descriptions
    if isinstance(state.creative_slots, Cat1CreativeSlots):
        slots = state.creative_slots
        lines.append("")
        lines.append(f"Game mechanic: {slots.game_mechanic}")
        lines.append(f"Metaphor: {slots.metaphor}")
        lines.append(f"Role title: {slots.role_title}")
        lines.append(f"Escalation: {slots.escalation_axis}")

        # Use instruction recipe rounds (rich scene descriptions) when available
        recipe_rounds = state.instruction_recipe.step_instructions.rounds if state.instruction_recipe else []

        lines.append("")
        lines.append("Round scenarios (use EXACTLY these — do NOT invent new ones):")
        if recipe_rounds:
            for r in recipe_rounds:
                marker = " ← CURRENT" if r.round_number == state.current_round else ""
                lines.append(f"  R{r.round_number}: {r.scenario}{marker}")
        else:
            for i, scenario in enumerate(slots.round_scenarios, 1):
                marker = " ← CURRENT" if i == state.current_round else ""
                lines.append(f"  R{i}: {scenario}{marker}")

        # Highlight the current round's full scenario text
        current_scenario = ""
        if recipe_rounds:
            for r in recipe_rounds:
                if r.round_number == state.current_round:
                    current_scenario = r.scenario
                    break
        elif 1 <= state.current_round <= len(slots.round_scenarios):
            current_scenario = slots.round_scenarios[state.current_round - 1]

        if current_scenario:
            lines.append("")
            lines.append(f'THIS ROUND\'S SCENARIO: "{current_scenario}"')
            lines.append(
                "You MUST present this exact scenario to the child. Do NOT substitute or invent a different one."
            )

    # Synthesis state
    if state.current_step == "STEP_4_SYNTHESIS":
        lines.append("")
        lines.append(f"Synthesis phase: {state.synthesis_phase}")
        lines.append(f"Synthesis prompt count: {state.synthesis_prompt_count}")
        if state.synthesis_child_story:
            lines.append(f'Child\'s story attempt: "{state.synthesis_child_story[:200]}"')

    # Creative slots summary
    lines.append("")
    lines.append("Creative Slots:")
    lines.append(_build_creative_slots_text(state.creative_slots))

    return "\n".join(lines)


def _build_system_prompt(state: SessionStateModel, child_text: str) -> str:
    """Build the complete Turn Director system prompt."""
    template = _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else ""

    replacements = {
        "{state_context}": _build_state_context(state),
        "{step_phase_rules}": _select_step_phase_rules(state),
        "{conversation_history}": _build_conversation_context(state),
        "{child_text}": child_text,
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


def _parse_directive(raw_json: str, state: SessionStateModel) -> TurnDirective:
    """Parse raw JSON into a TurnDirective, applying safe defaults for missing fields."""
    data = json.loads(raw_json)

    # Default to "stay" when the LLM returns a missing or invalid action
    data.setdefault("action", "stay")
    if data["action"] not in ("advance", "stay", "need_help", "redirect", "exit"):
        data["action"] = "stay"

    # Ensure required string fields
    data.setdefault("reasoning", "")
    data.setdefault("response_direction", "")
    data.setdefault("emotion_tag", "gentle")

    # Parse nested story_element: keep only if it's a dict, otherwise discard
    se_raw = data.get("story_element")
    data["story_element"] = StoryElement(**se_raw) if isinstance(se_raw, dict) else None

    # Apply tier-based defaults
    is_t0 = state.tier == "T0"
    data.setdefault("must_model_first", is_t0)
    data.setdefault("offer_binary_choice", is_t0)

    # Strip None values for fields with string defaults — the LLM sometimes
    # returns explicit null for optional-looking fields like screen_widget,
    # which overrides the Pydantic default and causes validation errors.
    for key in ("screen_widget", "emotion_tag", "reasoning", "response_direction"):
        if data.get(key) is None:
            data.pop(key, None)

    # Coerce stay_on_step to bool — LLM sometimes returns a string like "STEP_3_ROUND_1"
    sos = data.get("stay_on_step")
    if sos is not None and not isinstance(sos, bool):
        data["stay_on_step"] = str(sos).lower() in ("true", "1", "yes")

    # Coerce max_sentences to int
    ms = data.get("max_sentences")
    if ms is not None and not isinstance(ms, int):
        try:
            data["max_sentences"] = int(ms)
        except (ValueError, TypeError):
            data.pop("max_sentences", None)

    return TurnDirective.model_validate(data)


class TurnDirectorError(Exception):
    """Raised when the Turn Director fails to produce a valid directive."""


class TurnDirector:
    """Decides what happens next based on child input and session state.

    Replaces the separate classifier + planner pipeline with a single LLM
    call that outputs an action-based intent, reasoning, and response
    direction for the speaker.
    """

    async def direct_turn(self, state: SessionStateModel, child_text: str) -> TurnDirective:
        """Generate a TurnDirective from session state and child input.

        Args:
            state: Full session state.
            child_text: The child's input text (or empty for silence).

        Returns:
            TurnDirective with action, reasoning, and response direction.
            On LLM failure, returns a safe fallback directive (action="stay").
        """
        settings = get_settings()
        start = time.perf_counter()

        system_prompt = _build_system_prompt(state, child_text)

        user_prompt = (
            f'The child said: "{child_text or "(silence — no input)"}"\n\n'
            f"Current step: {state.current_step}, round {state.current_round} of {state.total_rounds}.\n\n"
            f"Output a valid JSON TurnDirective."
        )

        try:
            client = AsyncOpenAI(
                api_key=settings.ali_api_key,
                base_url=settings.ali_base_url,
                max_retries=1,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )

            response = await client.chat.completions.create(
                model=settings.ali_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.15,
                max_tokens=400,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            raw = response.choices[0].message.content or "{}"

            logger.info(
                "Turn Director response: step=%s, round=%d, activity=%s\n--- DIRECTOR RAW ---\n%s\n--- END ---",
                state.current_step,
                state.current_round,
                state.activity_type,
                raw,
            )

            directive = _parse_directive(raw, state)

            logger.info(
                "Turn Director: step=%s action=%s reasoning=%s latency=%dms",
                state.current_step,
                directive.action,
                directive.reasoning[:80],
                latency_ms,
            )
            await log_agent_call(state.session_id, "turn_director", latency_ms, True)
            return directive

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error("Turn Director failed (%dms): %s", latency_ms, e)
            await log_agent_call(state.session_id, "turn_director", latency_ms, False, error_message=str(e))

            # Safe fallback: stay on current step with generic direction
            return TurnDirective(
                action="stay",
                reasoning=f"Turn Director LLM failed: {e}. Defaulting to stay.",
                response_direction="Gently ask the child to continue with the current activity.",
                emotion_tag="gentle",
                stay_on_step=True,
            )
