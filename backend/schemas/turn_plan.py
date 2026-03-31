"""Pydantic schema for the Planner LLM output - describes WHAT to say, not HOW."""

from pydantic import BaseModel, ConfigDict, Field

from .turn_response import CharacterSfxCue


class TurnPlan(BaseModel):
    """Structured plan for what the AI response should contain.

    The TurnPlan is the output of the Planner pass in the two-pass generation
    architecture. It captures content decisions, constraints, and tone guidance
    that the Speaker pass converts into natural child-facing dialogue.
    """

    model_config = ConfigDict(extra="forbid")

    # What to respond to
    child_said: str = Field(default="", description="Summary of what the child said/did this turn")
    child_emotion: str = Field(
        default="neutral", description="Detected emotion: excited, confused, silent, disengaged, neutral"
    )

    # Content decisions
    celebrate_item: str | None = Field(default=None, description="Item name to celebrate (if correct photo)")
    progress_note: str | None = Field(default=None, description="How to mention progress — varies each round")
    sensory_observation: str | None = Field(
        default=None, description="What YOU notice about the item (how it feels/looks/sounds)"
    )
    name_choices: list[str] = Field(
        default_factory=list, description="2 character name suggestions based on sensory_observation"
    )
    characters_to_reference: list[str] = Field(default_factory=list, description="Previous character names to mention")
    question_type: str | None = Field(
        default=None, description="tactile, visual, comparison, binary_choice, open_guided, none"
    )
    story_beat: str | None = Field(default=None, description="For synthesis: the story content to deliver")

    # Constraints
    must_model_first: bool = Field(default=False, description="T0: must demonstrate before asking")
    offer_binary_choice: bool = Field(default=False, description="T0: offer A or B, not open question")
    do_not_suggest_items: bool = Field(default=True, description="Never name specific items child should find")
    do_not_ask_question: bool = Field(default=False, description="Final find or closing — end with statement")
    stay_on_step: bool = Field(default=False, description="Whether to stay on current step")

    # Tone and format
    emotion_tag: str = Field(default="excited", description="Emotion tag for the response")
    tone_guidance: str = Field(default="", description="Brief tone direction: warm, gentle, celebrating, etc.")
    max_sentences: int = Field(default=2, description="Maximum sentences for the response")

    # Screen/audio (pass-through to TurnResponse)
    screen_widget: str = Field(default="photo_display")
    screen_widget_params: dict = Field(default_factory=dict)
    screen_animation: str | None = Field(default=None)
    sfx_cue: str | None = Field(default=None)
    character_sfx: list[CharacterSfxCue] = Field(
        default_factory=list,
        description="Character/environment sound effects: [{cue, timing}]",
    )
    child_intent: str | None = Field(default=None)
