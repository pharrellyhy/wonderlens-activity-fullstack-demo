"""Tests for scenario loader and matcher."""

from game_loader import get_demo_entities
from scenarios import SCENARIO_CATEGORIES, build_activity_context, load_scenario, match_scenario

get_demo_entities()


class TestMatchScenario:
    def test_direct_match_dog(self) -> None:
        assert match_scenario("dog") == "mood_changer_dog"

    def test_direct_match_ladybug(self) -> None:
        assert match_scenario("ladybug") == "polka_dot_patrol"

    def test_direct_match_dandelion(self) -> None:
        assert match_scenario("dandelion") == "fluffy_expedition_dandelion"

    def test_case_insensitive(self) -> None:
        assert match_scenario("DOG") == "mood_changer_dog"
        assert match_scenario("Ladybug") == "polka_dot_patrol"

    def test_substring_match(self) -> None:
        assert match_scenario("stuffed dog toy") == "mood_changer_dog"

    def test_feature_match_dots(self) -> None:
        assert match_scenario("mystery object", ["spotted", "polka dot pattern"]) in {
            "polka_dot_patrol",
            "circle_spotter_challenge_eye",
        }

    def test_feature_match_fluffy(self) -> None:
        assert match_scenario("mystery object", ["fluffy seed head"]) == "fluffy_expedition_dandelion"

    def test_filename_fallback_matches_keyword(self) -> None:
        assert match_scenario("unknown", [], filename="ladybug.jpg") == "polka_dot_patrol"

    def test_filename_fallback_ignores_short_unrelated_name(self) -> None:
        assert match_scenario("unknown", [], filename="c.jpg") == "mood_changer_dog"

    def test_default_fallback(self) -> None:
        assert match_scenario("random_object_xyz") == "mood_changer_dog"

    def test_dinosaur_match(self) -> None:
        assert match_scenario("dinosaur") == "time_machine_dinosaur"

    def test_cat_match(self) -> None:
        assert match_scenario("cat") == "dream_whisperer_cat"


class TestScenarioCategories:
    def test_category_1_entries(self) -> None:
        for activity in ["mood_changer_dog", "dream_whisperer_cat", "time_machine_dinosaur"]:
            assert SCENARIO_CATEGORIES[activity] == "category_1"

    def test_category_5_entries(self) -> None:
        for activity in ["polka_dot_patrol", "fluffy_expedition_dandelion"]:
            assert SCENARIO_CATEGORIES[activity] == "category_5"


class TestLoadScenario:
    def test_missing_scenario_returns_empty(self) -> None:
        result = load_scenario("nonexistent_scenario_xyz")
        assert result == {}

    def test_load_mood_changer_dog(self) -> None:
        result = load_scenario("mood_changer_dog")
        # May be empty if YAML doesn't exist, but should not raise
        assert isinstance(result, dict)

    def test_load_fluffy_expedition_dandelion(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion")

        assert result["activity_name"] == "The Fluffy Expedition"
        assert result["entity"] == "dandelion"
        assert "Step 4 (Synthesis)" in result["activity_steps_summary"]


class TestLoadDandelionVariants:
    """Verify all dandelion scenario variants load correctly."""

    def test_load_dandelion_decline(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion_decline")
        assert result["entity"] == "dandelion"
        assert result["tier"] == "T0"
        assert any(t["type"] == "unexpected" and t["text"] == "No" for t in result["turns"] if t["role"] == "child")

    def test_load_dandelion_silent(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion_silent")
        assert result["entity"] == "dandelion"
        assert result["tier"] == "T0"
        silent_turns = [t for t in result["turns"] if t["role"] == "child" and t.get("type") == "silent"]
        assert len(silent_turns) >= 2, "Should have at least 2 consecutive silence turns"

    def test_load_dandelion_wrong_photos(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion_wrong_photos")
        assert result["entity"] == "dandelion"
        wrong_turns = [t for t in result["turns"] if "wrong photo" in t.get("text", "")]
        assert len(wrong_turns) >= 2, "Should have at least 2 wrong photo turns"

    def test_load_dandelion_offtopic(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion_offtopic")
        assert result["entity"] == "dandelion"
        # Should have a "you do it" turn for synthesis
        assert any(t.get("text") == "you do it" for t in result["turns"] if t["role"] == "child")

    def test_load_dandelion_t1(self) -> None:
        result = load_scenario("fluffy_expedition_dandelion_t1")
        assert result["entity"] == "dandelion"
        assert result["tier"] == "T1"
        assert result["age_range"] == "4-6"
        # T1 has 2 key concepts
        assert len(result["key_concepts"]) == 2

    def test_all_dandelion_scenarios_share_entity(self) -> None:
        """All dandelion variants should use the same entity."""
        variants = [
            "fluffy_expedition_dandelion",
            "fluffy_expedition_dandelion_decline",
            "fluffy_expedition_dandelion_silent",
            "fluffy_expedition_dandelion_wrong_photos",
            "fluffy_expedition_dandelion_offtopic",
            "fluffy_expedition_dandelion_t1",
        ]
        for variant in variants:
            result = load_scenario(variant)
            assert result.get("entity") == "dandelion", f"{variant} entity mismatch"
            assert result.get("activity_name") == "The Fluffy Expedition", f"{variant} name mismatch"

    def test_dandelion_scenarios_have_valid_turn_structure(self) -> None:
        """All turns should have required fields."""
        variants = [
            "fluffy_expedition_dandelion",
            "fluffy_expedition_dandelion_decline",
            "fluffy_expedition_dandelion_silent",
            "fluffy_expedition_dandelion_wrong_photos",
            "fluffy_expedition_dandelion_offtopic",
            "fluffy_expedition_dandelion_t1",
        ]
        for variant in variants:
            result = load_scenario(variant)
            for turn in result.get("turns", []):
                assert "role" in turn, f"{variant}: turn missing 'role'"
                if turn["role"] == "child":
                    assert "type" in turn, f"{variant}: child turn missing 'type'"
                    assert "text" in turn, f"{variant}: child turn missing 'text'"
                elif turn["role"] == "ai":
                    assert "step" in turn, f"{variant}: ai turn missing 'step'"


class TestBuildActivityContext:
    def test_basic_format(self) -> None:
        scenario = {
            "entity": "dog",
            "activity_name": "Mood Changer",
            "category": "Category 1",
            "scene": "bedroom",
            "visual_features": ["floppy ears"],
            "key_concepts": ["Perspective"],
            "activity_steps_summary": "Explore emotions",
            "detailed_interaction_script": "Round 1: ...",
        }
        vision_result = {"entity": "stuffed dog", "scene": "cozy bedroom"}
        result = build_activity_context(scenario, vision_result)
        assert "stuffed dog" in result
        assert "Mood Changer" in result

    def test_empty_scenario(self) -> None:
        result = build_activity_context({}, {})
        assert isinstance(result, str)
