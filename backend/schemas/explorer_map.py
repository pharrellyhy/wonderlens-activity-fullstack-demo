"""Pydantic model for Explorer's Map game state.

Defines the state payload that travels inside ScreenFrame.widget_params
when widget == "explorer_map" for Cat 5 activities.
"""

from typing import Literal

from pydantic import BaseModel


class ExplorerMapCharacter(BaseModel):
    """A collected item rendered as a character on the map."""

    id: str
    name: str
    image: str
    zone_index: int


class ExplorerMapState(BaseModel):
    """Game state for the Explorer's Map canvas widget.

    The backend sends the target state; the frontend animates toward it.
    """

    game_phase: Literal[
        "hook",
        "mission",
        "collect_photo",
        "collect_reveal",
        "collect_detail",
        "collect_named",
        "synthesis",
        "celebrate",
        "closing",
    ]
    entity_id: str
    entity_image: str
    revealed_zones: list[int] = []
    characters: list[ExplorerMapCharacter] = []
    active_zone: int | None = None
    total_zones: int = 3
    animation_cue: str | None = None
    collected_count: int = 0
    badge_title: str = ""
    badge_concepts: list[str] = []
