"""Activity catalog helpers for the standalone activity text game."""

from pydantic import BaseModel, Field

try:
    from .entity_registry import ENTITY_REGISTRY, EntityConfig
except ImportError:
    from entity_registry import ENTITY_REGISTRY, EntityConfig


ACTIVITY_TEXT_GAME_SET = "activity_text_game"


class ActivitySummary(BaseModel):
    """Frontend-safe activity metadata."""

    id: str
    kind: str = "activity"
    name: str
    source_export_id: str
    category: str
    mechanic: str
    tier: str
    premise: str
    core_ib_key_concepts: list[str] = Field(default_factory=list)
    asset_manifest_id: str = ""


def is_text_game_activity(entity: EntityConfig) -> bool:
    """Return whether an entity config belongs to the activity text game."""
    return entity.activity_set == ACTIVITY_TEXT_GAME_SET


def activity_summaries() -> list[ActivitySummary]:
    """Return stable activity summaries for the text game frontend."""
    summaries = [
        ActivitySummary(
            id=entity.activity_type,
            name=entity.display_label,
            source_export_id=entity.source_export_id,
            category=entity.category,
            mechanic=entity.mechanic,
            tier=entity.tier,
            premise=entity.plain_description,
            core_ib_key_concepts=entity.concepts_earned,
            asset_manifest_id=entity.activity_type,
        )
        for entity in ENTITY_REGISTRY
        if is_text_game_activity(entity)
    ]
    return sorted(summaries, key=lambda item: item.name)
