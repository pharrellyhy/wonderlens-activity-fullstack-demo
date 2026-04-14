"""Pydantic schema for structured scene-by-scene story output."""

from pydantic import BaseModel, Field


class StoryScene(BaseModel):
    """A single scene in the structured story."""

    narration: str = Field(description="The narration text for this scene (2-5 sentences)")
    image_description: str = Field(description="Visual description for Imagen generation")
    image_data_url: str | None = Field(default=None, description="Base64 data URL of generated image")
    image_failed: bool = Field(
        default=False,
        description="True when the image generation worker confirmed failure (vs. still in-flight)",
    )
    caption: str | None = Field(
        default=None,
        description="Short (<= 10 word) caption baked into the bottom of the image as hand-lettered text",
    )


class StructuredStory(BaseModel):
    """A complete structured story with scenes and achievement image.

    Scene count varies by synthesis format:
    - collaborative_story: 3 story scenes (beginning, middle, end)
    - comparison_reveal: 1 reveal scene (items shown side by side)
    """

    scenes: list[StoryScene] = Field(description="Story scenes (3 for story, 1 for comparison reveal)")
    # achievement_description is always overwritten post-parse with a
    # deterministic celebration-poster template (see _build_achievement_prompt
    # in turn_handling/synthesis.py). We keep it optional with a default of ""
    # so LLM responses that omit the field — which they will, because the
    # prompt no longer asks for it — validate cleanly.
    achievement_description: str = Field(
        default="",
        description="Visual description for achievement summary image (filled in post-parse)",
    )
    achievement_image_data_url: str | None = Field(default=None, description="Base64 data URL of achievement image")
    achievement_image_failed: bool = Field(
        default=False,
        description="True when the achievement image generation worker confirmed failure",
    )
    achievement_caption: str | None = Field(
        default=None,
        description="Short (<= 6 word) caption baked into the achievement image",
    )
