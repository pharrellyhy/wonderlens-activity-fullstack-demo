"""Template state machine for Cat 1 and Cat 5 activity flows.

Determines the next step, whether a step needs user input, and what screen
frame to display for each step.
"""

from typing import Literal, Union

try:
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
except ImportError:
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots

# --- Step Constants ---

# Cat 1 steps
CAT1_STEP_1_HOOK = "STEP_1_HOOK"
CAT1_STEP_2_RULES = "STEP_2_RULES"
CAT1_STEP_3_ROUND = "STEP_3_ROUND"  # Appended with round number at runtime
CAT1_STEP_4_CELEBRATE = "STEP_4_CELEBRATE"
CAT1_STEP_5_CLOSING = "STEP_5_CLOSING"

# Cat 5 steps
CAT5_STEP_1_HOOK = "STEP_1_HOOK"
CAT5_STEP_2_MISSION = "STEP_2_MISSION"
CAT5_STEP_3_COLLECT = "STEP_3_COLLECT"  # Appended with round number at runtime
CAT5_STEP_4_SYNTHESIS = "STEP_4_SYNTHESIS"
CAT5_STEP_5_CELEBRATE = "STEP_5_CELEBRATE"
CAT5_STEP_6_CLOSING = "STEP_6_CLOSING"

# Shared
EARLY_EXIT = "EARLY_EXIT"
ENDED = "ENDED"


def _parse_round_step(step: str) -> tuple[str, int]:
    """Parse 'STEP_3_ROUND_2' into ('STEP_3_ROUND', 2)."""
    for prefix in ("STEP_3_ROUND_", "STEP_3_COLLECT_"):
        if step.startswith(prefix):
            try:
                return prefix.rstrip("_"), int(step[len(prefix) :])
            except ValueError:
                pass
    return step, 0


def next_step(
    current_step: str,
    template_type: Literal["cat1", "cat5"],
    current_round: int,
    total_rounds: int,
) -> str:
    """Determine the next step given current state."""
    if current_step in (ENDED, EARLY_EXIT):
        return ENDED

    if template_type == "cat1":
        return _next_step_cat1(current_step, current_round, total_rounds)
    return _next_step_cat5(current_step, current_round, total_rounds)


def _next_step_cat1(current_step: str, current_round: int, total_rounds: int) -> str:
    if current_step == CAT1_STEP_1_HOOK:
        return CAT1_STEP_2_RULES
    if current_step == CAT1_STEP_2_RULES:
        return "STEP_3_ROUND_1"
    if current_step.startswith("STEP_3_ROUND_"):
        _, rnd = _parse_round_step(current_step)
        if rnd >= total_rounds:
            return CAT1_STEP_4_CELEBRATE
        return f"STEP_3_ROUND_{rnd + 1}"
    if current_step == CAT1_STEP_4_CELEBRATE:
        return CAT1_STEP_5_CLOSING
    if current_step == CAT1_STEP_5_CLOSING:
        return ENDED
    return ENDED


def _next_step_cat5(current_step: str, current_round: int, total_rounds: int) -> str:
    if current_step == CAT5_STEP_1_HOOK:
        return CAT5_STEP_2_MISSION
    if current_step == CAT5_STEP_2_MISSION:
        return "STEP_3_COLLECT_1"
    if current_step.startswith("STEP_3_COLLECT_"):
        _, rnd = _parse_round_step(current_step)
        if rnd >= total_rounds:
            return CAT5_STEP_4_SYNTHESIS
        return f"STEP_3_COLLECT_{rnd + 1}"
    if current_step == CAT5_STEP_4_SYNTHESIS:
        return CAT5_STEP_5_CELEBRATE
    if current_step == CAT5_STEP_5_CELEBRATE:
        return CAT5_STEP_6_CLOSING
    if current_step == CAT5_STEP_6_CLOSING:
        return ENDED
    return ENDED


def is_terminal(step: str) -> bool:
    """Check if a step is terminal (no more turns)."""
    return step == ENDED


def step_needs_user_input(step: str) -> bool:
    """Check if the step requires the child to respond before advancing.

    Round steps (STEP_3_*) and hook/rules/mission need input.
    Celebration and closing auto-advance (frontend sends empty turn).
    """
    if step in (ENDED, EARLY_EXIT):
        return False

    # Auto-advance steps: celebration, closing (NOT synthesis — it needs child interaction)
    auto_advance_steps = {
        CAT1_STEP_4_CELEBRATE,
        CAT1_STEP_5_CLOSING,
        CAT5_STEP_5_CELEBRATE,
        CAT5_STEP_6_CLOSING,
    }
    return step not in auto_advance_steps


def _match_visual_frame(step: str, visual_frames: list[ScreenFrame]) -> ScreenFrame | None:
    """Try to match a Visual Agent frame by mapping step to trigger."""
    if step == "STEP_1_HOOK":
        trigger = "on_enter"
    elif step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        _, rnd = _parse_round_step(step)
        trigger = f"on_round_{rnd}"
    elif step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        trigger = "on_correct"
    else:
        return None

    for frame in visual_frames:
        if frame.trigger == trigger:
            return frame
    return None


def _resolve_cat5_detail_photo_url(context: dict, round_number: int, photo_id: str) -> str:
    """Resolve the collected photo URL for Cat5 detail mode from round items."""
    round_items = context.get("round_items", [])
    round_idx = round_number - 1
    if 0 <= round_idx < len(round_items):
        for item in round_items[round_idx]:
            if item.get("id") == photo_id:
                return item.get("image", "")
    return ""


def _build_cat5_detail_frame(context: dict, entity: str, round_number: int) -> ScreenFrame:
    """Build the Cat5 Phase B frame showing the just-collected photo."""
    collected_photos = context.get("collected_photos", [])
    last_photo = collected_photos[-1] if collected_photos else ""
    return ScreenFrame(
        widget="photo_display",
        widget_params={
            "description": f"Just collected: {last_photo}",
            "entity": entity,
            "photo_id": last_photo,
            "photoUrl": _resolve_cat5_detail_photo_url(context, round_number, last_photo),
        },
        animation="sparkle_highlight",
        trigger=f"on_round_{round_number}",
    )


def _build_cat5_progress_widget_params(
    context: dict, creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots]
) -> dict:
    """Build widget params for Cat5 collection progress."""
    collected_count = len(context.get("collected_photos", []))
    total = creative_slots.collection_count if isinstance(creative_slots, Cat5CreativeSlots) else 3
    return {
        "filled": collected_count,
        "total": total,
        "description": f"Collection progress: {collected_count} of {total}",
    }


def _with_round_context(
    frame: ScreenFrame,
    step: str,
    context: dict,
    creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots],
) -> ScreenFrame:
    """Return a copy of a matched frame enriched with round-specific widget params."""
    if not (step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_")):
        return frame

    _, round_number = _parse_round_step(step)
    frame_copy = frame.model_copy(deep=True)
    frame_copy.widget_params["roundNumber"] = round_number

    if step.startswith("STEP_3_COLLECT_") and frame_copy.widget == "progress_tracker":
        frame_copy.widget_params.update(_build_cat5_progress_widget_params(context, creative_slots))

    return frame_copy


def get_screen_frame(
    step: str,
    template_type: Literal["cat1", "cat5"],
    creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots],
    context: dict,
    visual_frames: list[ScreenFrame] | None = None,
    celebration_frame: ScreenFrame | None = None,
) -> ScreenFrame:
    """Map a step to the appropriate screen frame.

    If visual_frames are provided (from Visual Agent), attempt to match by trigger first.
    For celebrate steps, prefer the dedicated celebration_frame when available.
    Falls back to hardcoded logic if no match is found.
    """
    if celebration_frame and step in {"STEP_4_CELEBRATE", "STEP_5_CELEBRATE"}:
        return celebration_frame

    entity = context.get("entity_name", context.get("entity", "object"))
    key_concepts = context.get("ib_key_concepts", context.get("key_concepts", []))

    if template_type == "cat5" and step.startswith("STEP_3_COLLECT_"):
        _, rnd = _parse_round_step(step)
        collection_phase = context.get("collection_phase", "photo")
        if collection_phase == "detail":
            return _build_cat5_detail_frame(context, entity, rnd)

    # Try matching from Visual Agent frames
    if visual_frames:
        matched = _match_visual_frame(step, visual_frames)
        if matched:
            return _with_round_context(matched, step, context, creative_slots)

    # Hook step: show the photo
    if step == "STEP_1_HOOK":
        return ScreenFrame(
            widget="photo_display",
            widget_params={"description": f"Photo of {entity}", "entity": entity},
            animation="sparkle_highlight",
            trigger="on_enter",
        )

    # Cat 1 specific steps
    if template_type == "cat1":
        if step == "STEP_2_RULES":
            return ScreenFrame(
                widget="character_display",
                widget_params={"description": "Zigzag explains the game", "entity": entity, "roundNumber": 0},
                animation="appear",
                trigger="on_enter",
            )

        if step.startswith("STEP_3_ROUND_"):
            _, rnd = _parse_round_step(step)
            return ScreenFrame(
                widget="character_display",
                widget_params={
                    "description": f"Round {rnd} for {entity} activity",
                    "roundNumber": rnd,
                    "entity": entity,
                },
                animation="scene_transition" if rnd > 1 else "gentle_pulse",
                trigger=f"on_round_{rnd}",
            )

        if step == "STEP_4_CELEBRATE":
            role_title = creative_slots.role_title if isinstance(creative_slots, Cat1CreativeSlots) else "Explorer"
            return ScreenFrame(
                widget="badge_award",
                widget_params={"title": role_title, "concepts": key_concepts, "entity": entity},
                animation="celebration_burst",
                trigger="on_correct",
            )

        if step == "STEP_5_CLOSING":
            return ScreenFrame(
                widget="badge_award",
                widget_params={"title": "IB Concepts", "concepts": key_concepts, "entity": entity},
                animation="badge_reveal",
                trigger="on_correct",
            )

    # Cat 5 specific steps
    if template_type == "cat5":
        if step == "STEP_2_MISSION":
            return ScreenFrame(
                widget="character_display",
                widget_params={
                    "description": "Mission briefing",
                    "entity": entity,
                    "roundNumber": 0,
                },
                animation="appear",
                trigger="on_enter",
            )

        if step.startswith("STEP_3_COLLECT_"):
            _, rnd = _parse_round_step(step)
            progress_params = _build_cat5_progress_widget_params(context, creative_slots)

            return ScreenFrame(
                widget="progress_tracker",
                widget_params=progress_params,
                animation="slot_fill_chime"
                if progress_params["filled"] < progress_params["total"]
                else "celebration_burst",
                trigger=f"on_round_{rnd}",
            )

        if step == "STEP_4_SYNTHESIS":
            return ScreenFrame(
                widget="photo_grid",
                widget_params={"description": "All collected items", "entity": entity},
                animation="sparkle_highlight",
                trigger="on_enter",
            )

        if step == "STEP_5_CELEBRATE":
            role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
            return ScreenFrame(
                widget="badge_award",
                widget_params={"title": role_title, "concepts": key_concepts, "entity": entity},
                animation="celebration_burst",
                trigger="on_correct",
            )

        if step == "STEP_6_CLOSING":
            return ScreenFrame(
                widget="badge_award",
                widget_params={"title": "IB Concepts", "concepts": key_concepts, "entity": entity},
                animation="badge_reveal",
                trigger="on_correct",
            )

    # Early exit / fallback
    if step == EARLY_EXIT:
        return ScreenFrame(
            widget="badge_award",
            widget_params={"title": "Great job!", "concepts": [], "entity": entity},
            animation="badge_reveal",
            trigger="on_correct",
        )

    # Default fallback
    return ScreenFrame(
        widget="photo_display",
        widget_params={"description": f"Photo of {entity}", "entity": entity},
        animation=None,
        trigger="on_enter",
    )


def get_step_name(step: str) -> str:
    """Return a human-readable name for a step (used in prompts)."""
    step_names = {
        "STEP_1_HOOK": "Transition Bridge (Hook)",
        "STEP_2_RULES": "Game Rules Introduction",
        "STEP_2_MISSION": "Mission Briefing",
        "STEP_4_CELEBRATE": "Celebration",
        "STEP_4_SYNTHESIS": "Collection Synthesis",
        "STEP_5_CELEBRATE": "Celebration",
        "STEP_5_CLOSING": "IB Closing",
        "STEP_6_CLOSING": "IB Closing",
        "EARLY_EXIT": "Graceful Exit",
        "ENDED": "Session Ended",
    }
    if step in step_names:
        return step_names[step]
    if step.startswith("STEP_3_ROUND_"):
        _, rnd = _parse_round_step(step)
        return f"Dialogue Round {rnd}"
    if step.startswith("STEP_3_COLLECT_"):
        _, rnd = _parse_round_step(step)
        return f"Collection Round {rnd}"
    return step
