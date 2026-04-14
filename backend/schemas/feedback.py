"""Pydantic schemas for tester feedback capture submissions."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FeedbackTag(StrEnum):
    """Closed taxonomy for quick-flag tags used by the tester UI."""

    TONE = "tone"
    CONFUSING = "confusing"
    BUG = "bug"
    LOVED_IT = "loved_it"


class TurnSnapshot(BaseModel):
    """Minimal slice of turn state captured when a flag is created."""

    model_config = ConfigDict(extra="forbid")

    step: str
    speaker_text: str
    child_transcript: str
    widget_type: str
    recipe_round: int


class FeedbackActivity(BaseModel):
    """Activity metadata attached to the session being reviewed."""

    model_config = ConfigDict(extra="forbid")

    template_type: str
    category: str
    photo_filename: str


class FeedbackFlag(BaseModel):
    """A single flagged moment from a tester session."""

    model_config = ConfigDict(extra="forbid")

    flag_id: str
    turn_number: int
    flagged_at: datetime
    tags: list[FeedbackTag]
    quick_note: str
    review_comment: str | None = None
    screenshots: list[str] = Field(default_factory=list)
    turn_snapshot: TurnSnapshot


class FeedbackPayload(BaseModel):
    """Top-level feedback bundle submitted for a single tester session."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    tester_alias: str
    app_mode: str
    activity: FeedbackActivity
    session_started_at: datetime
    session_ended_at: datetime
    flags: list[FeedbackFlag]
