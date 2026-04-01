"""Tests for emotion_tag → character_state mapping."""

import pytest
from server import _map_character_state


class TestMapCharacterState:
    """Verify deterministic mapping from emotion_tag + response_type to character animation state."""

    @pytest.mark.parametrize(
        "tone_marker,expected",
        [
            ("excited", "excited"),
            ("celebrating", "excited"),
            ("impressed", "excited"),
            ("joyful", "excited"),
            ("proud", "excited"),
            ("gentle", "encouraging"),
            ("encouraging", "encouraging"),
            ("warm", "encouraging"),
            ("curious", "surprised"),
            ("mysterious", "surprised"),
            ("adventurous", "surprised"),
            ("neutral", "speaking"),
            ("", "speaking"),
        ],
    )
    def test_emotion_tag_mapping(self, tone_marker: str, expected: str) -> None:
        assert _map_character_state(tone_marker, "round") == expected

    @pytest.mark.parametrize(
        "tone_marker,expected",
        [
            ("excited and warm", "excited"),
            ("gentle and curious", "encouraging"),
            ("very impressed", "excited"),
            ("mysteriously curious", "surprised"),
        ],
    )
    def test_compound_tone_markers(self, tone_marker: str, expected: str) -> None:
        assert _map_character_state(tone_marker, "round") == expected

    @pytest.mark.parametrize(
        "response_type,expected",
        [
            ("hook", "waving"),
            ("celebration", "celebrating"),
            ("closing", "waving"),
            ("graceful_exit", "waving"),
        ],
    )
    def test_response_type_overrides_emotion(self, response_type: str, expected: str) -> None:
        assert _map_character_state("excited", response_type) == expected

    def test_unknown_emotion_defaults_to_speaking(self) -> None:
        assert _map_character_state("some_unknown_emotion", "round") == "speaking"

    def test_response_type_takes_precedence(self) -> None:
        assert _map_character_state("gentle", "hook") == "waving"
        assert _map_character_state("celebrating", "closing") == "waving"
