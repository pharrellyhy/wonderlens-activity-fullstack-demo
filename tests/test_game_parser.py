"""Tests for game_parser: verify MD files produce correct EntityConfig + InstructionRecipe."""

from pathlib import Path

import game_loader
import pytest
from game_loader import get_demo_entities, get_demo_recipe
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.recipe import InstructionRecipe

GAMES_DIR = Path(__file__).resolve().parents[1] / "backend" / "games"

DEMO_ACTIVITY_TYPES = [
    "mood_changer_dog",
    "dream_whisperer_cat",
    "time_machine_dinosaur",
    "polka_dot_patrol",
    "fluffy_expedition_dandelion",
]


class TestGameLoaderLoadsAll:
    def test_demo_entities_loaded(self) -> None:
        entities = get_demo_entities()
        assert len(entities) >= 5

    def test_all_demo_activity_types_present(self) -> None:
        entities = get_demo_entities()
        loaded_types = {e.activity_type for e in entities}
        assert set(DEMO_ACTIVITY_TYPES).issubset(loaded_types)

    def test_all_recipes_loadable(self) -> None:
        for at in DEMO_ACTIVITY_TYPES:
            recipe = get_demo_recipe(at)
            assert recipe is not None
            assert isinstance(recipe, InstructionRecipe)

    def test_load_demo_games_raises_on_parse_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        bad_game = tmp_path / "broken_game.md"
        bad_game.write_text("---\nactivity_type: broken_game\n---\n")

        monkeypatch.setattr(game_loader, "_GAMES_DIR", tmp_path)
        monkeypatch.setattr(game_loader, "_entity_configs", {})
        monkeypatch.setattr(game_loader, "_instruction_recipes", {})

        def _boom(_: Path) -> tuple[object, object]:
            raise ValueError("broken frontmatter")

        monkeypatch.setattr(game_loader, "parse_game_file", _boom)

        with pytest.raises(RuntimeError, match="broken_game.md"):
            game_loader._load_demo_games()


class TestCat1Entities:
    @pytest.mark.parametrize("activity_type", ["mood_changer_dog", "dream_whisperer_cat", "time_machine_dinosaur"])
    def test_cat1_entity_config(self, activity_type: str) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        entity = entities[activity_type]
        assert entity.category == "category_1"
        assert entity.collection_catalog is None
        assert isinstance(entity.creative_slots, Cat1CreativeSlots)
        assert entity.demo_filename == f"{entity.entity_name}.png"
        assert entity.icon_src == f"/icons/{entity.entity_name}.png"

    def test_dog_creative_slots(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["mood_changer_dog"].creative_slots
        assert isinstance(slots, Cat1CreativeSlots)
        assert slots.game_mechanic == "voice_acting"
        assert slots.role_title == "Emotion Translator"
        assert len(slots.round_scenarios) == 3

    def test_cat_creative_slots(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["dream_whisperer_cat"].creative_slots
        assert isinstance(slots, Cat1CreativeSlots)
        assert slots.game_mechanic == "storytelling_chain"
        assert slots.role_title == "Dream Whisperer"

    def test_dinosaur_creative_slots(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["time_machine_dinosaur"].creative_slots
        assert isinstance(slots, Cat1CreativeSlots)
        assert slots.game_mechanic == "voice_acting"
        assert slots.role_title == "Time Traveler"


class TestCat5Entities:
    @pytest.mark.parametrize("activity_type", ["polka_dot_patrol", "fluffy_expedition_dandelion"])
    def test_cat5_entity_config(self, activity_type: str) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        entity = entities[activity_type]
        assert entity.category == "category_5"
        assert entity.collection_catalog is not None
        assert isinstance(entity.creative_slots, Cat5CreativeSlots)

    def test_ladybug_collection_catalog(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        catalog = entities["polka_dot_patrol"].collection_catalog
        assert catalog is not None
        assert len(catalog.correct) == 4
        assert len(catalog.distractors) == 8
        correct_ids = {item.id for item in catalog.correct}
        assert "spotted_mushroom" in correct_ids

    def test_dandelion_collection_catalog(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        catalog = entities["fluffy_expedition_dandelion"].collection_catalog
        assert catalog is not None
        assert len(catalog.correct) == 4
        assert len(catalog.distractors) == 8

    def test_polka_dot_synthesis_type(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["polka_dot_patrol"].creative_slots
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.synthesis_type == "comparison_chart"

    def test_dandelion_synthesis_type(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["fluffy_expedition_dandelion"].creative_slots
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.synthesis_type == "naming_story"

    def test_polka_dot_detail_question_and_sorting_criterion(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["polka_dot_patrol"].creative_slots
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.detail_question_template != ""
        assert "dots" in slots.detail_question_template.lower() or "different" in slots.detail_question_template.lower()
        assert slots.sorting_criterion != ""

    def test_dandelion_detail_question_template(self) -> None:
        entities = {e.activity_type: e for e in get_demo_entities()}
        slots = entities["fluffy_expedition_dandelion"].creative_slots
        assert isinstance(slots, Cat5CreativeSlots)
        assert slots.detail_question_template != ""
        assert "feel" in slots.detail_question_template.lower()


class TestRecipeStructure:
    @pytest.mark.parametrize("activity_type", DEMO_ACTIVITY_TYPES)
    def test_recipe_has_step_instructions(self, activity_type: str) -> None:
        recipe = get_demo_recipe(activity_type)
        assert recipe is not None
        si = recipe.step_instructions
        assert si.hook.goal
        assert si.transition.goal
        assert len(si.rounds) == 3
        assert si.celebrate.goal
        assert si.closing.goal
        assert si.early_exit.goal

    @pytest.mark.parametrize("activity_type", DEMO_ACTIVITY_TYPES)
    def test_recipe_has_screen_frames(self, activity_type: str) -> None:
        recipe = get_demo_recipe(activity_type)
        assert recipe is not None
        assert len(recipe.screen_frames) == 4
        assert recipe.celebration_frame is not None
        assert recipe.celebration_frame.widget == "badge_award"

    @pytest.mark.parametrize("activity_type", DEMO_ACTIVITY_TYPES)
    def test_metadata_matches_rounds(self, activity_type: str) -> None:
        recipe = get_demo_recipe(activity_type)
        assert recipe is not None
        assert recipe.metadata.round_count == len(recipe.step_instructions.rounds)

    @pytest.mark.parametrize("activity_type", DEMO_ACTIVITY_TYPES)
    def test_photo_features_present(self, activity_type: str) -> None:
        recipe = get_demo_recipe(activity_type)
        assert recipe is not None
        assert len(recipe.photo_features) > 0

    def test_cat5_recipes_have_synthesis(self) -> None:
        for at in ["polka_dot_patrol", "fluffy_expedition_dandelion"]:
            recipe = get_demo_recipe(at)
            assert recipe is not None
            assert recipe.step_instructions.synthesis is not None

    def test_cat1_recipes_have_no_synthesis(self) -> None:
        for at in ["mood_changer_dog", "dream_whisperer_cat", "time_machine_dinosaur"]:
            recipe = get_demo_recipe(at)
            assert recipe is not None
            assert recipe.step_instructions.synthesis is None

    def test_cat5_recipes_have_collection_items(self) -> None:
        for at in ["polka_dot_patrol", "fluffy_expedition_dandelion"]:
            recipe = get_demo_recipe(at)
            assert recipe is not None
            assert "correct" in recipe.collection_items
            assert "distractors" in recipe.collection_items


class TestRecipeMetadataValues:
    def test_dog_metadata(self) -> None:
        recipe = get_demo_recipe("mood_changer_dog")
        assert recipe is not None
        assert recipe.metadata.tier == "T0"
        assert recipe.metadata.ib_theme == "Who We Are"
        assert recipe.metadata.ib_key_concept == "Perspective"
        assert recipe.metadata.concepts_earned == ["Perspective"]

    def test_polka_dot_metadata(self) -> None:
        recipe = get_demo_recipe("polka_dot_patrol")
        assert recipe is not None
        assert recipe.metadata.tier == "T1"
        assert recipe.metadata.ib_theme == "How We Express Ourselves"
        assert recipe.metadata.concepts_earned == ["Form", "Connection"]

    def test_dandelion_metadata(self) -> None:
        recipe = get_demo_recipe("fluffy_expedition_dandelion")
        assert recipe is not None
        assert recipe.metadata.tier == "T0"
        assert recipe.metadata.ib_theme == "Sharing the Planet"
        assert recipe.metadata.concepts_earned == ["Connection"]
