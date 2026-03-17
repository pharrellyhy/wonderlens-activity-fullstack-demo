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
    tone_marker: str = Field(default="curious", description="Tone for round prompt delivery")
    on_wrong_photo: str | None = Field(default=None, description="Cat5 wrong photo response")


class VoiceScript(BaseModel):
    """Script Agent output: all voice/text content for an activity session."""

    hook_line: str = Field(description="Emotional hook (must follow hook rule)")
    transition_line: str = Field(description="Bridge from hook to the main activity")
    rounds: list[Round] = Field(description="Per-round dialogue sequences")
    closing_speech: str = Field(description="Celebration speech incorporating IB concepts")
    tomorrow_hook: str = Field(description="Cross-session retention hook")
    synthesis_speech: str | None = Field(default=None, description="Cat5 STEP_4_SYNTHESIS dialogue")
    early_exit_speech: str | None = Field(default=None, description="EARLY_EXIT graceful goodbye")
    hook_tone: str = Field(default="excited", description="Tone for hook delivery")
    transition_tone: str = Field(default="playful", description="Tone for transition delivery")
    closing_tone: str = Field(default="proud", description="Tone for closing speech delivery")
    tomorrow_tone: str = Field(default="warm", description="Tone for tomorrow hook delivery")
    synthesis_tone: str = Field(default="amazed", description="Tone for synthesis delivery")
    early_exit_tone: str = Field(default="gentle", description="Tone for early exit delivery")
