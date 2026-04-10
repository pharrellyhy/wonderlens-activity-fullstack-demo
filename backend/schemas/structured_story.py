"""Pydantic schema for structured scene-by-scene story output."""

from pydantic import BaseModel, Field


class StoryScene(BaseModel):
    """A single scene in the structured story."""

    narration: str = Field(description="The narration text for this scene (2-5 sentences)")
    image_description: str = Field(description="Visual description for Imagen generation")
    image_data_url: str | None = Field(default=None, description="Base64 data URL of generated image")


class StructuredStory(BaseModel):
    """A complete structured story with scenes and achievement image.

    Scene count varies by synthesis format:
    - collaborative_story: 3 story scenes (beginning, middle, end)
    - comparison_reveal: 1 reveal scene (items shown side by side)
    """

    scenes: list[StoryScene] = Field(description="Story scenes (3 for story, 1 for comparison reveal)")
    achievement_description: str = Field(description="Visual description for achievement summary image")
    achievement_image_data_url: str | None = Field(default=None, description="Base64 data URL of achievement image")
