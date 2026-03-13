"""Pydantic schema for server-side session state."""

from typing import Literal, Union

from pydantic import BaseModel, Field

from .creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from .visual_composition import ScreenFrame


class ConversationTurn(BaseModel):
    """A single exchange in the conversation history."""

    role: Literal["ai", "child"] = Field(description="Who produced this turn")
    text: str = Field(description="The dialogue text")
    step: str = Field(description="State machine step when this turn occurred")
    round_number: int | None = Field(default=None, description="Round number if applicable")


class SessionStateModel(BaseModel):
    """Full server-side session state for turn-by-turn generation."""

    session_id: str
    tier: str
    template_type: Literal["cat1", "cat5"]
    activity_type: str
    current_step: str = Field(description="Current state machine step")
    current_round: int = 0
    total_rounds: int = 3
    creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots]
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    collected_photos: list[str] = Field(default_factory=list, description="Cat 5 collected photo IDs")
    consecutive_wrong: int = 0
    consecutive_silence: int = 0
    turn_count: int = 0
    status: Literal["active", "completed", "exited", "error"] = "active"

    # Visual Agent output
    visual_frames: list[ScreenFrame] = Field(default_factory=list)
    celebration_frame: ScreenFrame | None = None

    # Vision/entity context
    entity_name: str = ""
    entity_attributes: list[str] = Field(default_factory=list)
    entity_category: str = ""
    scene: str = ""
    ib_key_concepts: list[str] = Field(default_factory=list)
    photo_url: str = ""
