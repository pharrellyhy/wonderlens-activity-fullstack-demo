"""Runtime asset contract tests for the standalone activity text game."""

import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
MANIFEST_PATH = REPO_ROOT / "frontend" / "public" / "activity-assets" / "activity-assets.manifest.json"
PUBLIC_ROOT = REPO_ROOT / "frontend" / "public"
REPRESENTATIVE_ACTIVITY_IDS = {
    "activity_career_decision_role_play",
    "activity_guided_drawing",
    "activity_phoneme_treasure_hunt",
    "activity_animal_sound_imitation",
    "activity_constellation_star_count",
    "activity_emotion_reader",
    "activity_partial_reveal_guess",
    "activity_recognition_pop_challenge",
    "activity_story_challenge_unlock",
    "activity_travel_planner",
    "activity_vegetable_sort",
    "activity_word_echo_practice",
}

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from activity_catalog import activity_summaries
from entity_registry import generate_round_items, get_collection_catalog
from game_loader import get_demo_recipe


def _manifest_entries() -> dict[str, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in manifest["activities"]}


def _required_beat_ids(activity_id: str, category: str) -> list[str]:
    recipe = get_demo_recipe(activity_id)
    assert recipe is not None

    round_ids = [f"round_{index}" for index in range(1, recipe.metadata.round_count + 1)]
    if activity_id in REPRESENTATIVE_ACTIVITY_IDS:
        tail = ["synthesis", "celebrate", "closing"] if category == "category_5" else ["celebrate", "closing"]
        return ["intro", "rules", *round_ids, *tail]
    if category == "category_5":
        return ["intro", "rules", *round_ids, "synthesis", "recap"]
    return ["intro", "rules", *round_ids, "recap"]


def _public_file_exists(asset_path: str) -> bool:
    return (PUBLIC_ROOT / asset_path.removeprefix("/")).exists()


def _public_path(asset_path: str) -> Path:
    return PUBLIC_ROOT / asset_path.removeprefix("/")


def _layout_asset_paths(layout: dict) -> list[str]:
    paths = []
    background = layout.get("background", {})
    if isinstance(background, dict) and background.get("src"):
        paths.append(background["src"])
    for item in layout.get("items", []):
        if item.get("src"):
            paths.append(item["src"])
    return paths


def _near_black_ratio(image: Image.Image) -> float:
    data = image.convert("RGB").tobytes()
    black_pixels = sum(1 for index in range(0, len(data), 3) if max(data[index : index + 3]) <= 8)
    return black_pixels / (image.width * image.height)


def test_manifest_activity_ids_match_activity_catalog() -> None:
    manifest_ids = set(_manifest_entries())
    catalog_ids = {summary.id for summary in activity_summaries()}

    assert manifest_ids == catalog_ids


def test_activity_asset_manifest_matches_runtime_recipe_beats() -> None:
    manifest_entries = _manifest_entries()

    for summary in activity_summaries():
        entry = manifest_entries[summary.id]
        assert entry["source_export_id"] == summary.source_export_id
        assert [beat["id"] for beat in entry["beats"]] == _required_beat_ids(summary.id, summary.category)
        assert _public_file_exists(entry["icon"]), f"missing icon asset for {summary.id}"
        for beat in entry["beats"]:
            assert _public_file_exists(beat["src"]), f"missing beat asset for {summary.id}: {beat['id']}"
            if summary.id in REPRESENTATIVE_ACTIVITY_IDS:
                assert "layout" in beat, f"missing layout metadata for {summary.id}: {beat['id']}"
            else:
                assert "layout" not in beat, f"pilot layout metadata leaked outside representative scope: {summary.id}"
            for asset_path in _layout_asset_paths(beat.get("layout", {})):
                assert _public_file_exists(asset_path), (
                    f"missing layout asset for {summary.id}: {beat['id']} -> {asset_path}"
                )


def test_cat5_collection_catalog_images_exist() -> None:
    catalog = get_collection_catalog("activity_phoneme_treasure_hunt")
    assert catalog is not None

    items = [*catalog.correct, *catalog.distractors]
    for item in items:
        assert item.image.startswith("/activity-assets/"), f"{item.id} should use activity-specific item art"
        assert _public_file_exists(item.image), f"missing Cat5 collection image: {item.id} -> {item.image}"


def test_activity_assets_do_not_keep_contact_sheet_sources() -> None:
    source_dir = PUBLIC_ROOT / "activity-assets" / "_sources"
    assert not source_dir.exists(), "display assets should be stored as scene/item files, not contact sheets"

    for entry in _manifest_entries().values():
        for beat in entry["beats"]:
            for asset_path in _layout_asset_paths(beat.get("layout", {})):
                assert "/_sources/" not in asset_path


def test_representative_activity_layout_contracts_match_touchless_goal() -> None:
    """Protect the Cat1/Cat3/Cat5 representative layout semantics."""
    manifest_entries = _manifest_entries()

    career = manifest_entries["activity_career_decision_role_play"]
    guided = manifest_entries["activity_guided_drawing"]
    phoneme = manifest_entries["activity_phoneme_treasure_hunt"]

    for entry in (career, guided):
        for beat in entry["beats"]:
            if beat["id"].startswith("round_"):
                layout = beat["layout"]
                assert layout["mode"] == "single"
                assert layout["selection"] == "none"
                assert layout["items"] == []

    for beat in phoneme["beats"]:
        layout = beat["layout"]
        if beat["id"].startswith("round_"):
            assert layout["mode"] == "choice3"
            assert layout["selection"] == "device-scroll"
            assert len(layout["items"]) == 3
        if beat["id"] == "synthesis":
            assert layout["mode"] == "carousel"
            assert layout["selection"] == "none"


def test_phoneme_runtime_round_items_match_approved_touchless_sets() -> None:
    """Keep Cat5 runtime choices aligned with the approved representative screen assets."""
    expected_rounds = [
        ["ball", "cup", "book"],
        ["banana", "spoon", "leaf"],
        ["basket", "toy_car", "sock"],
    ]

    for _index in range(5):
        rounds = generate_round_items("activity_phoneme_treasure_hunt", 3)
        assert [[item["id"] for item in round_items] for round_items in rounds] == expected_rounds

    rounds = generate_round_items("activity_phoneme_treasure_hunt", 3)
    assert [{item["id"] for item in round_items if item["correct"]} for round_items in rounds] == [
        {"ball", "book"},
        {"banana"},
        {"basket"},
    ]


def test_manifest_item_assets_are_sized_and_not_black_padded() -> None:
    item_paths = {
        asset_path
        for entry in _manifest_entries().values()
        for beat in entry["beats"]
        for asset_path in _layout_asset_paths(beat.get("layout", {}))
        if "/items/" in asset_path
    }
    assert item_paths

    for asset_path in sorted(item_paths):
        image_path = _public_path(asset_path)
        with Image.open(image_path) as image:
            assert image.size == (512, 512), f"unexpected item asset size for {asset_path}: {image.size}"
            edge_boxes = [
                (0, 0, image.width, 24),
                (0, image.height - 24, image.width, image.height),
                (0, 0, 24, image.height),
                (image.width - 24, 0, image.width, image.height),
            ]
            edge_black_ratio = max(_near_black_ratio(image.crop(box)) for box in edge_boxes)
            assert edge_black_ratio < 0.25, f"item asset appears black padded: {asset_path}"
