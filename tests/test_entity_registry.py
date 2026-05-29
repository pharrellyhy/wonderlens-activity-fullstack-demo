"""Tests for the entity registry module."""

import re
from pathlib import Path

import pytest
from agents.script_agent import _load_step_instructions, _load_tier_constraints
from entity_registry import (
    ENTITY_REGISTRY,
    SCENARIO_CATEGORIES,
    all_entities_for_api,
    entity_name_for_filename,
    generate_round_items,
    get_category,
    get_collection_catalog,
    get_creative_slots,
    get_entity,
    get_feature_keyword_map,
    get_keyword_map,
    is_demo_entity,
    keyword_to_activity_type,
    validate_registry,
)
from game_loader import get_demo_entities
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import SessionStateModel


class TestEntityRegistry:
    def test_all_entities_have_required_fields(self) -> None:
        for entity in ENTITY_REGISTRY:
            assert entity.activity_type
            assert entity.category in ("category_1", "category_5")
            assert entity.entity_name
            assert entity.demo_filename
            assert entity.display_label
            assert entity.icon_src
            assert len(entity.keywords) > 0
            assert len(entity.feature_keywords) > 0

    def test_all_loadable_games_are_registered(self) -> None:
        games_dir = Path(__file__).parent.parent / "backend" / "games"
        assert len(ENTITY_REGISTRY) == len(list(games_dir.glob("*.md")))

    def test_cat5_entities_have_collection_catalogs(self) -> None:
        for entity in ENTITY_REGISTRY:
            if entity.category == "category_5":
                assert entity.collection_catalog is not None
                assert len(entity.collection_catalog.correct) > 0
                assert len(entity.collection_catalog.distractors) > 0

    def test_cat1_entities_have_no_collection_catalog(self) -> None:
        for entity in ENTITY_REGISTRY:
            if entity.category == "category_1":
                assert entity.collection_catalog is None


class TestLookupFunctions:
    def test_get_entity(self) -> None:
        entity = get_entity("mood_changer_dog")
        assert entity.entity_name == "dog"
        assert entity.category == "category_1"

    def test_get_entity_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown activity type: nonexistent"):
            get_entity("nonexistent")

    def test_get_creative_slots_cat1(self) -> None:
        slots = get_creative_slots("mood_changer_dog")
        assert isinstance(slots, Cat1CreativeSlots)
        assert slots.game_mechanic == "voice_acting"

    def test_get_creative_slots_cat5(self) -> None:
        slots = get_creative_slots("polka_dot_patrol")
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.observation_angle == "pattern"

    def test_dandelion_synthesis_type_is_naming_story(self) -> None:
        slots = get_creative_slots("fluffy_expedition_dandelion")
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.synthesis_type == "naming_story"

    def test_get_collection_catalog(self) -> None:
        catalog = get_collection_catalog("polka_dot_patrol")
        assert catalog is not None
        assert len(catalog.correct) == 4

    def test_get_collection_catalog_returns_none_for_cat1(self) -> None:
        assert get_collection_catalog("mood_changer_dog") is None

    def test_get_category(self) -> None:
        assert get_category("mood_changer_dog") == "category_1"
        assert get_category("polka_dot_patrol") == "category_5"

    def test_is_demo_entity(self) -> None:
        assert is_demo_entity("dog.png") is True
        assert is_demo_entity("DOG.PNG") is True
        assert is_demo_entity("custom_photo.jpg") is False

    def test_entity_name_for_filename(self) -> None:
        assert entity_name_for_filename("dog.png") == "dog"
        assert entity_name_for_filename("ladybug.png") == "ladybug"
        assert entity_name_for_filename("random.jpg") == "object"

    def test_keyword_to_activity_type(self) -> None:
        assert keyword_to_activity_type("dog") == "mood_changer_dog"
        assert keyword_to_activity_type("ladybug") == "polka_dot_patrol"
        assert keyword_to_activity_type("unknown_thing") is None

    def test_keyword_map_contains_all_keywords(self) -> None:
        keyword_map = get_keyword_map()
        for entity in ENTITY_REGISTRY:
            for kw in entity.keywords:
                assert kw in keyword_map
        for entity in ENTITY_REGISTRY:
            matching_activity_types = {
                candidate.activity_type for candidate in ENTITY_REGISTRY if candidate.entity_name == entity.entity_name
            }
            assert keyword_map[entity.entity_name] in matching_activity_types
        assert keyword_map["cat"] == "dream_whisperer_cat"
        assert keyword_map["dandelion"] == "fluffy_expedition_dandelion"

    def test_feature_keyword_map(self) -> None:
        fkw_map = get_feature_keyword_map()
        assert "spot" in fkw_map
        assert fkw_map["spot"] == "polka_dot_patrol"
        assert "fluffy" in fkw_map
        assert fkw_map["fluffy"] == "fluffy_expedition_dandelion"


class TestScenarioCategories:
    def test_backward_compatible_categories(self) -> None:
        assert SCENARIO_CATEGORIES["mood_changer_dog"] == "category_1"
        assert SCENARIO_CATEGORIES["dream_whisperer_cat"] == "category_1"
        assert SCENARIO_CATEGORIES["time_machine_dinosaur"] == "category_1"
        assert SCENARIO_CATEGORIES["polka_dot_patrol"] == "category_5"
        assert SCENARIO_CATEGORIES["fluffy_expedition_dandelion"] == "category_5"


class TestGenerateRoundItems:
    def test_returns_correct_structure(self) -> None:
        rounds = generate_round_items("polka_dot_patrol", 3)
        assert len(rounds) == 3
        for round_items in rounds:
            assert len(round_items) == 3
            correct_count = sum(1 for item in round_items if item.get("correct"))
            assert correct_count == 1

    def test_returns_empty_for_cat1(self) -> None:
        assert generate_round_items("mood_changer_dog", 3) == []

    def test_returns_empty_for_unknown(self) -> None:
        assert generate_round_items("nonexistent", 3) == []

    def test_items_have_required_fields(self) -> None:
        rounds = generate_round_items("polka_dot_patrol", 2)
        for round_items in rounds:
            for item in round_items:
                assert "id" in item
                assert "label" in item
                assert "image" in item


class TestAllEntitiesForApi:
    def test_returns_two_categories(self) -> None:
        result = all_entities_for_api()
        assert len(result) == 2
        assert result[0]["id"] == "cat1"
        assert result[1]["id"] == "cat5"

    def test_cat1_includes_curated_photos(self) -> None:
        result = all_entities_for_api()
        photo_ids = {photo["id"] for photo in result[0]["photos"]}
        assert {"cat", "dog", "dinosaur", "dream_whisperer_cat__cat"}.issubset(photo_ids)

    def test_cat5_includes_curated_photos(self) -> None:
        result = all_entities_for_api()
        photo_ids = {photo["id"] for photo in result[1]["photos"]}
        assert {
            "concept_phoneme_hunt_collect__ball",
            "dandelion",
            "fluffy_expedition_dandelion__dandelion",
            "ladybug",
        }.issubset(photo_ids)

    def test_photo_structure(self) -> None:
        result = all_entities_for_api()
        for cat in result:
            for photo in cat["photos"]:
                assert "id" in photo
                assert "label" in photo
                assert "src" in photo

    def test_cat1_summary_round_scenarios_match_round_count(self) -> None:
        result = all_entities_for_api()
        photos_by_id = {photo["id"]: photo for category in result for photo in category["photos"]}

        cat_summary = photos_by_id["cat"]["summary"]

        assert cat_summary["round_scenarios"] is not None
        assert len(cat_summary["round_scenarios"]) == cat_summary["round_count"]


class TestStyleFragments:
    """Verify that fragment files exist for all styles referenced by entities."""

    _STEP_INSTRUCTIONS_DIR = Path(__file__).parent.parent / "backend" / "skills" / "step_instructions"

    # Which base templates support fragments, and which slot field selects the style
    _CAT1_FRAGMENT_BASES = ["cat1_step2_rules", "cat1_step3_round"]
    _CAT5_FRAGMENT_BASES = ["cat5_step3_collect", "cat5_step4_synthesis"]

    def _build_state(
        self,
        activity_type: str,
        current_step: str,
        *,
        current_round: int = 1,
        collected_photos: list[str] | None = None,
        collection_phase: str = "photo",
    ) -> SessionStateModel:
        entity = get_entity(activity_type)
        return SessionStateModel(
            session_id="test-session",
            tier="T0",
            template_type="cat1" if entity.category == "category_1" else "cat5",
            activity_type=entity.activity_type,
            current_step=current_step,
            current_round=current_round,
            total_rounds=3,
            creative_slots=entity.creative_slots,
            collected_photos=collected_photos or [],
            collection_phase=collection_phase,
            entity_name=entity.entity_name,
            entity_category=entity.category,
        )

    def test_cat1_fragments_exist_for_registered_mechanics(self) -> None:
        for entity in ENTITY_REGISTRY:
            if entity.category != "category_1":
                continue
            assert isinstance(entity.creative_slots, Cat1CreativeSlots)
            mechanic = entity.creative_slots.game_mechanic
            for base in self._CAT1_FRAGMENT_BASES:
                path = self._STEP_INSTRUCTIONS_DIR / f"{base}__{mechanic}.md"
                assert path.exists(), f"Missing fragment: {path.name} (entity={entity.activity_type})"

    def test_cat5_fragments_exist_for_registered_synthesis_types(self) -> None:
        # Synthesis now uses a single story_generation fragment for all types
        # (the old per-synthesis-type fragments were removed). Verify that the
        # collect fragment still exists per synthesis_type and the unified
        # story_generation fragment exists.
        story_gen_path = self._STEP_INSTRUCTIONS_DIR / "cat5_step4_synthesis__story_generation.md"
        assert story_gen_path.exists(), "Missing unified synthesis fragment: cat5_step4_synthesis__story_generation.md"

        for entity in ENTITY_REGISTRY:
            if entity.category != "category_5":
                continue
            assert isinstance(entity.creative_slots, Cat5CreativeSlots)
            synthesis = entity.creative_slots.synthesis_type
            collect_path = self._STEP_INSTRUCTIONS_DIR / f"cat5_step3_collect__{synthesis}.md"
            assert collect_path.exists(), f"Missing fragment: {collect_path.name} (entity={entity.activity_type})"

    def test_cat1_round_fragment_is_loaded_and_interpolated(self) -> None:
        state = self._build_state(
            "dream_whisperer_cat",
            "STEP_3_ROUND_1",
            current_round=1,
        )

        text = _load_step_instructions(state)

        assert "### Style: Storytelling Chain" in text
        assert "{entity_name}" not in text
        # Examples are now dynamically sampled from YAML, so check for the placeholder resolution
        assert "{sampled_examples}" not in text

    def test_cat5_synthesis_uses_story_generation_fragment(self) -> None:
        state = self._build_state(
            "fluffy_expedition_dandelion",
            "STEP_4_SYNTHESIS",
            collected_photos=["fuzzy_moss", "soft_petal", "fluffy_seed"],
        )
        state.synthesis_phase = "generate"

        text = _load_step_instructions(state)

        assert "### Story Generation" in text
        assert "### OUTPUT FORMAT" in text
        assert "### SCENE STRUCTURE" in text

    def test_cat5_synthesis_filters_inactive_phase_sections(self) -> None:
        state = self._build_state(
            "fluffy_expedition_dandelion",
            "STEP_4_SYNTHESIS",
            collected_photos=["fuzzy_moss", "soft_petal", "fluffy_seed"],
        )
        state.synthesis_phase = "generate"

        text = _load_step_instructions(state)

        assert "### PHASE: GENERATE" in text
        assert "### PHASE: INVITE" not in text
        assert "### PHASE: IMPROVE" not in text

    def test_cat5_mission_prompt_fully_interpolates_example_driven_variables(self) -> None:
        state = self._build_state("fluffy_expedition_dandelion", "STEP_2_MISSION")

        text = _load_step_instructions(state)

        assert "{activity_name}" not in text
        assert "{tier}" not in text
        assert re.search(r"\{[a-z_]+\}", text) is None

    def test_cat5_collect_detail_phase_loads_sampled_examples(self) -> None:
        state = self._build_state(
            "fluffy_expedition_dandelion",
            "STEP_3_COLLECT_2",
            current_round=2,
            collected_photos=["fuzzy_moss"],
            collection_phase="detail",
        )

        text = _load_step_instructions(state)

        # Sampled examples should be resolved (placeholder gone) and contain AI dialogue
        assert "{sampled_examples}" not in text
        assert "AI:" in text

    @pytest.mark.skip(reason="game_examples feature not implemented on Cat5CreativeSlots")
    def test_game_examples_are_interpolated_like_other_template_variables(self) -> None:
        state = self._build_state("fluffy_expedition_dandelion", "STEP_2_MISSION")
        assert isinstance(state.creative_slots, Cat5CreativeSlots)
        state.creative_slots = state.creative_slots.model_copy(
            update={"game_examples": {"mission": {"T0": "Badge: {role_title}"}}}
        )

        text = _load_step_instructions(state)

        assert "Badge: Fluffy Expedition Explorer" in text
        assert "{role_title}" not in text

    def test_tier_constraints_render_readably_for_compact_prompt(self) -> None:
        text = _load_tier_constraints("T0")

        assert "Tier: T0 (Sensory Explorer, ages 2-4)" in text
        assert "Sentences: max 2, ~5-10 words each." in text
        assert "Style: gentle and cute. simple, playful, exclamations" in text


class TestValidateRegistry:
    def test_validate_registry_passes(self) -> None:
        validate_registry()

    def test_validate_registry_requires_non_empty_registry(self) -> None:
        original_entities = list(get_demo_entities())
        try:
            from entity_registry import _populate_registry  # noqa: PLC0415

            _populate_registry([])

            with pytest.raises(ValueError, match="Entity registry is empty"):
                validate_registry()
        finally:
            _populate_registry(original_entities)
