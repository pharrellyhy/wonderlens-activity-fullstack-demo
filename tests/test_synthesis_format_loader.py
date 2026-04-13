"""Tests for the synthesis format loader — parsing, validation, registry caching."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from synthesis_formats.loader import (
    SynthesisFormat,
    _parse_format_file,
    get_format,
    get_format_registry,
)

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "synthesis_formats"
_VALID_FIXTURE = _FIXTURES_DIR / "test_format.md"


class TestParsesValidFixture:
    def test_parses_valid_fixture(self) -> None:
        fmt = _parse_format_file(_VALID_FIXTURE)
        assert isinstance(fmt, SynthesisFormat)
        assert fmt.id == "test_format"
        assert fmt.display_name == "TEST FORMAT — do not use in production"
        assert fmt.scene_count == 2
        assert fmt.scene_aspect_ratio == "4:3"
        assert fmt.achievement_aspect_ratio == "1:1"
        assert fmt.max_tokens == 512
        assert fmt.temperature == 0.5
        assert fmt.min_sentences_total == {"T0": 3, "T1": 5, "T2": 7}
        assert fmt.direction_max_sentences == {"T0": 4, "T1": 6, "T2": 8}
        assert fmt.direction_tier_sentences == {"T0": "2-4", "T1": "4-6", "T2": "6-8"}
        assert fmt.is_naming_game is True
        assert fmt.confirm_goes_to == "child_try"
        assert fmt.supports_delegation is False
        assert len(fmt.invite_templates) == 2
        assert fmt.invite_direction == "TEST INVITE DIRECTION — do not use in production"
        assert "TEST SYSTEM PROMPT" in fmt.system_prompt
        assert "TEST USER PROMPT" in fmt.user_prompt
        assert "TEST DIRECTION TEMPLATE" in fmt.direction_template


class TestMissingFrontmatterRaises:
    def test_missing_frontmatter_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "no_frontmatter.md"
        bad_file.write_text("# system_prompt\nSome content\n", encoding="utf-8")
        with pytest.raises(ValueError, match="frontmatter"):
            _parse_format_file(bad_file)


class TestMissingRequiredSectionRaises:
    def test_missing_required_section_raises(self, tmp_path: Path) -> None:
        content = """\
---
id: partial_format
display_name: Partial
scene_count: 1
min_sentences_total:
  T0: 3
  T1: 5
  T2: 7
direction_max_sentences:
  T0: 4
  T1: 6
  T2: 8
direction_tier_sentences:
  T0: "2-4"
  T1: "4-6"
  T2: "6-8"
invite_templates:
  - "[gentle] hello"
invite_direction: "some direction"
---

# system_prompt

Some system prompt.

# direction_template

Some direction template.
"""
        partial_file = tmp_path / "partial_format.md"
        partial_file.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="user_prompt"):
            _parse_format_file(partial_file)


class TestInvalidConfirmGoesToRaises:
    def test_invalid_confirm_goes_to_raises(self, tmp_path: Path) -> None:
        content = """\
---
id: bad_confirm
display_name: Bad Confirm
scene_count: 1
confirm_goes_to: bogus
min_sentences_total:
  T0: 3
  T1: 5
  T2: 7
direction_max_sentences:
  T0: 4
  T1: 6
  T2: 8
direction_tier_sentences:
  T0: "2-4"
  T1: "4-6"
  T2: "6-8"
invite_templates:
  - "[gentle] hello"
invite_direction: "some direction"
---

# system_prompt

Some system prompt.

# user_prompt

Some user prompt.

# direction_template

Some direction template.
"""
        bad_file = tmp_path / "bad_confirm.md"
        bad_file.write_text(content, encoding="utf-8")
        with pytest.raises(ValidationError):
            _parse_format_file(bad_file)


class TestGetFormatUnknownRaises:
    def test_get_format_unknown_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Patch the registry to return an empty dict so we can control the test
        # without depending on real format files being present.
        monkeypatch.setattr(
            "synthesis_formats.loader.get_format_registry",
            lambda: {},
        )
        with pytest.raises(ValueError, match="nonexistent"):
            get_format("nonexistent")


class TestRegistryIsCached:
    def test_registry_is_cached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Patch load_all_formats to return a controlled dict and count calls.
        call_count = {"n": 0}

        def _fake_load() -> dict[str, SynthesisFormat]:
            call_count["n"] += 1
            return {}

        # Clear the lru_cache so our patch takes effect cleanly.
        get_format_registry.cache_clear()
        monkeypatch.setattr("synthesis_formats.loader.load_all_formats", _fake_load)

        try:
            first = get_format_registry()
            second = get_format_registry()
            assert first is second, "Registry should be the same mapping instance on both calls"
            assert call_count["n"] == 1, "load_all_formats should be called exactly once"
        finally:
            # Restore cache state so other tests are unaffected.
            get_format_registry.cache_clear()


class TestRegistryIsReadOnly:
    def test_registry_mapping_rejects_mutation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The registry is exposed as a MappingProxyType so external callers
        # cannot corrupt the shared cached dict.
        get_format_registry.cache_clear()
        monkeypatch.setattr(
            "synthesis_formats.loader.load_all_formats",
            lambda: {},
        )
        try:
            registry = get_format_registry()
            # Cast through Any so the static type checker doesn't reject
            # the deliberate mutation attempt — we want the runtime TypeError
            # that MappingProxyType raises.
            mutable_view: Any = registry
            with pytest.raises(TypeError):
                mutable_view["injected"] = "oops"
        finally:
            get_format_registry.cache_clear()


class TestCRLFLineEndingsParse:
    def test_crlf_file_parses_cleanly(self, tmp_path: Path) -> None:
        # A format file saved with Windows-style line endings must still parse.
        content = (
            "---\r\n"
            "id: crlf_format\r\n"
            "display_name: CRLF format\r\n"
            "scene_count: 1\r\n"
            "min_sentences_total:\r\n"
            "  T0: 3\r\n"
            "  T1: 5\r\n"
            "  T2: 7\r\n"
            "direction_max_sentences:\r\n"
            "  T0: 4\r\n"
            "  T1: 6\r\n"
            "  T2: 8\r\n"
            "direction_tier_sentences:\r\n"
            '  T0: "2-4"\r\n'
            '  T1: "4-6"\r\n'
            '  T2: "6-8"\r\n'
            "invite_templates:\r\n"
            '  - "[gentle] hello"\r\n'
            'invite_direction: "some direction"\r\n'
            "---\r\n"
            "\r\n"
            "# system_prompt\r\n"
            "CRLF system prompt body\r\n"
            "\r\n"
            "# user_prompt\r\n"
            "CRLF user prompt body\r\n"
            "\r\n"
            "# direction_template\r\n"
            "CRLF direction template body\r\n"
        )
        crlf_file = tmp_path / "crlf_format.md"
        crlf_file.write_bytes(content.encode("utf-8"))
        fmt = _parse_format_file(crlf_file)
        assert fmt.id == "crlf_format"
        assert fmt.system_prompt == "CRLF system prompt body"
        assert fmt.user_prompt == "CRLF user prompt body"
        assert fmt.direction_template == "CRLF direction template body"


class TestRealRegistryLoadsCollaborativeStory:
    def test_collaborative_story_registered(self) -> None:
        get_format_registry.cache_clear()
        try:
            fmt = get_format("collaborative_story")
            assert fmt.id == "collaborative_story"
            assert fmt.scene_count == 3
            assert fmt.is_naming_game is True
            assert fmt.confirm_goes_to == "child_try"
            assert fmt.min_sentences_total == {"T0": 7, "T1": 9, "T2": 12}
        finally:
            get_format_registry.cache_clear()


class TestRealRegistryLoadsComparisonReveal:
    def test_comparison_reveal_registered(self) -> None:
        get_format_registry.cache_clear()
        try:
            fmt = get_format("comparison_reveal")
            assert fmt.id == "comparison_reveal"
            assert fmt.scene_count == 1
            assert fmt.is_naming_game is False
            assert fmt.confirm_goes_to == "generate"
            assert fmt.min_sentences_total == {"T0": 3, "T1": 3, "T2": 3}
        finally:
            get_format_registry.cache_clear()


class TestRealRegistryLoadsSortingChallenge:
    def test_sorting_challenge_registered(self) -> None:
        # Phase 6 proof: adding a new format is a markdown-only change.
        # This test exists to confirm the new format file is picked up by
        # the registry and that all prompt/direction sections render with
        # the existing template variable vocabulary — no Python edits needed.
        get_format_registry.cache_clear()
        try:
            fmt = get_format("sorting_challenge")
            assert fmt.id == "sorting_challenge"
            assert fmt.scene_count == 1
            assert fmt.is_naming_game is False
            assert fmt.confirm_goes_to == "generate"
            assert "lineup" in fmt.system_prompt.lower() or "order" in fmt.system_prompt.lower()
        finally:
            get_format_registry.cache_clear()


class TestStoryScaffoldValidatesFormat:
    def test_unknown_synthesis_format_raises_at_scaffold_creation(self) -> None:
        # StoryScaffold has a field_validator that calls get_format(); an
        # unknown id must fail fast at model validation time rather than
        # surfacing silently at synthesis time.
        from schemas.creative_slots import StoryScaffold

        get_format_registry.cache_clear()
        with pytest.raises(ValidationError, match="nonexistent_format"):
            StoryScaffold(
                premise="test",
                harvest_per_round="test",
                harvest_question_strategy="test",
                synthesis_goal="test",
                synthesis_format="nonexistent_format",
            )

    def test_known_synthesis_format_passes(self) -> None:
        # Sanity check: the registered formats must still build cleanly.
        from schemas.creative_slots import StoryScaffold

        get_format_registry.cache_clear()
        scaffold = StoryScaffold(
            premise="test",
            harvest_per_round="test",
            harvest_question_strategy="test",
            synthesis_goal="test",
            synthesis_format="collaborative_story",
        )
        assert scaffold.synthesis_format == "collaborative_story"


class TestEmptySectionRejected:
    def test_empty_section_body_raises(self, tmp_path: Path) -> None:
        # A format file with a required section heading but an empty body
        # must fail validation — otherwise the synthesis generator would silently
        # run with an empty prompt string.
        content = """\
---
id: empty_body
display_name: Empty body
scene_count: 1
min_sentences_total:
  T0: 3
  T1: 5
  T2: 7
direction_max_sentences:
  T0: 4
  T1: 6
  T2: 8
direction_tier_sentences:
  T0: "2-4"
  T1: "4-6"
  T2: "6-8"
invite_templates:
  - "[gentle] hello"
invite_direction: "some direction"
---

# system_prompt

# user_prompt
Present user prompt.

# direction_template
Present direction template.
"""
        empty_file = tmp_path / "empty_body.md"
        empty_file.write_text(content, encoding="utf-8")
        with pytest.raises(ValidationError):
            _parse_format_file(empty_file)
