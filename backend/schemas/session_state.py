"""Pydantic schema for server-side session state."""

from typing import Literal, Union

from pydantic import BaseModel, Field

CollectionPhase = Literal["photo", "detail"]

from .creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from .recipe import InstructionRecipe
from .structured_story import StructuredStory
from .turn_directive import StoryElement
from .visual_composition import ScreenFrame


class ConversationTurn(BaseModel):
    """A single exchange in the conversation history."""

    role: Literal["ai", "child"] = Field(description="Who produced this turn")
    text: str = Field(description="The dialogue text")
    step: str = Field(description="State machine step when this turn occurred")
    round_number: int | None = Field(default=None, description="Round number if applicable")


class UpstreamConversationTurn(BaseModel):
    """A prior exchange from the upstream app before deep-link handoff."""

    role: Literal["ai", "child"] = Field(description="Who produced this upstream turn")
    text: str = Field(description="The upstream dialogue text")


class SessionStateModel(BaseModel):
    """Full server-side session state for turn-by-turn generation."""

    session_id: str
    tier: str
    template_type: Literal["cat1", "cat5"]
    activity_type: str
    current_step: str = Field(description="Current state machine step")
    current_round: int = 0
    total_rounds: int = 3
    creative_slots: Union[Cat1CreativeSlots, Cat5CreativeSlots]
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    collected_photos: list[str] = Field(default_factory=list, description="Cat 5 collected photo IDs")
    collection_phase: CollectionPhase = Field(default="photo", description="Cat 5 2-phase loop: photo or detail")
    collected_details: list[str] = Field(default_factory=list, description="Cat 5 detail responses per find")
    collected_names: list[str] = Field(default_factory=list, description="Cat 5 character names per find")
    round_items: list[list[dict]] = Field(default_factory=list, description="Per-round item sets for Cat 5")
    consecutive_wrong: int = 0
    consecutive_silence: int = 0
    detail_exchange_count: int = Field(default=0, description="Cat 5 Phase B exchange counter — reset on phase change")
    turn_count: int = 0
    status: Literal["active", "completed", "exited", "error"] = "active"

    # Visual Agent output
    visual_frames: list[ScreenFrame] = Field(default_factory=list)
    celebration_frame: ScreenFrame | None = None

    # Instruction-based recipe support
    instruction_recipe: InstructionRecipe | None = None
    invitation_decline_count: int = 0
    invitation_accepted: bool = False
    round_advance_pending: bool = False

    # Story synthesis loop state
    synthesis_phase: str = Field(default="invite", description="Story loop phase: invite, evaluate, improve, generate")
    synthesis_prompt_count: int = Field(
        default=0, description="Times child has been asked to try making a story (max 2)"
    )
    synthesis_child_story: str = Field(
        default="", description="Child's story attempt, stored for improvement/expansion"
    )
    synthesis_story_attempts: int = Field(default=0, description="Times child attempted a story")
    synthesis_declines: int = Field(default=0, description="Times child declined to make a story")
    synthesis_silences: int = Field(default=0, description="Times child was silent during synthesis")
    synthesis_unrelated: int = Field(default=0, description="Times child gave an unrelated response")
    synthesis_story_quality: str = Field(
        default="", description="Last story classification quality: good, weak, or empty"
    )
    # Structured scene-by-scene story (used when imagen_enabled)
    structured_story: StructuredStory | None = Field(
        default=None, description="Scene-by-scene story with image data URLs"
    )
    current_scene: int = Field(default=0, description="Current scene being delivered (0=not started, 1-3=delivering)")
    child_intent: str = Field(
        default="", description="Pre-classified intent for the current turn: confirm, decline, substantive, off_topic"
    )

    # Turn Director state (used when turn_director_enabled=True)
    story_elements: list[StoryElement] = Field(
        default_factory=list,
        description="Structured story ingredients harvested during Cat5 collection rounds",
    )
    last_directive_action: str = Field(default="", description="Most recent Turn Director action for debugging/logging")

    # Deep link entry
    deep_linked: bool = False
    upstream_conversation: list[UpstreamConversationTurn] = Field(default_factory=list)

    # Narrator personality for creative diversity
    narrator_personality: str = ""

    # Vision/entity context
    entity_name: str = ""
    entity_attributes: list[str] = Field(default_factory=list)
    entity_category: str = ""
    scene: str = ""
    ib_key_concepts: list[str] = Field(default_factory=list)
    photo_url: str = ""
