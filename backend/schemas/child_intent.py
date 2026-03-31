"""Pydantic schema for unified child intent classification."""

from typing import Literal

from pydantic import BaseModel, Field


class ChildIntentClassification(BaseModel):
    """Result of classifying a child's response before Script Agent generation."""

    intent: Literal["confirm", "decline", "substantive", "off_topic"] = Field(
        description="What the child's response represents"
    )
    # Synthesis extension — only populated during STEP_4_SYNTHESIS
    story_quality: Literal["good", "weak"] | None = Field(
        default=None,
        description="Quality of story attempt — only set when intent is substantive and step is STEP_4_SYNTHESIS",
    )
    is_related_to_collection: bool | None = Field(
        default=None,
        description="Whether the response references collected characters — only set during STEP_4_SYNTHESIS",
    )
