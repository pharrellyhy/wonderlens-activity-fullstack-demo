"""Tests for the character sounds library — loading, validation, and prompt formatting."""

from character_sounds import (
    get_sound_list_for_prompt,
    load_character_sound_library,
    pick_fallback_cue,
    validate_character_sfx,
)
from schemas.turn_response import CharacterSfxCue


class TestLoadCharacterSoundLibrary:
    def test_loads_all_activities(self) -> None:
        library = load_character_sound_library()
        expected = {
            "mood_changer_dog",
            "dream_whisperer_cat",
            "time_machine_dinosaur",
            "polka_dot_patrol",
            "fluffy_expedition_dandelion",
        }
        assert set(library.keys()) == expected

    def test_each_activity_has_sounds(self) -> None:
        library = load_character_sound_library()
        for activity, sounds in library.items():
            assert len(sounds) > 0, f"{activity} has no sounds"

    def test_sound_entries_have_required_fields(self) -> None:
        library = load_character_sound_library()
        for activity, sounds in library.items():
            for sound in sounds:
                assert "id" in sound, f"Missing id in {activity}"
                assert "category" in sound, f"Missing category in {activity}: {sound}"
                assert "when" in sound, f"Missing when in {activity}: {sound}"

    def test_no_duplicate_ids_per_activity(self) -> None:
        library = load_character_sound_library()
        for activity, sounds in library.items():
            ids = [s["id"] for s in sounds]
            assert len(ids) == len(set(ids)), f"Duplicate sound IDs in {activity}"

    def test_cat1_has_both_character_and_environment(self) -> None:
        library = load_character_sound_library()
        for activity in ["mood_changer_dog", "dream_whisperer_cat", "time_machine_dinosaur"]:
            categories = {s["category"] for s in library[activity]}
            assert "character" in categories, f"{activity} missing character sounds"
            assert "environment" in categories, f"{activity} missing environment sounds"


class TestValidateCharacterSfx:
    def test_character_sound_gets_intro_timing(self) -> None:
        cues = [CharacterSfxCue(cue="dog_bark_happy", timing="overlay")]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert len(result) == 1
        assert result[0].timing == "intro"

    def test_environment_sound_gets_overlay_timing(self) -> None:
        cues = [CharacterSfxCue(cue="env_birds_chirp", timing="intro")]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert len(result) == 1
        assert result[0].timing == "overlay"

    def test_mixed_cues_get_correct_timing(self) -> None:
        cues = [
            CharacterSfxCue(cue="dog_bark_happy", timing="overlay"),
            CharacterSfxCue(cue="env_breeze_gentle", timing="intro"),
        ]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert len(result) == 2
        assert result[0].timing == "intro"  # character → intro
        assert result[1].timing == "overlay"  # environment → overlay

    def test_caps_at_two_cues(self) -> None:
        cues = [
            CharacterSfxCue(cue="dog_bark_happy", timing="intro"),
            CharacterSfxCue(cue="dog_pant_content", timing="intro"),
            CharacterSfxCue(cue="env_birds_chirp", timing="overlay"),
        ]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert len(result) == 2

    def test_invalid_cues_dropped(self) -> None:
        cues = [CharacterSfxCue(cue="hallucinated_sound", timing="overlay")]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert result == []

    def test_cross_activity_cues_rejected(self) -> None:
        cues = [CharacterSfxCue(cue="cat_purr_soft", timing="overlay")]
        result = validate_character_sfx("mood_changer_dog", cues)
        assert result == []

    def test_empty_list_returns_empty(self) -> None:
        result = validate_character_sfx("mood_changer_dog", [])
        assert result == []


class TestPickFallbackCue:
    def test_cat1_returns_ambient_overlay(self) -> None:
        result = pick_fallback_cue("mood_changer_dog")
        assert len(result) == 1
        assert result[0].timing == "overlay"
        assert result[0].cue.startswith("env_")

    def test_cat5_returns_nature_overlay(self) -> None:
        result = pick_fallback_cue("polka_dot_patrol")
        assert len(result) == 1
        assert result[0].timing == "overlay"
        assert result[0].cue.startswith("nature_")

    def test_unknown_activity_returns_empty(self) -> None:
        result = pick_fallback_cue("nonexistent_activity")
        assert result == []

    def test_never_returns_character_sounds(self) -> None:
        for _ in range(20):
            result = pick_fallback_cue("mood_changer_dog")
            for cue in result:
                assert not cue.cue.startswith("dog_"), f"Fallback should not pick character sound: {cue.cue}"


class TestGetSoundListForPrompt:
    def test_returns_formatted_list(self) -> None:
        result = get_sound_list_for_prompt("mood_changer_dog")
        assert "dog_bark_happy" in result
        assert "env_birds_chirp" in result
        assert "use when:" in result

    def test_unknown_activity_returns_message(self) -> None:
        result = get_sound_list_for_prompt("nonexistent_activity")
        assert "No character sounds available" in result

    def test_all_activities_have_prompt_content(self) -> None:
        library = load_character_sound_library()
        for activity in library:
            result = get_sound_list_for_prompt(activity)
            assert len(result) > 0
            assert "No character sounds" not in result
