"""Pipeline orchestrator — runs the full agent pipeline with retry and fallback."""

import json
from pathlib import Path

try:
    from ..config import get_settings
    from ..logger import setup_logger
    from ..scenarios import build_activity_context, load_scenario
    from ..schemas import ActivityRecipe
    from .director import DirectorAgent
    from .recipe_assembler import RecipeAssembler
    from .script_agent import ScriptAgent
    from .visual_agent import VisualAgent
except ImportError:
    from config import get_settings
    from logger import setup_logger
    from scenarios import build_activity_context, load_scenario
    from schemas import ActivityRecipe

    from agents.director import DirectorAgent
    from agents.recipe_assembler import RecipeAssembler
    from agents.script_agent import ScriptAgent
    from agents.visual_agent import VisualAgent

logger = setup_logger(__name__)

_FALLBACKS_DIR = Path(__file__).parent.parent / "fallbacks"


def load_fallback(activity_type: str) -> ActivityRecipe:
    """Load a pre-authored fallback recipe."""
    path = _FALLBACKS_DIR / f"{activity_type}.json"
    if not path.exists():
        # Try mood_changer_dog as ultimate fallback
        path = _FALLBACKS_DIR / "mood_changer_dog.json"
    with open(path) as f:
        data = json.load(f)
    return ActivityRecipe.model_validate(data)


async def generate_recipe(context: dict, session_id: str = "") -> ActivityRecipe:
    """Run the full agent pipeline to generate an ActivityRecipe.

    Flow: Director → Script + Visual → Assembler
    Retries up to max_retries times, then falls back to a pre-authored recipe.
    """
    settings = get_settings()
    director = DirectorAgent()
    script_agent = ScriptAgent()
    visual_agent = VisualAgent()
    assembler = RecipeAssembler()

    # Enrich context with activity_context string from scenario
    if "activity_context" not in context:
        scenario = load_scenario(context.get("activity_type", "mood_changer_dog"))
        vision_result = {
            "entity": context.get("entity", "unknown"),
            "scene": context.get("scene", ""),
            "features": context.get("features", []),
        }
        context["activity_context"] = build_activity_context(scenario, vision_result)
        # Pull key_concepts from scenario if not in context
        if "key_concepts" not in context:
            context["key_concepts"] = scenario.get("key_concepts", [])
        if "ib_theme" not in context:
            context["ib_theme"] = "Who We Are"

    last_error = None
    for attempt in range(settings.max_retries):
        try:
            plan = await director.run(context, session_id)
            script = await script_agent.run(plan, context, session_id)
            visuals = visual_agent.run(plan, context)
            recipe = assembler.merge(script, visuals, plan, context)

            logger.info(
                f"Pipeline: attempt {attempt + 1} succeeded, "
                f"rounds={len(recipe.voice_script.rounds)}, "
                f"frames={len(recipe.screen_frames)}"
            )
            return recipe

        except Exception as e:
            last_error = e
            logger.warning(f"Pipeline attempt {attempt + 1}/{settings.max_retries} failed: {e}")

    # All retries failed → load fallback
    activity_type = context.get("activity_type", "mood_changer_dog")
    logger.error(
        f"All {settings.max_retries} pipeline attempts failed, using fallback for {activity_type}. Last error: {last_error}"
    )
    return load_fallback(activity_type)
