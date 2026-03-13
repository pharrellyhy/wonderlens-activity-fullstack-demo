"""Pydantic schemas for Director Agent creative slot outputs."""

from typing import Literal, Union

from pydantic import BaseModel, Field


class Cat1CreativeSlots(BaseModel):
    """Creative slots for Category 1 (In-Device Verbal) activities."""

    game_mechanic: Literal[
        "mood_guessing",
        "true_or_silly",
        "what_would_it_say",
        "storytelling_chain",
        "riddle_game",
        "sound_imitation",
    ] = Field(description="Game mechanic chosen based on entity category")
    metaphor: str = Field(description="Playful imaginative frame for the entity")
    role_title: str = Field(description="Fun title awarded to the child at the end")
    round_scenarios: list[str] = Field(description="One scenario per dialogue round, escalating in complexity")
    escalation_axis: str = Field(description="How rounds increase in difficulty")
    observation_detail: str = Field(description="Specific visual detail from the photo to anchor the hook")


class Cat5CreativeSlots(BaseModel):
    """Creative slots for Category 5 (Out-of-Device Collection) activities."""

    observation_angle: Literal["color", "shape", "texture", "size", "pattern", "function", "habitat"] = Field(
        description="Visual/sensory feature to anchor the collection mission"
    )
    collection_criterion: str = Field(description="Specific rule for what to collect")
    collection_count: int = Field(ge=2, le=4, description="Number of items to find (T0=2, T1=3, T2=3-4)")
    mission_metaphor: str = Field(description="Playful frame for the collection mission")
    role_title: str = Field(description="Fun title awarded at the end")
    synthesis_type: Literal["naming_story", "comparison_chart", "creative_narrative", "sorting_game"] = Field(
        description="Creative activity for the collected items"
    )
    stuck_hint: str = Field(description="Hint for where to look if the child is stuck")
    naming_prompt: str = Field(description="Prompt for child to name/characterize each collected item")


CreativeSlots = Union[Cat1CreativeSlots, Cat5CreativeSlots]
