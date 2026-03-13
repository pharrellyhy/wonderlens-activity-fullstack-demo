"""Director Agent — plans activity composition using OpenAI GPT-5.2."""

import json
import time
from functools import lru_cache
from pathlib import Path

from openai import APITimeoutError, AsyncOpenAI

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..scenarios import SCENARIO_CATEGORIES
    from ..schemas import CompositionPlan
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES
    from schemas import CompositionPlan
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "director.md"


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        max_retries=0,
    )


def _template_type_from_category(activity_type: str) -> str:
    """Map activity type to template type."""
    category = SCENARIO_CATEGORIES.get(activity_type, "category_1")
    return "cat5" if category == "category_5" else "cat1"


def _default_creative_slots_cat1(context: dict) -> Cat1CreativeSlots:
    """Return default Cat 1 creative slots."""
    entity = context.get("entity", "object")
    return Cat1CreativeSlots(
        game_mechanic="what_would_it_say",
        metaphor=f"This {entity} has been on so many adventures!",
        role_title=f"{entity.title()} Whisperer",
        round_scenarios=[
            f"The {entity} is taking a nap",
            f"The {entity} is at a party",
            f"The {entity} is on the moon",
        ],
        escalation_axis="scenarios go from everyday to fantastical",
        observation_detail=f"the interesting details of this {entity}",
    )


def _default_creative_slots_cat5(context: dict) -> Cat5CreativeSlots:
    """Return default Cat 5 creative slots."""
    entity = context.get("entity", "object")
    tier = context.get("tier", "T0")
    count = 2 if tier == "T0" else 3
    return Cat5CreativeSlots(
        observation_angle="shape",
        collection_criterion=f"Find {count} things with different shapes near this {entity}",
        collection_count=count,
        mission_metaphor=f"You are a Shape Detective on a secret {entity} mission!",
        role_title=f"{entity.title()} Shape Specialist",
        synthesis_type="naming_story" if tier in ("T0", "T1") else "comparison_chart",
        stuck_hint="Try looking around you — there might be interesting shapes nearby!",
        naming_prompt="What shape does this remind you of? Give it a fun name!",
    )


def _default_plan(context: dict) -> CompositionPlan:
    """Return a sensible default plan based on activity category."""
    activity_type = context.get("activity_type", "mood_changer_dog")
    template_type = _template_type_from_category(activity_type)
    tier = context.get("tier", "T0")
    entity = context.get("entity", "object")

    if template_type == "cat5":
        slots = _default_creative_slots_cat5(context)
        return CompositionPlan(
            creative_brief=f"Guide the child on a collection mission inspired by the {entity}.",
            modalities=["voice", "screen"],
            round_count=slots.collection_count,
            screen_strategy="progressive",
            widget_hint="progress_tracker",
            emotional_arc="build_excitement",
            ib_concept_integration="Notice patterns through collecting similar items.",
            closing_concept_targets=["Form", "Connection"][: 2 if tier != "T0" else 1],
            transition_strategy="challenge",
            template_type="cat5",
            creative_slots=slots,
        )

    slots = _default_creative_slots_cat1(context)
    return CompositionPlan(
        creative_brief=f"Explore emotions and perspectives through imaginative play with the {entity}.",
        modalities=["voice", "screen"],
        round_count=3,
        screen_strategy="per_round",
        widget_hint="character_display",
        emotional_arc="playful_surprise",
        ib_concept_integration="Discover different perspectives through role-play scenarios.",
        closing_concept_targets=["Perspective"] if tier == "T0" else ["Perspective", "Change"],
        transition_strategy="imagination_prompt",
        template_type="cat1",
        creative_slots=slots,
    )


class DirectorAgent:
    """Plans activity composition — creative direction, round count, screen strategy, creative slots."""

    def __init__(self) -> None:
        self.skill = _SKILL_PATH.read_text() if _SKILL_PATH.exists() else ""

    async def run(self, context: dict, session_id: str = "") -> CompositionPlan:
        settings = get_settings()
        start = time.perf_counter()

        activity_type = context.get("activity_type", "mood_changer_dog")
        template_type = _template_type_from_category(activity_type)

        user_prompt = json.dumps(
            {
                "entity": context.get("entity", "unknown"),
                "tier": context.get("tier", "T0"),
                "activity_type": activity_type,
                "category": SCENARIO_CATEGORIES.get(activity_type, "category_1"),
                "template_type": template_type,
                "ib_theme": context.get("ib_theme", "Who We Are"),
                "key_concepts": context.get("key_concepts", []),
                "scene": context.get("scene", ""),
                "features": context.get("features", []),
            }
        )

        try:
            client = _get_client()

            response = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.skill},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=CompositionPlan,
                temperature=0.3,
                max_completion_tokens=settings.director_max_tokens,
                timeout=settings.director_timeout_ms / 1000,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            plan = response.choices[0].message.parsed

            if plan is None:
                raise ValueError("Model returned unparseable response")

            # Ensure template_type is set
            plan.template_type = template_type

            # Fill default creative slots if the LLM didn't provide them
            if plan.creative_slots is None:
                if template_type == "cat5":
                    plan.creative_slots = _default_creative_slots_cat5(context)
                else:
                    plan.creative_slots = _default_creative_slots_cat1(context)

            logger.info(
                f"Director: rounds={plan.round_count}, strategy={plan.screen_strategy}, "
                f"template={template_type}, latency={latency_ms}ms"
            )
            await log_agent_call(session_id, "director", latency_ms, True)
            return plan

        except APITimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(f"Director timed out ({latency_ms}ms), using default plan")
            await log_agent_call(session_id, "director", latency_ms, False, error_message="timeout")
            return _default_plan(context)

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Director failed ({latency_ms}ms): {e}")
            await log_agent_call(session_id, "director", latency_ms, False, error_message=str(e))
            return _default_plan(context)
