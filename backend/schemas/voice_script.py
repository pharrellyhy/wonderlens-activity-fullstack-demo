"""Pydantic schema for the Script Agent output (voice script with per-round dialogue)."""

from pydantic import BaseModel, Field


class Round(BaseModel):
    """Per-round dialogue with branching paths for correct, incorrect, and silence responses."""

    prompt: str = Field(description="What the AI says to prompt the child")
    correct_responses: list[str] = Field(default_factory=list, description="Acceptable answers (empty for open-ended)")
    on_correct: str = Field(description="Response to a correct answer")
    on_incorrect: str = Field(description="Response to an incorrect answer (encouraging)")
    on_silence: str = Field(description="Response after silence timeout")
    hint: str = Field(description="Help text if the child is stuck")
    sfx_cue: str | None = Field(default=None, description="Sound effect trigger")


class VoiceScript(BaseModel):
    """Script Agent output: all voice/text content for an activity session."""

    hook_line: str = Field(description="Emotional hook (must follow hook rule)")
    transition_line: str = Field(description="Bridge from hook to the main activity")
    rounds: list[Round] = Field(description="Per-round dialogue sequences")
    closing_speech: str = Field(description="Celebration speech incorporating IB concepts")
    tomorrow_hook: str = Field(description="Cross-session retention hook")
