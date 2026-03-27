"""Focused tests for the Gemini-based entity icon generator."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPT_PATH = SCRIPTS_DIR / "generate_icon.py"


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
    image_module.new = lambda *args, **kwargs: FakeImage()
    pil_module.Image = image_module
    sys.modules.setdefault("PIL", pil_module)
    sys.modules.setdefault("PIL.Image", image_module)


def _load_generate_icon_module():
    _install_pil_stub()
    sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("generate_icon", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GENERATE_ICON = _load_generate_icon_module()


def test_generate_entity_icon_creates_parent_dirs_for_custom_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "nested" / "icons" / "dog.png"
    monkeypatch.setattr(GENERATE_ICON, "_build_description", lambda *args, **kwargs: "A friendly dog")
    monkeypatch.setattr(GENERATE_ICON, "_generate_with_style_ref", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        GENERATE_ICON,
        "save_icon",
        lambda image, out_path: Path(out_path).write_bytes(b"fake-png"),
    )

    result = GENERATE_ICON.generate_entity_icon(
        "dog",
        client=object(),
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.exists()


def test_find_entities_needing_icons_only_returns_missing_non_prod_entities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    games_dir = tmp_path / "games"
    icons_dir = tmp_path / "icons"
    games_dir.mkdir()
    icons_dir.mkdir()

    (games_dir / "alpha.md").write_text(
        "---\nentity_name: alpha\n---\nbody\n",
        encoding="utf-8",
    )
    (games_dir / "beta.md").write_text(
        "---\nentity_name: beta\n---\nbody\n",
        encoding="utf-8",
    )
    (games_dir / "ignored_cat1_prod.md").write_text(
        "---\nentity_name: ignored\n---\nbody\n",
        encoding="utf-8",
    )
    (icons_dir / "beta.png").write_bytes(b"png")

    monkeypatch.setattr(GENERATE_ICON, "GAMES_DIR", games_dir)
    monkeypatch.setattr(GENERATE_ICON, "OUT_DIR", icons_dir)

    entities = GENERATE_ICON._find_entities_needing_icons()

    assert entities == ["alpha"]
