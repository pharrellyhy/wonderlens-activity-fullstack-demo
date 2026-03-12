"""Recipe Assembler — merges Script + Visual outputs, validates, and handles fallback."""

from pathlib import Path

import yaml

try:
    from ..logger import setup_logger
    from ..schemas import (
        ActivityRecipe,
        CompositionPlan,
        RecipeMetadata,
        ScreenFrame,
        VisualComposition,
        VoiceScript,
    )
except ImportError:
    from logger import setup_logger
    from schemas import (
        ActivityRecipe,
        CompositionPlan,
        RecipeMetadata,
        ScreenFrame,
        VisualComposition,
        VoiceScript,
    )

logger = setup_logger(__name__)

_TIER_RULES_PATH = Path(__file__).parent.parent / "tier_rules.yaml"

ALLOWED_SFX: set[str] = {
    "wonder_chime",
    "excitement_rising",
    "photo_shutter_click",
    "slot_fill_chime",
    "mission_accepted",
    "mission_complete_fanfare",
    "celebration_fanfare",
    "badge_awarded",
    "scene_woosh",
    "game_start_chime",
}

_FACTUAL_PATTERNS: list[str] = [
    "how many",
    "what color",
    "do you know",
    "can you count",
    "what type",
    "what kind",
    "how big",
    "what is this",
    "what are these",
]


def _load_tier_rules() -> dict:
    if _TIER_RULES_PATH.exists():
        with open(_TIER_RULES_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_tier_max_rounds(tier: str) -> int:
    rules = _load_tier_rules()
    tier_rules = rules.get("tiers", {}).get(tier, {})
    pathway_rounds = tier_rules.get("pathway_rounds", [2, 5])
    return pathway_rounds[-1] if pathway_rounds else 5


def _get_tier_max_concepts(tier: str) -> int:
    rules = _load_tier_rules()
    tier_rules = rules.get("tiers", {}).get(tier, {})
    return tier_rules.get("max_concept_badges", 2)


class RecipeAssembler:
    """Merges agent outputs into a validated ActivityRecipe."""

    def merge(
        self,
        script: VoiceScript,
        visuals: VisualComposition,
        plan: CompositionPlan,
        context: dict,
    ) -> ActivityRecipe:
        tier = context.get("tier", "T0")
        warnings: list[str] = []

        # Pad if round count != frame count (excluding the first photo_display frame)
        activity_frames = visuals.screen_frames
        round_count = len(script.rounds)
        frame_count = len(activity_frames)

        if round_count + 1 > frame_count:
            # Need more frames — repeat last frame
            last_frame = (
                activity_frames[-1]
                if activity_frames
                else ScreenFrame(widget="character_display", widget_params={}, trigger="on_enter")
            )
            while len(activity_frames) < round_count + 1:
                activity_frames.append(
                    ScreenFrame(
                        widget=last_frame.widget,
                        widget_params=last_frame.widget_params,
                        animation=last_frame.animation,
                        trigger=f"on_round_{len(activity_frames)}",
                    )
                )
            warnings.append(f"Padded frames from {frame_count} to {len(activity_frames)}")

        # Build metadata
        metadata = RecipeMetadata(
            tier=tier,
            ib_theme=context.get("ib_theme", "Who We Are"),
            ib_key_concept=context.get("key_concepts", ["Perspective"])[0]
            if context.get("key_concepts")
            else "Perspective",
            concepts_earned=plan.closing_concept_targets,
            round_count=len(script.rounds),
        )

        recipe = ActivityRecipe(
            activity_type=context.get("activity_type", "unknown"),
            voice_script=script,
            screen_frames=activity_frames,
            celebration_frame=visuals.celebration_frame,
            metadata=metadata,
        )

        # Run validation
        status, validation_warnings = self._validate(recipe, tier)
        warnings.extend(validation_warnings)

        if warnings:
            for w in warnings:
                logger.warning(f"Assembler: {w}")

        return recipe

    def _validate(self, recipe: ActivityRecipe, tier: str) -> tuple[str, list[str]]:
        """Validate the recipe. Returns (status, warnings)."""
        warnings: list[str] = []

        # Check hook rule — no factual questions
        hook = recipe.voice_script.hook_line.lower()
        for pattern in _FACTUAL_PATTERNS:
            if pattern in hook:
                raise ValueError(f"Hook line contains factual question pattern: '{pattern}'")

        # Check if hook ends with '?' after factual phrase
        if "?" in hook:
            # Allow emotional questions, reject factual ones
            sentences = hook.split("?")
            for sentence in sentences[:-1]:
                fragment = sentence.strip().split(".")[-1].strip()
                if any(p in fragment for p in _FACTUAL_PATTERNS):
                    raise ValueError(f"Hook line contains factual question: '{fragment}?'")

        # Round count within tier limits
        max_rounds = _get_tier_max_rounds(tier)
        if len(recipe.voice_script.rounds) > max_rounds:
            recipe.voice_script.rounds = recipe.voice_script.rounds[:max_rounds]
            recipe.metadata.round_count = max_rounds
            warnings.append(f"Truncated rounds to tier max ({max_rounds})")

        # Closing concepts within tier limit
        max_concepts = _get_tier_max_concepts(tier)
        if len(recipe.metadata.concepts_earned) > max_concepts:
            recipe.metadata.concepts_earned = recipe.metadata.concepts_earned[:max_concepts]
            warnings.append(f"Trimmed concepts to tier max ({max_concepts})")

        # Validate SFX cues
        for rnd in recipe.voice_script.rounds:
            if rnd.sfx_cue and rnd.sfx_cue not in ALLOWED_SFX:
                warnings.append(f"Invalid sfx_cue '{rnd.sfx_cue}' set to null")
                rnd.sfx_cue = None

        status = "fixed_warnings" if warnings else "ok"
        return status, warnings
