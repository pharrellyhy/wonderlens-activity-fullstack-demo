"""Director Agent — plans activity composition using Gemini 2.0 Flash."""

import asyncio
import json
import time
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import types

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..scenarios import SCENARIO_CATEGORIES
    from ..schemas import CompositionPlan
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES
    from schemas import CompositionPlan

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "director.md"


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


def _default_plan(context: dict) -> CompositionPlan:
    """Return a sensible default plan based on activity category."""
    activity_type = context.get("activity_type", "mood_changer_dog")
    category = SCENARIO_CATEGORIES.get(activity_type, "category_1")
    tier = context.get("tier", "T0")
    entity = context.get("entity", "object")

    if category == "category_5":
        return CompositionPlan(
            creative_brief=f"Guide the child on a collection mission inspired by the {entity}.",
            modalities=["voice", "screen"],
            round_count=3,
            screen_strategy="progressive",
            widget_hint="progress_tracker",
            emotional_arc="build_excitement",
            ib_concept_integration="Notice patterns through collecting similar items.",
            closing_concept_targets=["Form", "Connection"][: 2 if tier != "T0" else 1],
            transition_strategy="challenge",
        )

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
    )


class DirectorAgent:
    """Plans activity composition — creative direction, round count, screen strategy."""

    def __init__(self) -> None:
        self.skill = _SKILL_PATH.read_text() if _SKILL_PATH.exists() else ""

    async def run(self, context: dict, session_id: str = "") -> CompositionPlan:
        settings = get_settings()
        start = time.perf_counter()

        user_prompt = json.dumps(
            {
                "entity": context.get("entity", "unknown"),
                "tier": context.get("tier", "T0"),
                "activity_type": context.get("activity_type", "mood_changer_dog"),
                "category": SCENARIO_CATEGORIES.get(context.get("activity_type", ""), "category_1"),
                "ib_theme": context.get("ib_theme", "Who We Are"),
                "key_concepts": context.get("key_concepts", []),
                "scene": context.get("scene", ""),
                "features": context.get("features", []),
            }
        )

        try:
            client = _get_client()
            loop = asyncio.get_running_loop()

            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=settings.gemini_model,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.skill,
                            response_mime_type="application/json",
                            response_schema=CompositionPlan,
                            temperature=0.3,
                            max_output_tokens=settings.director_max_tokens,
                        ),
                    ),
                ),
                timeout=settings.director_timeout_ms / 1000,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            plan = CompositionPlan.model_validate_json(response.text)
            logger.info(f"Director: rounds={plan.round_count}, strategy={plan.screen_strategy}, latency={latency_ms}ms")

            await log_agent_call(session_id, "director", latency_ms, True)
            return plan

        except asyncio.TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(f"Director timed out ({latency_ms}ms), using default plan")
            await log_agent_call(session_id, "director", latency_ms, False, error_message="timeout")
            return _default_plan(context)

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Director failed ({latency_ms}ms): {e}")
            await log_agent_call(session_id, "director", latency_ms, False, error_message=str(e))
            return _default_plan(context)
