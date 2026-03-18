"""Pydantic schema for instruction-based recipe steps."""

from pydantic import BaseModel, Field, model_validator


class StepGoal(BaseModel):
    """Goal and constraints for a single non-round step (hook, transition, celebrate, etc.)."""

    goal: str = Field(description="What the AI should accomplish in this step")
    constraint: str = Field(description="Tier-appropriate constraints (sentence count, tone, etc.)")
    emotion_tag: str = Field(description="Suggested emotion tag for TTS, e.g. 'excited'")


class RoundInstruction(BaseModel):
    """Goal and constraints for a single round within the activity."""

    round_number: int = Field(description="1-based round number")
    goal: str = Field(description="What the round explores, e.g. 'explore how the dog feels about warm sunshine'")
    scenario: str = Field(description="The scenario presented, e.g. 'warm sunshine on belly'")
    constraint: str = Field(description="Tier-appropriate constraints for this round")
    emotion_tag: str = Field(description="Suggested emotion tag for this round")
    acceptable_themes: list[str] = Field(
        default_factory=list, description="Loose thematic validation for child responses"
    )
    escalation_note: str = Field(default="", description="How this round fits the escalation arc")


class StepInstruction(BaseModel):
    """Complete instruction set for an activity — goals and constraints per step, not exact dialogue."""

    hook: StepGoal = Field(description="Hook step instructions")
    transition: StepGoal = Field(description="Transition / invitation step instructions")
    rounds: list[RoundInstruction] = Field(description="Per-round instructions")
    celebrate: StepGoal = Field(description="Celebration step instructions")
    closing: StepGoal = Field(description="Closing / tomorrow hook instructions")
    synthesis: StepGoal | None = Field(default=None, description="Cat5 synthesis step instructions")
    early_exit: StepGoal = Field(description="Early exit / graceful goodbye instructions")

    @model_validator(mode="after")
    def validate_round_numbers(self) -> "StepInstruction":
        expected_numbers = list(range(1, len(self.rounds) + 1))
        actual_numbers = [round_instruction.round_number for round_instruction in self.rounds]
        if actual_numbers != expected_numbers:
            raise ValueError("Round numbers must be sequential starting at 1")
        return self
