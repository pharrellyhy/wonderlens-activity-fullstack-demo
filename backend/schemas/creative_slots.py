"""Pydantic schemas for Director Agent creative slot outputs."""

from typing import Literal, Union

from pydantic import BaseModel, Field, field_validator

try:
    from ..synthesis_formats import get_format
except ImportError:
    from synthesis_formats import get_format


class StoryScaffold(BaseModel):
    """Defines the narrative arc connecting Cat5 collection rounds to synthesis.

    The Turn Director reads this scaffold to decide what story ingredient to
    harvest each round and how to vary detail questions so they build toward
    a coherent synthesis story.
    """

    premise: str = Field(
        description="Narrative conceit tying all finds together, "
        "e.g. 'Each fluffy find becomes a character with a talent based on how it feels'"
    )
    harvest_per_round: str = Field(
        description="What story ingredient to extract each round: "
        "character_talent, comparison_observation, sound_label, etc."
    )
    harvest_question_strategy: str = Field(
        description="How to vary the detail question across rounds, "
        "e.g. 'R1: direct texture question; R2: compare to previous; R3: group role'"
    )
    synthesis_goal: str = Field(
        description="What synthesis should accomplish, e.g. 'Characters combine their talents on a shared adventure'"
    )
    synthesis_format: str = Field(
        description="Structural format id — must be registered in backend/synthesis_formats/*.md",
    )
    story_themes: list[str] = Field(
        default_factory=list,
        description="Optional theme seeds for story generation, "
        "e.g. 'One friend can't sleep, the others use their talents to help'",
    )

    @field_validator("synthesis_format")
    @classmethod
    def _validate_format_registered(cls, value: str) -> str:
        """Fail fast at scaffold creation time if the format id is unknown.

        ``get_format`` raises ``ValueError`` naming the registered ids, so
        typos and missing format files are surfaced at session start rather
        than silently at synthesis time.
        """
        get_format(value)
        return value


class Cat1CreativeSlots(BaseModel):
    """Creative slots for Category 1 (In-Device Verbal) activities."""

    game_mechanic: Literal[
        "mood_guessing",
        "true_or_silly",
        "voice_acting",
        "storytelling_chain",
        "riddle_game",
        "sound_imitation",
        "prediction_game",
        "helper_hotline",
        "deduce",
        "motion_voice",
        "remember",
        "care",
        "enumerate",
        "decide",
        "sort",
        "predict",
        "imagine",
        "compare",
    ] = Field(description="Game mechanic chosen based on entity category")
    metaphor: str = Field(description="Playful imaginative frame for the entity")
    role_title: str = Field(description="Fun title awarded to the child at the end")
    round_scenarios: list[str] = Field(description="One scenario per dialogue round, escalating in complexity")
    escalation_axis: str = Field(description="How rounds increase in difficulty")
    observation_detail: str = Field(description="Specific visual detail from the photo to anchor the hook")


class Cat3CreativeSlots(BaseModel):
    """Creative slots for Category 3 guided build activities."""

    game_mechanic: Literal["build"] = Field(description="Guided build mechanic")
    metaphor: str = Field(description="Playful frame for the build")
    role_title: str = Field(description="Fun title awarded to the child")
    build_materials: list[str] = Field(default_factory=list, description="Suggested child materials")
    build_steps: list[str] = Field(description="One build step per round")
    escalation_axis: str = Field(description="How build rounds increase in complexity")
    observation_detail: str = Field(description="Specific visual or thematic detail that anchors the hook")


class Cat5CreativeSlots(BaseModel):
    """Creative slots for Category 5 (Out-of-Device Collection) activities."""

    observation_angle: Literal[
        "color", "shape", "texture", "size", "pattern", "function", "habitat", "form", "movement", "smell"
    ] = Field(description="Visual/sensory feature to anchor the collection mission")
    collection_criterion: str = Field(description="Specific rule for what to collect")
    collection_count: int = Field(ge=2, le=4, description="Number of items to find (T0=2, T1=3, T2=3-4)")
    mission_metaphor: str = Field(description="Playful frame for the collection mission")
    role_title: str = Field(description="Fun title awarded at the end")
    synthesis_type: Literal["naming_story", "comparison_chart", "creative_narrative", "sorting_game"] = Field(
        default="naming_story",
        description="Legacy field — synthesis now always uses the story loop regardless of this value",
    )
    stuck_hint: str = Field(description="Hint for where to look if the child is stuck")
    naming_prompt: str = Field(description="Prompt for child to name/characterize each collected item")
    detail_question_template: str = Field(default="", description="Detail-harvesting question template for each find")
    sorting_criterion: str = Field(default="", description="For comparison_chart: criterion to sort by in synthesis")

    # Turn Director story scaffold (optional — when present, drives story-first collection)
    story_scaffold: StoryScaffold | None = Field(
        default=None,
        description="Narrative scaffold for story-first collection — when set, the Turn Director "
        "uses it to vary detail questions per round and feed harvested elements into synthesis",
    )


CreativeSlots = Union[Cat1CreativeSlots, Cat3CreativeSlots, Cat5CreativeSlots]
