"""Tests for deterministic autodesign package import into demo games."""

import shutil
from pathlib import Path

import pytest
import yaml
from autodesign_importer import AutodesignImportError, import_autodesign_package
from game_parser import parse_game_file

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "autodesign_packages"
PINNED_COMMIT = "72b97241b4f3bd235fe23df91f2fb3aa08ce8b47"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    yaml_text = text.split("---", maxsplit=2)[1]
    data = yaml.safe_load(yaml_text)
    assert isinstance(data, dict)
    return data


def _import_output_roots(tmp_path: Path) -> tuple[Path, Path]:
    games_dir = tmp_path / "games"
    assets_dir = tmp_path / "public" / "activity-assets"
    return games_dir, assets_dir


def _package_copy(source_name: str, tmp_path: Path) -> Path:
    source = FIXTURES_DIR / source_name
    destination = tmp_path / source.name
    shutil.copytree(source, destination)
    return destination


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_supported_cat1_package_imports_to_parseable_frontmatter(tmp_path: Path) -> None:
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        FIXTURES_DIR / "valid" / "supported_cat1",
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    assert result.status == "supported"
    assert result.demo_id == "dream_whisperer_cat__cat"
    assert result.game_path == games_dir / "dream_whisperer_cat__cat.md"
    assert result.game_path.exists()
    assert result.asset_readiness == "ready"

    entity_config, recipe = parse_game_file(result.game_path)
    assert entity_config.activity_type == "dream_whisperer_cat__cat"
    assert entity_config.entity_name == "cat"
    assert entity_config.demo_filename == "dream_whisperer_cat__cat.png"
    assert recipe.activity_type == "dream_whisperer_cat__cat"
    assert recipe.step_instructions.synthesis is None

    data = _frontmatter(result.game_path)
    assert data["autodesign"]["source_activity_id"] == "dream_whisperer_cat"
    assert data["autodesign"]["source_commit"] == PINNED_COMMIT
    assert data["demo_support"]["status"] == "supported"
    assert data["entity_binding"]["entity_id"] == "cat"
    assert data["asset_readiness"]["status"] == "ready"
    assert data["asset_manifest"]["assets"]["entity_hero"]["browser_url"].startswith(
        "/activity-assets/dream_whisperer_cat__cat/"
    )
    entity_variant_path = data["asset_manifest"]["assets"]["entity_hero"]["variants"][0]["path"]
    assert entity_variant_path.startswith("activity-assets/dream_whisperer_cat__cat/")
    assert not Path(entity_variant_path).is_absolute()


def test_runtime_ai_instructions_import_to_step_instructions(tmp_path: Path) -> None:
    package_dir = _package_copy("valid/supported_cat1", tmp_path)
    (package_dir / "prod.md").write_text(
        """# Orion Number Reveal

#### Step 1: Choose A Number

**Runtime AI instruction:** Goal: ask the child to choose one number before any constellation image appears. Constraint: T1 max two sentences; offer simple choices and do not show the Orion card yet. Tone: mysterious and warm. Progress evidence: child chooses a number or accepts the modeled number. Branch behavior: handle ideal, unexpected, and no response differently. Frame/source guardrail: number choice comes before reveal and is not a count-the-image task.

#### Step 2: Reveal The Real Orion Card

**Runtime AI instruction:** Goal: display the package-local reference-bound Orion asset after the number choice. Constraint: T1 max two sentences; reveal only asset_id=orion_seven_star_card and do not ask the child to count the stars. Tone: wonder-filled and careful. Progress evidence: child looks at the card or points to a guide star. Branch behavior: handle ideal, unexpected, and no response differently. Frame/source guardrail: preserve verified source layout.

#### Step 3: Tell Orion Background

**Round 1 -- Orion Background Reveal:**

**Runtime AI instruction:** Goal: tell one short background fact after the reveal and connect it to the visible card. Constraint: T1 max two short sentences; include only stable background information. Tone: gentle teacher with wonder. Progress evidence: child listens, repeats Orion, or points to the pattern. Branch behavior: handle ideal, unexpected, and no response differently. Frame/source guardrail: do not replace background information with a counting challenge.

#### Step 4: Celebration

**Runtime AI instruction:** Goal: celebrate that the child chose first and then discovered a real constellation card. Constraint: one or two short sentences; mention the chosen number only as the opener. Tone: proud and wonder-filled. Progress evidence: child acknowledges the number or Orion. Branch behavior: handle ideal, unexpected, and no response differently. Frame/source guardrail: do not convert celebration into counting.

#### Step 5: Closing

**Runtime AI instruction:** Goal: recap the number choice, real Orion reveal, and background fact. Constraint: max two short sentences; no new constellation or counting prompt. Tone: gentle closing. Progress evidence: child says goodbye, Orion, number, or listens quietly. Branch behavior: handle ideal, unexpected, and no response differently. Frame/source guardrail: close with source-faithful Orion context intact.
""",
        encoding="utf-8",
    )
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        package_dir,
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    _, recipe = parse_game_file(result.game_path)
    instructions = recipe.step_instructions

    assert instructions.hook.goal.startswith("ask the child to choose one number")
    assert "do not show the Orion card yet" in instructions.hook.constraint
    assert instructions.transition.goal.startswith("display the package-local reference-bound Orion asset")
    assert instructions.rounds[0].scenario == "Orion Background Reveal"
    assert instructions.rounds[0].goal.startswith("tell one short background fact")
    assert instructions.celebrate.goal.startswith("celebrate that the child chose first")
    assert instructions.closing.goal.startswith("recap the number choice")


def test_supported_cat5_package_imports_catalog_assets(tmp_path: Path) -> None:
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        FIXTURES_DIR / "valid" / "supported_cat5",
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    assert result.status == "supported"
    assert result.demo_id == "fluffy_expedition_dandelion__dandelion"
    assert result.asset_readiness == "ready"

    entity_config, recipe = parse_game_file(result.game_path)
    assert entity_config.activity_type == "fluffy_expedition_dandelion__dandelion"
    assert entity_config.collection_catalog is not None
    assert recipe.step_instructions.synthesis is not None

    correct_ids = {item.id for item in entity_config.collection_catalog.correct}
    distractor_ids = {item.id for item in entity_config.collection_catalog.distractors}
    assert "fuzzy_moss" in correct_ids
    assert "fluffy_seed" not in correct_ids
    assert "smooth_pebble" in distractor_ids

    fuzzy_moss = next(item for item in entity_config.collection_catalog.correct if item.id == "fuzzy_moss")
    assert fuzzy_moss.image == "/activity-assets/fluffy_expedition_dandelion__dandelion/fuzzy_moss__icon_256.png"
    copied_asset = assets_dir / "fluffy_expedition_dandelion__dandelion" / "fuzzy_moss__icon_256.png"
    assert copied_asset.exists()


def test_degraded_package_imports_with_visible_warning_metadata(tmp_path: Path) -> None:
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        FIXTURES_DIR / "valid" / "degraded_cat5_reference_bound",
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    assert result.status == "degraded"
    assert result.game_path.exists()
    data = _frontmatter(result.game_path)
    assert data["demo_support"]["status"] == "degraded"
    assert data["demo_support"]["degraded_reasons"]
    assert data["asset_readiness"]["status"] in {"ready", "partial"}


def test_unsupported_package_is_not_written_as_playable_game(tmp_path: Path) -> None:
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        FIXTURES_DIR / "valid" / "unsupported_sort",
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    assert result.status == "unsupported"
    assert result.game_path is None
    assert result.unsupported_reasons
    assert not list(games_dir.glob("*.md"))


def test_reference_bound_required_asset_without_source_blocks_import(tmp_path: Path) -> None:
    games_dir, assets_dir = _import_output_roots(tmp_path)

    with pytest.raises(AutodesignImportError, match="reference-bound asset"):
        import_autodesign_package(
            FIXTURES_DIR / "invalid" / "reference_bound_missing_source",
            games_dir=games_dir,
            activity_assets_dir=assets_dir,
            source_commit=PINNED_COMMIT,
        )


def test_supported_required_asset_without_file_blocks_import(tmp_path: Path) -> None:
    package_dir = _package_copy("valid/supported_cat1", tmp_path)
    games_dir, assets_dir = _import_output_roots(tmp_path)
    manifest_path = package_dir / "asset_manifest.yaml"
    manifest = _load_yaml_for_test(manifest_path)
    manifest["assets"][0]["variants"][0]["path"] = None
    manifest["assets"][0]["variants"][1]["path"] = None
    _write_yaml(manifest_path, manifest)

    with pytest.raises(AutodesignImportError, match="Missing required assets"):
        import_autodesign_package(
            package_dir,
            games_dir=games_dir,
            activity_assets_dir=assets_dir,
            source_commit=PINNED_COMMIT,
        )


def test_reference_bound_asset_requires_approved_verified_source(tmp_path: Path) -> None:
    package_dir = _package_copy("invalid/reference_bound_missing_source", tmp_path)
    games_dir, assets_dir = _import_output_roots(tmp_path)
    fixture_asset = package_dir / "orion_fixture.png"
    shutil.copyfile(REPO_ROOT / "frontend" / "public" / "icons" / "cat.png", fixture_asset)

    manifest_path = package_dir / "asset_manifest.yaml"
    manifest = _load_yaml_for_test(manifest_path)
    reference_asset = manifest["assets"][0]
    reference_asset["sources"] = [
        {
            "source_type": "unreviewed_web_image",
            "label": "Unreviewed image",
            "uri": "https://example.invalid/random",
            "license": "unknown",
            "verification_status": "unverified",
        }
    ]
    reference_asset["variants"][0]["path"] = "orion_fixture.png"
    _write_yaml(manifest_path, manifest)

    with pytest.raises(AutodesignImportError, match="approved source"):
        import_autodesign_package(
            package_dir,
            games_dir=games_dir,
            activity_assets_dir=assets_dir,
            source_commit=PINNED_COMMIT,
        )


def test_package_without_demo_extensions_is_reported_unsupported(tmp_path: Path) -> None:
    package_dir = _package_copy("valid/supported_cat1", tmp_path)
    (package_dir / "demo_support.yaml").unlink()
    (package_dir / "asset_manifest.yaml").unlink()
    games_dir, assets_dir = _import_output_roots(tmp_path)

    result = import_autodesign_package(
        package_dir,
        games_dir=games_dir,
        activity_assets_dir=assets_dir,
        source_commit=PINNED_COMMIT,
    )

    assert result.status == "unsupported"
    assert result.game_path is None
    assert result.asset_readiness == "blocked"
    assert result.unsupported_reasons == ["Package does not include demo_support.yaml or asset_manifest.yaml."]


def _load_yaml_for_test(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data
