"""Pydantic schema for the Visual Agent output (screen frames and widget layout)."""

from pydantic import BaseModel, Field


class ScreenFrame(BaseModel):
    """A single screen frame specifying a widget, its parameters, and trigger condition."""

    widget: str = Field(description="Widget primitive ID")
    widget_params: dict = Field(default_factory=dict, description="Widget-specific parameters")
    animation: str | None = Field(default=None, description="Animation preset")
    trigger: str = Field(description="on_enter | on_round_N | on_correct")
    sfx_cue: str | None = Field(default=None, description="Sound effect ID")
    sfx_label: str | None = Field(default=None, description="Human-readable SFX description")
    animation_label: str | None = Field(default=None, description="Human-readable animation description")
    widget_label: str | None = Field(default=None, description="Human-readable widget description")


class VisualComposition(BaseModel):
    """Visual Agent output: ordered sequence of screen frames for an activity session."""

    screen_frames: list[ScreenFrame] = Field(description="Ordered screen frames for the activity")
    celebration_frame: ScreenFrame | None = Field(
        default=None, description="Special frame shown on activity completion"
    )
