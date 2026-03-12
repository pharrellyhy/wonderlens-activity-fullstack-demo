"""Pydantic schema for the final merged activity recipe."""

from pydantic import BaseModel, Field

from .visual_composition import ScreenFrame
from .voice_script import VoiceScript


class RecipeMetadata(BaseModel):
    """Metadata about the activity session: tier, IB theme, and earned concepts."""

    tier: str = Field(description="Age tier: T0 (2-4) | T1 (4-6) | T2 (6-8)")
    ib_theme: str = Field(description="IB theme for this activity")
    ib_key_concept: str = Field(description="Primary IB concept explored")
    concepts_earned: list[str] = Field(default_factory=list, description="Concepts earned during the activity")
    round_count: int = Field(description="Number of rounds in this activity")


class ActivityRecipe(BaseModel):
    """Final merged recipe combining voice script, visual frames, and metadata."""

    activity_type: str = Field(description="Activity type identifier")
    voice_script: VoiceScript = Field(description="Complete voice/text content")
    screen_frames: list[ScreenFrame] = Field(description="Ordered screen frames")
    celebration_frame: ScreenFrame | None = Field(default=None, description="Special frame for activity completion")
    metadata: RecipeMetadata = Field(description="Activity metadata")
