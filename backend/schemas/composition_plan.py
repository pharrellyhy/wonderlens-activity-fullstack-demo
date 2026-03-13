"""Pydantic schema for the Director Agent output (composition plan)."""

from typing import Literal, Union

from pydantic import BaseModel, Field

from .creative_slots import Cat1CreativeSlots, Cat5CreativeSlots


class CompositionPlan(BaseModel):
    """Director Agent output: high-level creative plan for an activity session."""

    creative_brief: str = Field(description="1-2 sentence creative direction")
    modalities: list[str] = Field(default=["voice", "screen"])
    round_count: int = Field(ge=2, le=5, description="Constrained by tier")
    screen_strategy: str = Field(description="static | per_round | progressive")
    widget_hint: str | None = Field(default=None, description="Primary widget suggestion")
    emotional_arc: str = Field(description="build_excitement | calm_curiosity | playful_surprise | gentle_wonder")
    ib_concept_integration: str = Field(description="How to weave IB concept into the activity")
    closing_concept_targets: list[str] = Field(default_factory=list, description="Related concepts for closing")
    transition_strategy: str = Field(description="natural_question | challenge | imagination_prompt | silly_proposal")
    template_type: Literal["cat1", "cat5"] = Field(default="cat1", description="Template category")
    creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots, None] = Field(
        default=None, description="Creative slots filled by the Director for per-turn Script Agent"
    )
