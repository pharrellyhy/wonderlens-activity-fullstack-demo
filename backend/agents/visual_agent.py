"""Visual Agent — rule-based screen frame composition (no LLM)."""

try:
    from ..logger import setup_logger
    from ..schemas import CompositionPlan, ScreenFrame, VisualComposition
except ImportError:
    from logger import setup_logger
    from schemas import CompositionPlan, ScreenFrame, VisualComposition

logger = setup_logger(__name__)

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


class VisualAgent:
    """Selects screen widgets, assigns assets, and sequences frames using rules."""

    def run(self, plan: CompositionPlan, context: dict) -> VisualComposition:
        activity_type = context.get("activity_type", "mood_changer_dog")
        entity = context.get("entity", "object")
        widget = plan.widget_hint or ACTIVITY_WIDGET_MAP.get(activity_type, "character_display")
        arc_animation = EMOTIONAL_ARC_ANIMATION.get(plan.emotional_arc, "gentle_pulse")
        celeb_animation = CELEBRATION_ANIMATION.get(plan.emotional_arc, "badge_reveal")

        frames: list[ScreenFrame] = []

        # First frame: always photo_display with sparkle_highlight
        frames.append(
            ScreenFrame(
                widget="photo_display",
                widget_params={"description": f"Photo of {entity}", "entity": entity},
                animation="sparkle_highlight",
                trigger="on_enter",
            )
        )

        # Per-round frames based on screen strategy
        if plan.screen_strategy == "static":
            # Single frame reused for all rounds
            static_frame = ScreenFrame(
                widget=widget,
                widget_params={"description": f"{entity} activity scene", "entity": entity},
                animation=arc_animation,
                trigger="on_round_1",
            )
            frames.append(static_frame)

        elif plan.screen_strategy == "progressive":
            # One frame with progressive slot updates
            for i in range(1, plan.round_count + 1):
                frames.append(
                    ScreenFrame(
                        widget=widget,
                        widget_params={
                            "filled": i,
                            "total": plan.round_count + 1,
                            "description": f"Collection progress: {i} of {plan.round_count + 1}",
                        },
                        animation="celebration_burst" if i == plan.round_count else "slot_fill_chime",
                        trigger=f"on_round_{i}",
                    )
                )

        else:  # per_round
            for i in range(1, plan.round_count + 1):
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
        )

        logger.debug(f"Visual: {len(frames)} frames, widget={widget}, strategy={plan.screen_strategy}")

        return VisualComposition(
            screen_frames=frames,
            celebration_frame=celebration_frame,
        )
