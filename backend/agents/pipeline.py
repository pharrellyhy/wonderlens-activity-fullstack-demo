"""Pipeline orchestrator — initializes sessions with Director + first Script turn."""

import asyncio
import json
from pathlib import Path

try:
    from ..logger import setup_logger
    from ..scenarios import SCENARIO_CATEGORIES, build_activity_context, load_scenario
    from ..schemas import ActivityRecipe
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import ConversationTurn, SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import next_step
    from .director import DirectorAgent
    from .script_agent import ScriptAgent, ScriptAgentError
    from .visual_agent import VisualAgent
except ImportError:
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES, build_activity_context, load_scenario
    from schemas import ActivityRecipe
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import next_step

    from agents.director import DirectorAgent
    from agents.script_agent import ScriptAgent, ScriptAgentError
    from agents.visual_agent import VisualAgent

logger = setup_logger(__name__)

_FALLBACKS_DIR = Path(__file__).parent.parent / "fallbacks"

# Default hook lines for when Script Agent fails on the very first turn
_DEFAULT_HOOKS = {
    "cat1": "(excited) Wow, look at what you found! This is amazing! I have an idea for a really fun game we can play together!",
    "cat5": "(curious) Oh, how interesting! Look at all the cool details! I wonder if there are more things like this around here...",
}


def load_fallback(activity_type: str) -> ActivityRecipe:
    """Load a pre-authored fallback recipe (legacy support)."""
    path = _FALLBACKS_DIR / f"{activity_type}.json"
    if not path.exists():
        path = _FALLBACKS_DIR / "mood_changer_dog.json"
    with open(path) as f:
        data = json.load(f)
    return ActivityRecipe.model_validate(data)


async def initialize_session(
    context: dict,
    session_id: str,
) -> tuple[SessionStateModel, TurnResponse]:
    """Initialize a new session: Director → create state → Script (hook turn).

    Args:
        context: Vision result + tier + activity info.
        session_id: Unique session identifier.

    Returns:
        Tuple of (session state, first turn response).
    """
    director = DirectorAgent()
    script_agent = ScriptAgent()
    visual_agent = VisualAgent()

    # Enrich context with activity_context string from scenario
    if "activity_context" not in context:
        scenario = load_scenario(context.get("activity_type", "mood_changer_dog"))
        vision_result = {
            "entity": context.get("entity", "unknown"),
            "scene": context.get("scene", ""),
            "features": context.get("features", []),
        }
        context["activity_context"] = build_activity_context(scenario, vision_result)
        if "key_concepts" not in context:
            context["key_concepts"] = scenario.get("key_concepts", [])
        if "ib_theme" not in context:
            context["ib_theme"] = "Who We Are"

    # Step 1: Director Agent — fills creative slots
    plan = await director.run(context, session_id)

    # Determine template type
    activity_type = context.get("activity_type", "mood_changer_dog")
    template_type = plan.template_type
    tier = context.get("tier", "T0")

    # Ensure creative slots exist
    if plan.creative_slots is None:
        category = SCENARIO_CATEGORIES.get(activity_type, "category_1")
        if category == "category_5":
            plan.creative_slots = Cat5CreativeSlots(
                observation_angle="shape",
                collection_criterion="Find things with different shapes",
                collection_count=2 if tier == "T0" else 3,
                mission_metaphor="You are a Shape Detective!",
                role_title="Shape Specialist",
                synthesis_type="naming_story",
                stuck_hint="Try looking around you!",
                naming_prompt="What shape does this remind you of?",
            )
        else:
            plan.creative_slots = Cat1CreativeSlots(
                game_mechanic="what_would_it_say",
                metaphor=f"This {context.get('entity', 'friend')} has so many stories!",
                role_title="Story Whisperer",
                round_scenarios=["relaxing at home", "at a big party", "flying through space"],
                escalation_axis="everyday to fantastical",
                observation_detail=f"the interesting features of this {context.get('entity', 'friend')}",
            )

    # Step 2: Create session state
    state = SessionStateModel(
        session_id=session_id,
        tier=tier,
        template_type=template_type,
        activity_type=activity_type,
        current_step="STEP_1_HOOK",
        current_round=0,
        total_rounds=plan.round_count,
        creative_slots=plan.creative_slots,
        entity_name=context.get("entity", "object"),
        entity_attributes=context.get("features", []),
        entity_category=context.get("entity_category", ""),
        scene=context.get("scene", ""),
        ib_key_concepts=context.get("key_concepts", []),
        photo_url=context.get("photo_url", ""),
    )

    # Step 3: Visual Agent + Script Agent in parallel
    async def _run_visual() -> None:
        try:
            visual_result = await visual_agent.run(plan, context, session_id)
            state.visual_frames = visual_result.screen_frames
            state.celebration_frame = visual_result.celebration_frame
        except Exception as e:
            logger.warning(f"Visual Agent failed: {e}")

    async def _run_script() -> TurnResponse:
        try:
            return await script_agent.generate_turn(state)
        except ScriptAgentError:
            logger.warning("Script Agent failed for hook, retrying once")
            try:
                return await script_agent.generate_turn(state)
            except ScriptAgentError:
                logger.error("Script Agent failed twice for hook, using default")
                default_hook = _DEFAULT_HOOKS.get(template_type, _DEFAULT_HOOKS["cat1"])
                return TurnResponse(
                    dialogue=default_hook,
                    tone_marker="excited",
                    screen_widget="photo_display",
                    screen_widget_params={"description": f"Photo of {state.entity_name}", "entity": state.entity_name},
                    screen_animation="sparkle_highlight",
                    sfx_cue="wonder_chime",
                )

    visual_task = asyncio.create_task(_run_visual())
    script_task = asyncio.create_task(_run_script())
    first_turn = await script_task
    await visual_task

    # Record hook in conversation history
    state.conversation_history.append(
        ConversationTurn(
            role="ai",
            text=first_turn.dialogue,
            step=state.current_step,
            round_number=None,
        )
    )

    # Advance to next step
    state.current_step = next_step(state.current_step, state.template_type, state.current_round, state.total_rounds)
    state.turn_count = 1

    logger.info(
        f"Session initialized: {session_id}, activity={activity_type}, "
        f"template={template_type}, rounds={plan.round_count}"
    )

    return state, first_turn


# Legacy function for backward compatibility
async def generate_recipe(context: dict, session_id: str = "") -> ActivityRecipe:
    """Legacy pipeline — loads a fallback recipe.

    The new architecture uses initialize_session() instead.
    """
    activity_type = context.get("activity_type", "mood_changer_dog")
    logger.warning(f"generate_recipe() is deprecated, loading fallback for {activity_type}")
    return load_fallback(activity_type)
