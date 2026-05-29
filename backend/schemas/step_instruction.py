"""Pydantic schema for instruction-based recipe steps."""

from pydantic import BaseModel, Field, model_validator


class SourceBranchSet(BaseModel):
    """Source-package response or follow-up branches for one runtime beat."""

    ideal: str = Field(default="", description="Expected on-task branch")
    unexpected: str = Field(default="", description="Off-task or unsupported branch")
    no_response: str = Field(default="", description="Silence/no-response branch")


class SourceStepContract(BaseModel):
    """Dialogue and screen contract imported from an autodesign source package."""

    runtime_instruction: str = Field(default="", description="Source runtime instruction for this beat")
    example_ai_line: str = Field(default="", description="Source example AI line for style and specificity")
    child_responses: SourceBranchSet = Field(default_factory=SourceBranchSet)
    ai_followups: SourceBranchSet = Field(default_factory=SourceBranchSet)
    screen: str = Field(default="", description="Source screen or fallback contract for this beat")


class StepGoal(BaseModel):
    """Goal and constraints for a single non-round step (hook, transition, celebrate, etc.)."""

    goal: str = Field(description="What the AI should accomplish in this step")
    constraint: str = Field(description="Tier-appropriate constraints (sentence count, tone, etc.)")
    emotion_tag: str = Field(description="Suggested emotion tag for TTS, e.g. 'excited'")
    source_contract: SourceStepContract = Field(
        default_factory=SourceStepContract, description="Source-package dialogue fidelity contract"
    )


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
    source_contract: SourceStepContract = Field(
        default_factory=SourceStepContract, description="Source-package dialogue fidelity contract"
    )


class StepInstruction(BaseModel):
    """Complete instruction set for an activity — goals and constraints per step, not exact dialogue."""

    hook: StepGoal = Field(description="Hook step instructions")
    transition: StepGoal = Field(description="Transition / invitation step instructions")
    rounds: list[RoundInstruction] = Field(description="Per-round instructions")
    celebrate: StepGoal = Field(description="Celebration step instructions")
    closing: StepGoal = Field(description="Closing / tomorrow hook instructions")
    synthesis: StepGoal | None = Field(default=None, description="Cat5 synthesis step instructions")
    early_exit: StepGoal = Field(description="Early exit / graceful goodbye instructions")
    source_intent_lock: str = Field(default="", description="Source-package intent lock for this activity")
    runtime_detail_floor_notes: list[str] = Field(
        default_factory=list, description="Source-package runtime detail floor notes"
    )

    @model_validator(mode="after")
    def validate_round_numbers(self) -> "StepInstruction":
        expected_numbers = list(range(1, len(self.rounds) + 1))
        actual_numbers = [round_instruction.round_number for round_instruction in self.rounds]
        if actual_numbers != expected_numbers:
            raise ValueError("Round numbers must be sequential starting at 1")
        return self
