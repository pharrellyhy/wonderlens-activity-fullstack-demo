"""Pydantic schema for the final merged activity recipe."""

from pydantic import BaseModel, Field, model_validator

from .step_instruction import StepInstruction
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


class InstructionRecipe(BaseModel):
    """Instruction-based recipe: goals + constraints per step, not exact dialogue."""

    activity_type: str = Field(description="Activity type identifier")
    step_instructions: StepInstruction = Field(description="Per-step goals and constraints")
    screen_frames: list[ScreenFrame] = Field(description="Ordered screen frames")
    celebration_frame: ScreenFrame | None = Field(default=None, description="Special frame for activity completion")
    metadata: RecipeMetadata = Field(description="Activity metadata")
    photo_features: list[str] = Field(default_factory=list, description="Cat1 visible feature anchors")
    collection_items: dict = Field(default_factory=dict, description="Cat5 item metadata")

    @model_validator(mode="after")
    def validate_instruction_contract(self) -> "InstructionRecipe":
        round_count = len(self.step_instructions.rounds)
        if self.metadata.round_count != round_count:
            raise ValueError(f"metadata.round_count must match the number of step rounds ({round_count})")
        if self.collection_items and self.step_instructions.synthesis is None:
            raise ValueError("Collection recipes must define a synthesis step")
        return self
