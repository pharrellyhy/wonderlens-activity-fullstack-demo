"""Pydantic schema for structured scene-by-scene story output."""

from pydantic import BaseModel, Field


class StoryScene(BaseModel):
    """A single scene in the structured story."""

    narration: str = Field(description="The narration text for this scene (2-5 sentences)")
    image_description: str = Field(description="Visual description for Imagen generation")
    image_data_url: str | None = Field(default=None, description="Base64 data URL of generated image")


class StructuredStory(BaseModel):
    """A complete structured story with scenes and achievement image."""

    scenes: list[StoryScene] = Field(description="Exactly 3 story scenes")
    achievement_description: str = Field(description="Visual description for achievement summary image")
    achievement_image_data_url: str | None = Field(default=None, description="Base64 data URL of achievement image")
