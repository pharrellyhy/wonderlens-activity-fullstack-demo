"""Focused tests for the Gemini-based prod game converter."""

import importlib.util
import re
import sys
import types
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPT_PATH = SCRIPTS_DIR / "convert_game.py"
PROD_GAMES_DIR = REPO_ROOT / "backend" / "games"


def _install_pil_stub() -> None:
    pil_module = types.ModuleType("PIL")
    image_module = types.ModuleType("PIL.Image")

    class FakeImage:
        def convert(self, mode: str):
            return self

        def resize(self, size, resampling):
            return self

        def save(self, out_path: Path, image_format: str = "PNG") -> None:
            Path(out_path).write_bytes(b"fake-png")

    image_module.Image = FakeImage
    image_module.Resampling = types.SimpleNamespace(LANCZOS="LANCZOS")
    image_module.open = lambda *args, **kwargs: FakeImage()
    pil_module.Image = image_module
    sys.modules.setdefault("PIL", pil_module)
    sys.modules.setdefault("PIL.Image", image_module)


def _load_convert_game_module():
    _install_pil_stub()
    sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("convert_game", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _extract_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match is not None
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict)
    return data


CONVERT_GAME = _load_convert_game_module()


@pytest.fixture
def sample_cat1_model():
    data = _extract_frontmatter(PROD_GAMES_DIR / "mood_changer_dog.md")
    return CONVERT_GAME.Cat1GameFrontmatter.model_validate(data)


def _record_parse_call(parse_calls: list[Path], path: Path) -> None:
    parse_calls.append(path)


def test_convert_prod_file_creates_parent_dirs_for_custom_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_cat1_model,
) -> None:
    output_path = tmp_path / "nested" / "converted" / "dog_game.md"

    def fake_call_gemini(*args, **kwargs):
        return sample_cat1_model

    parse_calls: list[Path] = []

    def fake_parse_game_file(path: Path) -> None:
        _record_parse_call(parse_calls, path)

    monkeypatch.setattr(CONVERT_GAME, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(CONVERT_GAME, "parse_game_file", fake_parse_game_file, raising=False)

    result = CONVERT_GAME.convert_prod_file(
        PROD_GAMES_DIR / "bicycle_cat1_prod.md",
        output_path=output_path,
        client=object(),
    )

    assert result == output_path
    assert output_path.exists()
    assert parse_calls == [output_path]


def test_convert_prod_file_validates_dry_run_output(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    sample_cat1_model,
) -> None:
    def fake_call_gemini(*args, **kwargs):
        return sample_cat1_model

    parse_calls: list[Path] = []

    def fake_parse_game_file(path: Path) -> None:
        _record_parse_call(parse_calls, path)

    monkeypatch.setattr(CONVERT_GAME, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(CONVERT_GAME, "parse_game_file", fake_parse_game_file, raising=False)

    result = CONVERT_GAME.convert_prod_file(
        PROD_GAMES_DIR / "bicycle_cat1_prod.md",
        output_path=None,
        client=object(),
        dry_run=True,
    )

    captured = capsys.readouterr()

    assert result is None
    assert len(parse_calls) == 1
    assert parse_calls[0].name.endswith(".md")
    assert parse_calls[0].parent != PROD_GAMES_DIR
    assert "activity_type:" in captured.out
