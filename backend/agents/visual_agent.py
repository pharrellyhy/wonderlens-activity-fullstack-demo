"""Visual Agent — LLM-based screen frame composition with rule-based fallback."""

import json
import time
from functools import lru_cache
from pathlib import Path

import httpx
from openai import AsyncOpenAI

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas import CompositionPlan, ScreenFrame, VisualComposition
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas import CompositionPlan, ScreenFrame, VisualComposition

logger = setup_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "visual_system.md"

ALLOWED_WIDGETS = {"photo_display", "character_display", "progress_tracker", "photo_grid", "badge_award"}

ALLOWED_SFX = {
    "wonder_chime",
    "scene_woosh",
    "celebration_fanfare",
    "photo_shutter_click",
    "slot_fill_chime",
    "mission_accepted",
    "mission_complete_fanfare",
    "badge_awarded",
    "excitement_rising",
    "game_start_chime",
}

SFX_LABELS: dict[str, str] = {
    "wonder_chime": "A magical wonder chime",
    "scene_woosh": "Scene transition whoosh",
    "celebration_fanfare": "Celebration fanfare",
    "photo_shutter_click": "Camera shutter click",
    "slot_fill_chime": "Collection slot filled",
    "mission_accepted": "Mission accepted fanfare",
    "mission_complete_fanfare": "Mission complete celebration",
    "badge_awarded": "Badge awarded sparkle",
    "excitement_rising": "Excitement rising",
    "game_start_chime": "Game start chime",
}

ACTIVITY_WIDGET_MAP: dict[str, str] = {
    "mood_changer": "character_display",
    "mood_changer_dog": "character_display",
    "dream_whisperer": "character_display",
    "dream_whisperer_cat": "character_display",
    "time_machine": "character_display",
    "time_machine_dinosaur": "character_display",
    "polka_dot_patrol": "progress_tracker",
    "fluffy_expedition": "progress_tracker",
    "fluffy_expedition_dandelion": "progress_tracker",
}

EMOTIONAL_ARC_ANIMATION: dict[str, str] = {
    "build_excitement": "celebration_burst",
    "calm_curiosity": "gentle_pulse",
    "playful_surprise": "appear",
    "gentle_wonder": "sparkle_highlight",
}

CELEBRATION_ANIMATION: dict[str, str] = {
    "build_excitement": "mission_complete_fanfare",
    "calm_curiosity": "sparkle_highlight",
    "playful_surprise": "celebration_burst",
    "gentle_wonder": "badge_reveal",
}


@lru_cache(maxsize=1)
def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text()
    return ""


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.ali_api_key,
        base_url=settings.ali_base_url,
        max_retries=0,
        timeout=httpx.Timeout(30.0, connect=5.0),
    )


def _validate_composition(comp: VisualComposition) -> VisualComposition:
    """Validate and sanitize widget names and SFX cues."""
    for frame in comp.screen_frames:
        if frame.widget not in ALLOWED_WIDGETS:
            frame.widget = "photo_display"
        if frame.sfx_cue and frame.sfx_cue not in ALLOWED_SFX:
            frame.sfx_cue = None
            frame.sfx_label = None
    if comp.celebration_frame:
        if comp.celebration_frame.widget not in ALLOWED_WIDGETS:
            comp.celebration_frame.widget = "badge_award"
        if comp.celebration_frame.sfx_cue and comp.celebration_frame.sfx_cue not in ALLOWED_SFX:
            comp.celebration_frame.sfx_cue = None
            comp.celebration_frame.sfx_label = None
    return comp


class VisualAgent:
    """Generates screen frames using Qwen LLM with rule-based fallback."""

    async def run(self, plan: CompositionPlan, context: dict, session_id: str = "") -> VisualComposition:
        """Generate visual composition, trying LLM first then falling back to rules."""
        start = time.perf_counter()
        try:
            result = await self._llm_generate(plan, context)
            result = _validate_composition(result)
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.info(f"Visual (LLM): {len(result.screen_frames)} frames, latency={latency_ms}ms")
            await log_agent_call(session_id, "visual", latency_ms, True)
            return result
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(f"Visual LLM failed ({latency_ms}ms): {e}, using rule-based fallback")
            await log_agent_call(session_id, "visual", latency_ms, False, error_message=str(e))
            return self._rule_based_fallback(plan, context)

    async def _llm_generate(self, plan: CompositionPlan, context: dict) -> VisualComposition:
        """Call ALI Qwen to generate visual composition."""
        settings = get_settings()
        client = _get_client()
        prompt = _load_prompt()

        schema_json = json.dumps(VisualComposition.model_json_schema(), indent=2)

        user_content = (
            f"Entity: {context.get('entity', 'object')}\n"
            f"Activity type: {context.get('activity_type', 'mood_changer_dog')}\n"
            f"Emotional arc: {plan.emotional_arc}\n"
            f"Screen strategy: {plan.screen_strategy}\n"
            f"Round count: {plan.round_count}\n"
            f"Scene: {context.get('scene', '')}\n"
            f"Key concepts: {context.get('key_concepts', [])}\n"
            f"\nRespond with a single JSON object matching this schema:\n{schema_json}"
        )

        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )

        text = response.choices[0].message.content or ""
        return VisualComposition.model_validate_json(text)

    def _rule_based_fallback(self, plan: CompositionPlan, context: dict) -> VisualComposition:
        """Deterministic rule-based frame generation (original logic with labels)."""
        activity_type = context.get("activity_type", "mood_changer_dog")
        entity = context.get("entity", "object")
        widget = plan.widget_hint or ACTIVITY_WIDGET_MAP.get(activity_type, "character_display")
        arc_animation = EMOTIONAL_ARC_ANIMATION.get(plan.emotional_arc, "gentle_pulse")
        celeb_animation = CELEBRATION_ANIMATION.get(plan.emotional_arc, "badge_reveal")

        frames: list[ScreenFrame] = []

        # Entry frame: photo_display with sparkle
        frames.append(
            ScreenFrame(
                widget="photo_display",
                widget_params={"description": f"Photo of {entity}", "entity": entity},
                animation="sparkle_highlight",
                trigger="on_enter",
                sfx_cue="wonder_chime",
                sfx_label=SFX_LABELS["wonder_chime"],
                animation_label="A gentle sparkle highlights the photo",
                widget_label=f"Your {entity} adventure photo",
            )
        )

        # Per-round frames
        if plan.screen_strategy == "static":
            static_frame = ScreenFrame(
                widget=widget,
                widget_params={"description": f"{entity} activity scene", "entity": entity},
                animation=arc_animation,
                trigger="on_round_1",
                sfx_cue="game_start_chime",
                sfx_label=SFX_LABELS["game_start_chime"],
                animation_label=f"The {entity} scene comes alive",
                widget_label=f"Imagine with your {entity}",
            )
            frames.append(static_frame)

        elif plan.screen_strategy == "progressive":
            for i in range(1, plan.round_count + 1):
                is_last = i == plan.round_count
                sfx = "celebration_fanfare" if is_last else "slot_fill_chime"
                frames.append(
                    ScreenFrame(
                        widget=widget,
                        widget_params={
                            "filled": i,
                            "total": plan.round_count + 1,
                            "description": f"Collection progress: {i} of {plan.round_count + 1}",
                        },
                        animation="celebration_burst" if is_last else "slot_fill_chime",
                        trigger=f"on_round_{i}",
                        sfx_cue=sfx,
                        sfx_label=SFX_LABELS[sfx],
                        animation_label="Collection complete!" if is_last else f"Item {i} collected",
                        widget_label=f"Collection progress: {i} of {plan.round_count + 1}",
                    )
                )

        else:  # per_round
            for i in range(1, plan.round_count + 1):
                sfx = "scene_woosh" if i > 1 else "game_start_chime"
                frames.append(
                    ScreenFrame(
                        widget=widget,
                        widget_params={
                            "description": f"Scene {i} for {entity} activity",
                            "round_number": i,
                            "entity": entity,
                        },
                        animation="scene_transition" if i > 1 else arc_animation,
                        trigger=f"on_round_{i}",
                        sfx_cue=sfx,
                        sfx_label=SFX_LABELS[sfx],
                        animation_label=f"Scene {i} appears" if i > 1 else f"The {entity} scene comes alive",
                        widget_label=f"Round {i} with your {entity}",
                    )
                )

        # Celebration frame
        key_concepts = context.get("key_concepts", [])
        celebration_frame = ScreenFrame(
            widget="badge_award",
            widget_params={
                "title": context.get("role_title", "Explorer"),
                "concepts": key_concepts,
                "entity": entity,
            },
            animation=celeb_animation,
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label=SFX_LABELS["badge_awarded"],
            animation_label="A shining badge appears",
            widget_label="Your explorer badge",
        )

        logger.debug(f"Visual (fallback): {len(frames)} frames, widget={widget}, strategy={plan.screen_strategy}")

        return VisualComposition(
            screen_frames=frames,
            celebration_frame=celebration_frame,
        )
