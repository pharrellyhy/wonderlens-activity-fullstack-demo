"""Turn Director feature-flagged bypass path.

Contains the directive-based turn resolution flow: fast-path mapping of
common phrases to TurnDirective, LLM Turn Director calls, story direction
building, and the action-based routing that replaces the legacy if/elif path.

Extracted verbatim from turn_handler.py during package decomposition.
"""

import random
import re

try:
    from ..agents.script_agent import ScriptAgent
    from ..agents.turn_director import TurnDirector
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_directive import StoryElement, TurnDirective
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import (
        EARLY_EXIT,
        is_terminal,
    )
except ImportError:
    from agents.script_agent import ScriptAgent
    from agents.turn_director import TurnDirector
    from logger import setup_logger
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_directive import StoryElement, TurnDirective
    from schemas.turn_response import TurnResponse
    from state_machine import (
        EARLY_EXIT,
        is_terminal,
    )

from .collection import _record_collection_detail
from .debug import _build_debug_payload
from .generation import _generate_with_retry
from .helpers import (
    _CONFIRM_WORDS,
    _DECLINE_WORDS,
    _advance_state,
    _append_ai_turn,
    _get_response_type,
    _get_screen_frame,
    _is_celebrate_step,
    _is_closing_step_directive,
    _is_invitation_step,
    _should_auto_advance,
)
from .synthesis import _loading_result
from .types import GenerationDebugInfo, TurnInput, TurnResult

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Turn Director path (feature-flagged)
# ---------------------------------------------------------------------------

_turn_director = TurnDirector()

_NON_ANSWER_PHRASES = frozenset(
    {
        "i dont know",
        "i don't know",
        "idk",
        "dunno",
        "no idea",
        "help",
        "help me",
        "i need help",
        "you pick",
        "you choose",
        "you decide",
        "you do it",
        "you provide one",
        "you tell me",
        "you name it",
        "you suggest one",
        "you suggest",
        "you give it a name",
        "you say",
        "hmm",
        "uh",
        "um",
        "huh",
    }
)

_NAME_EXTRACT_PATTERNS = [
    re.compile(r"(?:let'?s? call (?:it|him|her|them|this one)?)\s+(.+)", re.IGNORECASE),
    re.compile(
        r"(?:I (?:want to |wanna )?(?:name|call) (?:it|him|her|them|this one)?)\s+(.+)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:how about|maybe)\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:name (?:it|him|her|them))\s+(.+)", re.IGNORECASE),
]

# Playful fallback (name, detail) pairs per observation angle. Used when the
# child is stuck at the detail phase (2+ consecutive non-answers). The first
# unused option is picked so two stuck items in a row get distinct defaults.
_STUCK_DEFAULTS: dict[str, list[tuple[str, str]]] = {
    "texture": [("Softie", "soft and cozy"), ("Fuzzy", "fluffy and warm")],
    "color": [("Sunny", "bright and cheerful"), ("Rainbow", "colorful and fun")],
    "shape": [("Curvy", "smooth and curvy"), ("Pointy", "tall and pointy")],
    "size": [("Tiny", "small and cute"), ("Mighty", "big and strong")],
    "pattern": [("Spotty", "covered in pretty spots"), ("Dotty", "full of tiny dots")],
    "form": [("Bumpy", "bumpy and interesting"), ("Wiggly", "wiggly and playful")],
    "movement": [("Dancy", "always moving"), ("Bouncy", "bouncing around")],
    "smell": [("Sweetie", "sweet and fresh"), ("Minty", "cool and fresh")],
    "function": [("Helpful", "useful and clever"), ("Special", "special and unique")],
    "habitat": [("Cozy", "snug and safe"), ("Hidden", "tucked away")],
}


def _pick_stuck_default(state: SessionStateModel) -> tuple[str, str]:
    """Pick a playful (name, detail) fallback for a stuck child at detail phase.

    Rotates through options by observation angle so consecutive stuck items
    don't all get the same default. Falls back to texture defaults if the
    game's angle has no entry.
    """
    angle = "texture"
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        angle = state.creative_slots.observation_angle
    options = _STUCK_DEFAULTS.get(angle) or _STUCK_DEFAULTS["texture"]
    used_names = {n for n in state.collected_names}
    for opt in options:
        if opt[0] not in used_names:
            return opt
    # All options already used — just cycle by modulo of how many items stuck
    return options[len(state.collected_names) % len(options)]


def _build_story_direction(state: SessionStateModel, chosen_theme: str = "") -> tuple[str, int]:
    """Build a rich synthesis direction from harvested story elements.

    The direction varies by synthesis_format:
    - collaborative_story: Tell a complete story with named characters
    - comparison_reveal: Guide comparison across observations
    - sorting_challenge: Guide sorting by criterion

    Args:
        state: Session state with story elements and scaffold.
        chosen_theme: Theme chosen by the child (or empty for random).

    Returns:
        (direction_text, max_sentences).
    """
    scaffold = None
    if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
        scaffold = state.creative_slots.story_scaffold

    synthesis_format = scaffold.synthesis_format if scaffold else "collaborative_story"

    # Use child's chosen theme, or fall back to random from scaffold
    theme = chosen_theme
    if not theme and scaffold and scaffold.story_themes:
        theme = random.choice(scaffold.story_themes)

    tier_sentences = {"T0": "4-6", "T1": "6-10", "T2": "8-14"}
    max_s = {"T0": 8, "T1": 11, "T2": 14}.get(state.tier, 11)

    if synthesis_format == "collaborative_story":
        # Named characters → story
        elems = state.story_elements
        if elems:
            parts = []
            for e in elems:
                name = e.character_name or f"Friend {e.round_number}"
                trait = e.trait_or_detail or "soft"
                parts.append(f"{name} ({trait})")
            chars_desc = ", ".join(parts)
        else:
            chars_desc = ", ".join(state.collected_names) if state.collected_names else "the collected friends"

        direction = (
            f"Tell a COMPLETE story about {chars_desc}. "
            f"The story must have:\n"
            f"- BEGINNING: Set the scene. The characters are together and something happens"
        )
        if theme:
            direction += f" ({theme})"
        direction += (
            ".\n"
            "- MIDDLE: Each character uses their special trait to help. "
            "Show what each one DOES, not just what they are.\n"
            "- END: The problem is solved and the friends celebrate together.\n\n"
        )
        if scaffold:
            direction += f"Premise: {scaffold.premise}. Goal: {scaffold.synthesis_goal}.\n"
        if state.synthesis_child_story:
            direction += (
                f'\nThe child tried to tell a story: "{state.synthesis_child_story}". '
                f"Weave their idea into the story — honor what they said and expand it.\n"
            )
        direction += (
            f"Length: {tier_sentences.get(state.tier, '6-10')} sentences. "
            f"Do NOT end with a question. End the story with a warm conclusion."
        )

    else:
        # comparison_reveal or sorting_challenge → comparison/sorting synthesis
        elems = state.story_elements
        obs_list = ""
        if elems:
            parts = []
            for i, e in enumerate(elems, 1):
                detail = e.trait_or_detail or e.child_words or f"find {i}"
                parts.append(f"Find {i}: {detail}")
            obs_list = "; ".join(parts)
        else:
            obs_list = "; ".join(state.collected_details) if state.collected_details else "the collected finds"

        obs_angle = ""
        sorting_criterion = ""
        if isinstance(state.creative_slots, Cat5CreativeSlots):
            obs_angle = state.creative_slots.observation_angle
            sorting_criterion = state.creative_slots.sorting_criterion

        direction = (
            f"Guide a fun comparison of all the finds. "
            f"Observations collected: {obs_list}.\n"
            f"Help the child see how the same thing ({obs_angle}) looks DIFFERENT on each item. "
        )
        if theme:
            direction += f"Use this angle: {theme}. "
        if sorting_criterion:
            direction += f"Sort by: {sorting_criterion}. "
        if scaffold:
            direction += f"\nGoal: {scaffold.synthesis_goal}. "
        direction += (
            f"\nThen invite the child to give each find a fun creative name "
            f"(e.g. 'Freckle Stone', 'Polka Petal'). "
            f"Length: {tier_sentences.get(state.tier, '6-10')} sentences. "
            f"End warmly — do NOT end with a question."
        )
        max_s = {"T0": 6, "T1": 8, "T2": 11}.get(state.tier, 8)

    return direction, max_s


def _fast_path_directive(normalized_text: str, state: SessionStateModel) -> TurnDirective | None:
    """Map common short phrases to TurnDirective without an LLM call.

    Context-dependent: "yes" means different things at different steps.
    Returns None when LLM classification is needed.
    """
    # Synthesis: detect delegation phrases ("you tell me", "you do it") → generate story directly
    if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase not in ("invite",):
        if "you tell" in normalized_text or "you do" in normalized_text or "tell me a story" in normalized_text:
            story_dir, max_s = _build_story_direction(state)
            state.synthesis_phase = "generate"
            return TurnDirective(
                action="advance",
                reasoning="Child asked AI to generate story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )

    if normalized_text in _DECLINE_WORDS:
        if _is_invitation_step(state.current_step):
            count = state.invitation_decline_count + 1
            if count >= 2:
                return TurnDirective(
                    action="exit",
                    reasoning="Child declined the invitation twice.",
                    response_direction="Gentle goodbye, no pressure to continue.",
                    emotion_tag="gentle",
                    sfx_cue="session_end_chime",
                )
            return TurnDirective(
                action="stay",
                reasoning="Child declined once. Re-invite with different framing.",
                response_direction="Re-invite warmly with a different approach. Don't repeat the same invitation.",
                emotion_tag="warm",
                stay_on_step=True,
            )
        if state.current_step == "STEP_4_SYNTHESIS":
            if state.synthesis_phase == "invite":
                return None  # invitation hasn't been shown yet
            story_dir, max_s = _build_story_direction(state)
            return TurnDirective(
                action="advance",
                reasoning="Child declined to make a story. AI generates the full story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
        # During collection: decline is unusual, let LLM handle
        return None

    if normalized_text in _CONFIRM_WORDS:
        if _is_invitation_step(state.current_step):
            # Build context-aware direction for the NEXT step
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                angle = state.creative_slots.observation_angle
                criterion = state.creative_slots.collection_criterion
                direction = (
                    f"Celebrate acceptance briefly, then invite the child to go find their first "
                    f"{angle} item. Encourage them to explore and find something that matches: "
                    f"{criterion}. Do NOT talk about the original photo."
                )
            elif isinstance(state.creative_slots, Cat1CreativeSlots):
                # Use the instruction recipe's rich scenario text when available
                scenario = ""
                if state.instruction_recipe:
                    rounds = state.instruction_recipe.step_instructions.rounds
                    if rounds:
                        scenario = rounds[0].scenario
                if not scenario and state.creative_slots.round_scenarios:
                    scenario = state.creative_slots.round_scenarios[0]
                if state.creative_slots.game_mechanic == "storytelling_chain":
                    question_guidance = (
                        f"Ask ONE question about what the {state.entity_name} "
                        f"sees, finds, or does in the scene — NOT about how it feels."
                    )
                else:
                    question_guidance = f"Ask ONE question about how the {state.entity_name} feels or reacts."
                direction = (
                    f"Celebrate acceptance briefly. This is a verbal/imagination game — the child "
                    f'stays with the photo on screen. Present the first scenario: "{scenario}". '
                    f"{question_guidance}"
                )
            else:
                direction = "Celebrate acceptance and introduce the first round of the activity."
            return TurnDirective(
                action="advance",
                reasoning="Child accepted the invitation.",
                response_direction=direction,
                emotion_tag="celebrating",
                max_sentences=3,
            )
        if state.current_step == "STEP_4_SYNTHESIS":
            # At invite phase the child hasn't been asked yet — the "ok" is
            # from the previous auto-advance, not a synthesis confirmation.
            # Generate the invitation first so the child knows what they're
            # agreeing to before we process their response.
            if state.synthesis_phase == "invite":
                return None  # let LLM Turn Director or fallback handle the invite

            names = ", ".join(state.collected_names) if state.collected_names else "our friends"
            scaffold = None
            if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
                scaffold = state.creative_slots.story_scaffold
            is_story_game = scaffold and scaffold.synthesis_format == "collaborative_story"

            if is_story_game and state.synthesis_phase not in ("child_try", "theme_choice", "generate"):
                # Child said yes → invite them to try making a story first
                state.synthesis_phase = "child_try"
                direction = (
                    f"The child wants a story about {names}! "
                    f"Encourage the child to try making one up. "
                    f"Ask: what happens to {names}? "
                    f"Keep it simple and inviting — they can say anything."
                )
                return TurnDirective(
                    action="stay",
                    reasoning="Child confirmed synthesis. Inviting them to try a story first.",
                    response_direction=direction,
                    emotion_tag="excited",
                    stay_on_step=True,
                    max_sentences=2,
                )

            # Fallback: generate story directly (no scaffold, or already in generate phase)
            story_dir, max_s = _build_story_direction(state)
            return TurnDirective(
                action="advance",
                reasoning="Generating story for synthesis.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
        if state.current_step.startswith("STEP_3_COLLECT_") and state.collection_phase == "photo":
            return TurnDirective(
                action="stay",
                reasoning="Child affirmed but hasn't selected a photo yet. Encourage finding.",
                response_direction=(
                    "Encourage the child to find and photograph something matching the collection criterion."
                ),
                emotion_tag="encouraging",
                stay_on_step=True,
            )
        # Other contexts: let LLM decide
        return None

    return None


async def _get_turn_directive(state: SessionStateModel, turn_input: "TurnInput") -> TurnDirective:
    """Get a TurnDirective via fast-path or LLM Turn Director call."""
    child_text = turn_input.text or ""

    # Fast path: synthesis invite phase — the child hasn't been invited yet.
    # Any input here (e.g. "ok") is from the previous auto-advance, not a
    # synthesis response. Generate the invitation first.
    if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "invite":
        names = ", ".join(state.collected_names) if state.collected_names else "your collected friends"
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
            scaffold = state.creative_slots.story_scaffold
        is_story_game = scaffold and scaffold.synthesis_format == "collaborative_story"

        if is_story_game:
            direction = (
                f"Invite the child to make up a little story about {names}. "
                f"Keep it warm and simple — ask if they'd like to imagine what {names} might do together."
            )
        else:
            obs_angle = ""
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                obs_angle = state.creative_slots.observation_angle
            direction = (
                f"Invite the child to compare all their finds together. "
                f"Ask if they'd like to see how the {obs_angle} looks different on each one."
            )

        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count += 1
        logger.info(
            "turn_director: step=%s action=stay (fast-path invite) synthesis_format=%s",
            state.current_step,
            scaffold.synthesis_format if scaffold else "unknown",
        )
        return TurnDirective(
            action="stay",
            reasoning="Synthesis invite phase — asking child before generating.",
            response_direction=direction,
            emotion_tag="gentle",
            stay_on_step=True,
            max_sentences=2,
        )

    # Fast path: synthesis sub-phases
    # Flow: invite → child_try (yes) / theme_choice (no) → generate
    if (
        state.current_step == "STEP_4_SYNTHESIS"
        and state.synthesis_phase in ("child_try", "theme_choice")
        and child_text
        and not turn_input.is_silent
    ):
        normalized_synth = child_text.strip().lower().rstrip("!.?")

        if state.synthesis_phase == "child_try":
            # Check if child declined to make a story → offer theme choices
            if normalized_synth in _DECLINE_WORDS:
                scaffold = None
                if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
                    scaffold = state.creative_slots.story_scaffold
                names = ", ".join(state.collected_names) if state.collected_names else "our friends"
                if scaffold and scaffold.story_themes and len(scaffold.story_themes) >= 2:
                    themes = random.sample(scaffold.story_themes, min(2, len(scaffold.story_themes)))
                    state.synthesis_phase = "theme_choice"
                    direction = (
                        f"That's okay! Ask the child what kind of adventure {names} should have. "
                        f'Offer two ideas: "{themes[0]}" or "{themes[1]}". '
                    )
                    if state.tier != "T0":
                        direction += "Also say they can suggest their own idea. "
                    fast = TurnDirective(
                        action="stay",
                        reasoning="Child declined to make a story. Offering theme choices.",
                        response_direction=direction,
                        emotion_tag="encouraging",
                        stay_on_step=True,
                        max_sentences=2,
                    )
                else:
                    # No themes available → AI generates directly
                    state.synthesis_phase = "generate"
                    story_dir, max_s = _build_story_direction(state)
                    fast = TurnDirective(
                        action="advance",
                        reasoning="Child declined. No themes available. AI generates story.",
                        response_direction=story_dir,
                        emotion_tag="playful",
                        max_sentences=max_s,
                    )
                logger.info(
                    "turn_director: step=%s action=%s (child declined story, offering themes)",
                    state.current_step,
                    fast.action,
                )
                state.last_directive_action = fast.action
                return fast

            # Child gave a story attempt — use it as seed
            state.synthesis_child_story = child_text.strip()
            state.synthesis_phase = "generate"
            story_dir, max_s = _build_story_direction(state, chosen_theme="")
            logger.info(
                "turn_director: step=%s action=advance (child story attempt) text=%s",
                state.current_step,
                child_text[:50],
            )
            fast = TurnDirective(
                action="advance",
                reasoning=f"Child attempted story: '{child_text[:50]}'. AI weaves into complete story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
            state.last_directive_action = fast.action

        else:
            # theme_choice: child picked a theme (or their own idea)
            chosen_theme = child_text.strip()
            state.synthesis_phase = "generate"
            story_dir, max_s = _build_story_direction(state, chosen_theme=chosen_theme)
            logger.info(
                "turn_director: step=%s action=advance (fast-path theme chosen) theme=%s",
                state.current_step,
                chosen_theme[:50],
            )
            fast = TurnDirective(
                action="advance",
                reasoning=f"Child chose story theme: '{chosen_theme[:50]}'. Generating story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
            state.last_directive_action = fast.action
        return fast

    # Fast path: celebrate step — always advance (or stay on silence)
    if _is_celebrate_step(state.current_step):
        if turn_input.is_silent and state.consecutive_silence < 2:
            role_title = ""
            if isinstance(state.creative_slots, Cat1CreativeSlots):
                role_title = state.creative_slots.role_title
            elif isinstance(state.creative_slots, Cat5CreativeSlots):
                role_title = state.creative_slots.role_title
            names_str = ", ".join(state.collected_names) if state.collected_names else "all the friends"
            return TurnDirective(
                action="stay",
                reasoning="Child is silent at celebrate — give them a moment, don't exit.",
                response_direction=(
                    f"Award the title '{role_title}' ceremonially. "
                    f"Recap the journey with {names_str}. Celebrate warmly."
                ),
                emotion_tag="proud",
                stay_on_step=True,
                max_sentences=4,
            )
        # Any input or auto-advance → advance to closing
        role_title = ""
        if isinstance(state.creative_slots, Cat1CreativeSlots):
            role_title = state.creative_slots.role_title
        elif isinstance(state.creative_slots, Cat5CreativeSlots):
            role_title = state.creative_slots.role_title
        names_str = ", ".join(state.collected_names) if state.collected_names else "all the friends"
        return TurnDirective(
            action="advance",
            reasoning="Celebrate step — advancing to closing.",
            response_direction=(
                f"Award the title '{role_title}' ceremonially. "
                f"Recap the journey with {names_str}. Celebrate the whole process warmly."
            ),
            emotion_tag="proud",
            max_sentences=4,
            sfx_cue="badge_awarded",
            screen_widget="badge_award",
        )

    # Fast path: closing step — always advance to end
    if _is_closing_step_directive(state.current_step):
        ib_concepts = ", ".join(state.ib_key_concepts) if state.ib_key_concepts else ""
        return TurnDirective(
            action="advance",
            reasoning="Closing step — wrapping up the activity.",
            response_direction=(
                f"Name the IB concept ({ib_concepts}) naturally connected to what they discovered. "
                f"Plant a curiosity seed for next time. Warm goodbye."
            ),
            emotion_tag="warm",
            max_sentences=3,
            screen_widget="badge_award",
            sfx_cue="badge_awarded",
        )

    # Fast path: correct photo pick — child selected a photo, phase is now "detail".
    # This is NOT silence — the child acted by picking a photo.
    if (
        turn_input.photo_id
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and state.detail_exchange_count == 0
    ):
        remaining = max(0, state.total_rounds - len(state.collected_photos))
        is_last = remaining == 0

        # Build context-aware direction using story scaffold if available
        direction = "Celebrate finding this item! Ask a detail question about it."
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
            scaffold = state.creative_slots.story_scaffold
            direction = (
                f"Celebrate finding this item! Based on the story scaffold strategy for round "
                f"{state.current_round}: {scaffold.harvest_question_strategy}. "
                f"Ask a question to harvest: {scaffold.harvest_per_round}."
            )
        if is_last:
            direction += (
                " This is the LAST find — you MUST still ask the harvest question. "
                "Do NOT celebrate completion or say 'all done'. The child still needs to "
                "describe this item before we move to synthesis."
            )

        sfx = "mission_complete_fanfare" if is_last else "slot_fill_chime"
        fast = TurnDirective(
            action="stay",
            reasoning=(
                f"Child selected correct photo {turn_input.photo_id}. Now in detail phase — ask a harvest question."
            ),
            response_direction=direction,
            emotion_tag="excited",
            stay_on_step=True,
            sfx_cue=sfx,
            must_model_first=state.tier == "T0",
            offer_binary_choice=state.tier == "T0",
        )
        logger.info(
            "turn_director: step=%s action=stay (fast-path photo pick) photo=%s remaining=%d",
            state.current_step,
            turn_input.photo_id,
            remaining,
        )
        state.last_directive_action = fast.action
        return fast

    # Fast path: child responded in detail phase.
    # Flow depends on synthesis_format:
    #   collaborative_story → 2 exchanges: (1) detail → ask name (2) name → advance
    #   comparison_reveal / sorting_challenge → 1 exchange: observation → advance
    #
    # Delegation phrases ("you ..." when short) skip this fast-path entirely
    # so the LLM Turn Director at the bottom of the function classifies them —
    # a fixed list can't anticipate every way a child asks the AI to answer.
    _detail_text = child_text.strip().lower().rstrip("!.?") if child_text else ""
    _is_detail_delegation = (
        bool(
            re.match(
                r"^(?:you |can you |could you |will you |would you |please )",
                _detail_text,
            )
        )
        and len(_detail_text.split()) <= 6
    )
    if (
        child_text
        and not turn_input.is_silent
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and not _is_detail_delegation
    ):
        normalized_detail = _detail_text

        # Determine if this is a naming game (2 exchanges) or observation game (1 exchange)
        is_naming_game = True  # default to naming
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots):
            scaffold = state.creative_slots.story_scaffold
            if scaffold and scaffold.synthesis_format != "collaborative_story":
                is_naming_game = False

        # Detect non-answers: child is stuck, confused, or asking AI to decide.
        if normalized_detail in _NON_ANSWER_PHRASES:
            state.detail_stuck_count += 1
            current_item = state.collected_photos[-1] if state.collected_photos else "this item"
            current_item_label = current_item.replace("_", " ")
            obs_angle = ""
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                obs_angle = state.creative_slots.observation_angle

            # After 2 consecutive non-answers, stop scaffolding: pick a playful
            # default and force-advance past the detail phase. This prevents
            # the infinite scaffold loop where the LLM keeps generating the
            # same "Is it soft like a bunny or smooth like an egg?" question.
            if state.detail_stuck_count >= 2:
                default_name, default_detail = _pick_stuck_default(state)
                _record_collection_detail(state, default_detail)
                if is_naming_game:
                    state.collected_names.append(default_name)
                state.detail_stuck_count = 0
                state.detail_exchange_count = 0
                state.round_advance_pending = True

                if is_naming_game:
                    direction = (
                        f"No worries! Let's call this one {default_name} — it feels {default_detail}. "
                        f"Then warmly invite the child to find the next item."
                    )
                else:
                    direction = (
                        f"No worries! This {current_item_label} looks {default_detail}. "
                        f"Then warmly invite the child to find the next item."
                    )
                fast = TurnDirective(
                    action="advance",
                    reasoning=(
                        f"Child stuck (2 consecutive non-answers). "
                        f"Applied default name='{default_name}' detail='{default_detail}'."
                    ),
                    response_direction=direction,
                    emotion_tag="gentle",
                    max_sentences=3,
                )
                logger.info(
                    "turn_director: step=%s action=advance (stuck default) name=%s detail=%s",
                    state.current_step,
                    default_name,
                    default_detail,
                )
                state.last_directive_action = fast.action
                return fast

            if is_naming_game:
                exchange_label = "texture" if state.detail_exchange_count == 0 else "naming"
                direction = (
                    f'The child said "{child_text}" — they need help with {exchange_label}. '
                    f"We are talking about the {current_item_label}. Model an answer yourself first. "
                )
                if state.detail_exchange_count == 0:
                    direction += (
                        f"Describe how the {current_item_label} feels in a playful way. "
                        f"Then offer a binary choice about the texture."
                    )
                else:
                    names_so_far = ", ".join(state.collected_names) if state.collected_names else ""
                    direction += f"Suggest two simple ONE-WORD name choices for the {current_item_label}. "
                    if names_so_far:
                        direction += f"Existing friends: {names_so_far} — this one needs its OWN name."
            else:
                exchange_label = "observation"
                direction = (
                    f'The child said "{child_text}" — they need help describing the {obs_angle}. '
                    f"We are talking about the {current_item_label}. Model an answer yourself first. "
                    f"Describe the {obs_angle} of the {current_item_label} in a playful way. "
                    f"Then offer a binary choice about the {obs_angle}."
                )

            fast = TurnDirective(
                action="need_help",
                reasoning=f"Child needs help with {exchange_label}: '{child_text[:30]}'. Scaffolding.",
                response_direction=direction,
                emotion_tag="gentle",
                stay_on_step=True,
                must_model_first=True,
                offer_binary_choice=True,
            )
            logger.info(
                "turn_director: step=%s action=need_help (non-answer %d) text=%s",
                state.current_step,
                state.detail_stuck_count,
                child_text[:30],
            )
            state.last_directive_action = fast.action
            return fast

        # Successful harvest — reset the stuck counter
        state.detail_stuck_count = 0
        state.detail_exchange_count += 1
        remaining = max(0, state.total_rounds - len(state.collected_photos))
        names_so_far = ", ".join(state.collected_names) if state.collected_names else ""
        details_so_far = ", ".join(state.collected_details) if state.collected_details else ""

        if is_naming_game:
            # --- Naming game: 2-exchange flow (detail → name) ---
            if state.detail_exchange_count == 1:
                _record_collection_detail(state, child_text)

                direction = (
                    f'Celebrate the child\'s description (they said: "{child_text}"). '
                    f"This is a NEW character that does NOT have a name yet. "
                    f"Do NOT use any previous character names for this one. "
                    f"Invite the child to give THIS NEW character a fun name. "
                )
                if state.tier == "T0":
                    direction += (
                        "Suggest two simple ONE-WORD name choices (e.g., Fuzzy or Cloudy — not compound names). "
                    )
                else:
                    direction += "Ask what they would name this friend. Let the child choose freely. "
                if names_so_far:
                    direction += (
                        f"(For reference only — PREVIOUS characters: {names_so_far}. "
                        f"Do NOT reuse these names or apply them to the current item.) "
                    )

                fast = TurnDirective(
                    action="stay",
                    reasoning=f"Child described detail: '{child_text[:50]}'. Now asking them to name.",
                    response_direction=direction,
                    emotion_tag="delighted",
                    stay_on_step=True,
                )
                logger.info(
                    "turn_director: step=%s action=stay (naming game exchange 1 — ask name) text=%s",
                    state.current_step,
                    child_text[:30],
                )
            else:
                trait = state.collected_details[-1] if state.collected_details else ""
                child_name = child_text.strip()

                for pat in _NAME_EXTRACT_PATTERNS:
                    m = pat.search(child_name)
                    if m:
                        child_name = m.group(1).strip().rstrip("!.?,")
                        break

                story_elem = StoryElement(
                    round_number=state.current_round,
                    character_name=child_name,
                    trait_or_detail=trait,
                    child_words=child_name,
                )

                direction = f'The child named this character "{child_name}". Celebrate the name enthusiastically! '
                if names_so_far:
                    direction += f"Introduce the whole crew so far: {names_so_far} and {child_name}. "
                if remaining > 0:
                    direction += f"Then invite the child to find the next item ({remaining} more to go)."
                else:
                    direction += (
                        "This was the last find! Celebrate the full team — name everyone. "
                        "Then tease what comes next — tell the child you're going to "
                        "make up a story together about the whole crew. Make it sound exciting."
                    )

                fast = TurnDirective(
                    action="advance",
                    reasoning=f"Child named character: '{child_name}'. Harvesting and advancing.",
                    response_direction=direction,
                    emotion_tag="celebrating",
                    stay_on_step=False,
                    story_element=story_elem,
                )
                logger.info(
                    "turn_director: step=%s action=advance (naming exchange 2 — name given) name=%s",
                    state.current_step,
                    child_name[:30],
                )
        else:
            # --- Observation game (comparison_reveal / sorting_challenge): ---
            # Single exchange: child describes observation → harvest → advance
            _record_collection_detail(state, child_text)

            obs_angle = ""
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                obs_angle = state.creative_slots.observation_angle

            story_elem = StoryElement(
                round_number=state.current_round,
                character_name=None,
                trait_or_detail=child_text,
                child_words=child_text,
            )

            direction = f'Celebrate the child\'s observation (they said: "{child_text}"). '
            if details_so_far:
                direction += f"Previous observations: {details_so_far}. Briefly connect to what they noticed before. "
            if remaining > 0:
                direction += (
                    f"Then invite the child to find the next item ({remaining} more to go). "
                    f"Use invitational language about finding something with {obs_angle}."
                )
            else:
                direction += (
                    "This was the last find! Celebrate the full collection. "
                    "Then tease what comes next — tell the child you're going to "
                    "look at all the finds together and see how the "
                    f"{obs_angle} looks different on each one. "
                    "Make it sound exciting, like a reveal."
                )

            fast = TurnDirective(
                action="advance",
                reasoning=f"Child described {obs_angle}: '{child_text[:50]}'. Harvesting observation and advancing.",
                response_direction=direction,
                emotion_tag="celebrating" if remaining == 0 else "delighted",
                stay_on_step=False,
                story_element=story_elem,
            )
            logger.info(
                "turn_director: step=%s action=advance (observation — %s) text=%s remaining=%d",
                state.current_step,
                obs_angle,
                child_text[:30],
                remaining,
            )

        state.last_directive_action = fast.action
        return fast

    # Fast path for common short phrases
    if child_text and not turn_input.is_silent:
        normalized = child_text.strip().lower().rstrip("!.?")
        fast = _fast_path_directive(normalized, state)
        if fast is not None:
            logger.info(
                "turn_director: step=%s action=%s (fast-path) text=%s",
                state.current_step,
                fast.action,
                normalized,
            )
            state.last_directive_action = fast.action
            return fast

    # Enrich child_text with photo context so the LLM doesn't think it's silence
    if turn_input.photo_id and not child_text:
        child_text = f"[selected photo: {turn_input.photo_id}]"

    # LLM Turn Director call
    directive = await _turn_director.direct_turn(state, child_text)

    # Post-process Cat1 advance directives: inject the EXACT next scenario text
    # from the instruction recipe so the speaker doesn't rely on the LLM's summary
    if (
        directive.action == "advance"
        and state.template_type == "cat1"
        and state.current_step.startswith("STEP_3_ROUND_")
        and state.instruction_recipe
    ):
        next_round = state.current_round + 1
        recipe_rounds = state.instruction_recipe.step_instructions.rounds
        next_scenario = ""
        for r in recipe_rounds:
            if r.round_number == next_round:
                next_scenario = r.scenario
                break
        if next_scenario:
            # Append the exact scenario to the direction so the speaker uses it
            directive.response_direction += f' NEXT SCENARIO (use this EXACT text): "{next_scenario}"'

    state.last_directive_action = directive.action
    return directive


async def _resolve_turn_with_directive(
    state: SessionStateModel,
    turn_input: "TurnInput",
    script_agent: ScriptAgent,
    directive: TurnDirective,
) -> TurnResult:
    """Process a turn using the Turn Director's action-based routing.

    Replaces the ~300-line if/elif routing in the legacy path with a
    simple match on directive.action.
    """

    speaker_errors: list[str] = []

    logger.info(
        "directive_to_speaker: step=%s action=%s reasoning=%s direction=%s",
        state.current_step,
        directive.action,
        directive.reasoning,
        directive.response_direction,
    )

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
        debug = _build_debug_payload(state, gen_debug, script_agent, turn_response)
        debug["turn_director"] = {
            "action": directive.action,
            "reasoning": directive.reasoning,
            "response_direction": directive.response_direction,
            "emotion_tag": directive.emotion_tag,
        }
        if directive.story_element:
            debug["turn_director"]["story_element"] = {
                "round": directive.story_element.round_number,
                "character_name": directive.story_element.character_name,
                "trait_or_detail": directive.story_element.trait_or_detail,
                "child_words": directive.story_element.child_words[:100],
            }
        if speaker_errors:
            debug["turn_director"]["speaker_errors"] = speaker_errors
        return debug

    # Record story element if harvested
    if directive.story_element:
        state.story_elements.append(directive.story_element)
        if directive.story_element.character_name:
            state.collected_names.append(directive.story_element.character_name)
        if directive.story_element.trait_or_detail:
            state.collected_details.append(directive.story_element.trait_or_detail)

    # --- Pre-generation state mutations per action ---
    action = directive.action
    auto_advance = False
    response_type = _get_response_type(state.current_step)
    stay_on_step = False
    turn_response: TurnResponse | None = None

    if action == "advance":
        if _is_invitation_step(state.current_step) and not state.invitation_accepted:
            state.invitation_accepted = True
            state.invitation_decline_count = 0

        # Reset collection phase when advancing from a collection step
        if state.current_step.startswith("STEP_3_COLLECT_"):
            state.collection_phase = "photo"
            state.detail_exchange_count = 0
            state.detail_stuck_count = 0

        # Synthesis: show loading screen then generate companion images.
        # collaborative_story → 3 story scenes. comparison_reveal → 1 reveal
        # scene showing items side by side. Both end with an achievement image.
        if state.current_step == "STEP_4_SYNTHESIS":
            return _loading_result(state)

        # Celebrate: generate celebrate dialogue, show badge, then auto-advance
        # to closing on the NEXT turn. This keeps celebrate and closing as
        # separate turns so the badge stays visible long enough.
        if _is_celebrate_step(state.current_step):
            directive.screen_widget = "achievement_image"
            directive.sfx_cue = "badge_awarded"
            # Celebrate auto-advances to closing. The speaker LLM tends to end
            # with a conversational question ("Would you like to wear your
            # badge?") which creates an unnatural UX when we auto-advance
            # without waiting for an answer. Append a hard no-question
            # constraint to the direction before generating.
            no_question_suffix = (
                " End with a warm celebratory statement. Do NOT ask the child "
                "a question at the end — do not say 'would you like...', "
                "'shall we...', 'ready for...', or anything similar. "
                "The celebration is a statement, not an invitation."
            )
            if no_question_suffix not in (directive.response_direction or ""):
                directive.response_direction = (directive.response_direction or "") + no_question_suffix
            try:
                turn_response = await script_agent.generate_turn_from_directive(state, directive)
            except Exception as e:
                speaker_errors.append(f"celebrate: {e}")
                logger.warning("Directive speaker failed at celebrate, falling back: %s", e)
                turn_response, _ = await _generate_with_retry(script_agent, state)
            turn_response.screen_widget = "achievement_image"
            turn_response.sfx_cue = "badge_awarded"
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1

            # Snapshot the celebrate screen frame BEFORE advancing — otherwise
            # _get_screen_frame(state) would return the STEP_6_CLOSING frame
            # (concept_reveal) and the achievement image would never render.
            celebrate_screen_frame = _get_screen_frame(state)

            # Advance to closing now, so the next auto-advance turn
            # arrives at STEP_6_CLOSING instead of looping at celebrate.
            _advance_state(state)

            # Force auto_advance=True here: we explicitly want a closing turn
            # to follow so concept_reveal actually renders. _should_auto_advance
            # would return False because state is now at closing, which would
            # leave the frontend stuck on the celebrate frame forever.
            return TurnResult(
                turn_response=turn_response,
                screen_frame=celebrate_screen_frame,
                auto_advance=True,
                response_type="celebrate",
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        # Generate speaker output BEFORE advancing state so the speaker
        # loads step instructions for the CURRENT step (where the response
        # direction was authored), not the NEXT step.
        is_closing = _is_closing_step_directive(state.current_step)
        try:
            turn_response = await script_agent.generate_turn_from_directive(state, directive)
        except Exception as e:
            speaker_errors.append(f"speaker: {e}")
            logger.warning("Directive speaker failed, falling back to legacy path: %s", e)
            turn_response, _ = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1

        # For closing: Cat5 uses concept_reveal, Cat1 keeps achievement_image
        if is_closing:
            if state.template_type == "cat5":
                turn_response.screen_widget = "concept_reveal"
            else:
                turn_response.screen_widget = "achievement_image"

        # Snapshot screen frame BEFORE advancing — closing advances to ENDED
        # which has no matching widget and would fall through to ExplorerMap.
        pre_advance_frame = _get_screen_frame(state) if is_closing else None

        _advance_state(state)

        # When the last collection round advances into STEP_4_SYNTHESIS,
        # the advance response already teases the synthesis (e.g. "let's
        # compare all your finds!"), so skip the invite phase — treat the
        # child's next reply as a response to that built-in invitation.
        if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "invite":
            state.synthesis_phase = "evaluate"
            state.synthesis_prompt_count = 1

        if is_terminal(state.current_step):
            state.status = "completed"
            return TurnResult(
                turn_response=turn_response,
                screen_frame=pre_advance_frame or _get_screen_frame(state),
                auto_advance=False,
                response_type="closing",
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        auto_advance = _should_auto_advance(state)
        response_type = _get_response_type(state.current_step)

    elif action in ("stay", "need_help", "redirect"):
        stay_on_step = True
        if action == "stay" and _is_invitation_step(state.current_step):
            normalized = (turn_input.text or "").strip().lower().rstrip("!.?")
            if normalized in _DECLINE_WORDS:
                state.invitation_decline_count += 1

    elif action == "exit":
        state.current_step = EARLY_EXIT
        state.status = "exited"
        response_type = "graceful_exit"

    if action != "advance":
        # For non-advance actions, generate after state mutations
        try:
            turn_response = await script_agent.generate_turn_from_directive(state, directive)
        except Exception as e:
            speaker_errors.append(f"speaker: {e}")
            logger.warning("Directive speaker failed, falling back to legacy path: %s", e)
            turn_response, _ = await _generate_with_retry(script_agent, state)

        turn_response.stay_on_step = stay_on_step
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1

    assert turn_response is not None, "turn_response must be set by advance/stay/exit branch"

    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=auto_advance,
        response_type=response_type,
        error_exit=state.status == "error",
        debug=_debug(None, turn_response),
    )
