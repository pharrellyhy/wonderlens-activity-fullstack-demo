"""Pydantic schema for classifying a child's response during the story synthesis loop."""

from typing import Literal

from pydantic import BaseModel, Field


class StoryClassification(BaseModel):
    """Result of classifying a child's response in the synthesis step."""

    classification: Literal["story_attempt", "decline", "ask_ai", "unrelated"] = Field(
        description="What the child's response represents"
    )
    is_related_to_collection: bool = Field(description="Whether the response references the collected characters/items")
    story_quality: Literal["good", "weak"] | None = Field(
        default=None,
        description="Quality of the story attempt — only set when classification is story_attempt",
    )
