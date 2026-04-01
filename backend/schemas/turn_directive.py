"""Pydantic schemas for the Turn Director output — action-based intent + response strategy.

The Turn Director replaces the separate classifier + planner pipeline when the
turn_director_enabled feature flag is on.  It decides WHAT HAPPENS NEXT (action)
and HOW TO RESPOND (response_direction), which the Speaker then converts into
child-facing dialogue.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .turn_response import CharacterSfxCue


class StoryElement(BaseModel):
    """A single story ingredient harvested during a Cat5 collection round.

    Replaces the flat ``collected_details`` / ``collected_names`` strings with
    structured data that synthesis can weave into a coherent story.
    """

    round_number: int = Field(description="Which collection round produced this element")
    character_name: str | None = Field(default=None, description="Character name assigned to this find")
    trait_or_detail: str | None = Field(
        default=None,
        description="Story-relevant detail: talent, texture comparison, sound label, etc.",
    )
    child_words: str = Field(default="", description="Raw child quote for synthesis weaving")


class TurnDirective(BaseModel):
    """Output of the Turn Director — action-based intent + response strategy.

    Replaces ``ChildIntentClassification`` (what the child said) and ``TurnPlan``
    (what the response should contain) with a single unified decision.
    """

    model_config = ConfigDict(extra="forbid")

    # --- Core decision ---
    action: Literal["advance", "stay", "need_help", "redirect", "exit"] = Field(
        description=(
            "advance: child completed phase objective, move forward. "
            "stay: engaged but objective not met yet. "
            "need_help: stuck/confused/silent, provide scaffolding. "
            "redirect: off-topic but animated, acknowledge and steer back. "
            "exit: consistently disengaged, graceful goodbye."
        )
    )
    reasoning: str = Field(description="1-3 sentences explaining why this action was chosen")
    response_direction: str = Field(
        description=(
            "Strategy for what the speaker should say — specific enough to guide "
            "generation but not final dialogue. E.g., 'celebrate the texture comparison, "
            "name the character Fuzzy, reference Mossy from round 1'"
        )
    )

    # --- Story element (Cat5 collection only) ---
    story_element: StoryElement | None = Field(
        default=None,
        description="Story ingredient harvested this turn — only populated during Cat5 collection detail phase",
    )

    # --- Tone and constraints ---
    emotion_tag: str = Field(default="gentle", description="Emotion tag for the response")
    stay_on_step: bool = Field(default=False, description="Whether to stay on current step")
    max_sentences: int = Field(default=2, description="Maximum sentences for the response")
    must_model_first: bool = Field(default=False, description="T0: must demonstrate before asking")
    offer_binary_choice: bool = Field(default=False, description="T0: offer A or B, not open question")
    do_not_suggest_items: bool = Field(default=True, description="Never name specific items child should find")

    # --- Screen / audio (pass-through to TurnResponse) ---
    screen_widget: str = Field(default="photo_display")
    screen_widget_params: dict = Field(default_factory=dict)
    screen_animation: str | None = Field(default=None)
    sfx_cue: str | None = Field(default=None)
    character_sfx: list[CharacterSfxCue] = Field(
        default_factory=list,
        description="Character/environment sound effects: [{cue, timing}]",
    )
