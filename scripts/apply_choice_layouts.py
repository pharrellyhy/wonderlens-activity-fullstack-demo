"""Apply passive choice/carousel round layouts to selected cat1 activities.

These activities are conversational (text/voice), so the multi-item layouts are
VISUAL aids only: selection is "none" (no interactive picker). One item per round
is marked selected so it reads as the round's focus among the options.

Usage: python scripts/apply_choice_layouts.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "frontend" / "public" / "activity-assets" / "activity-assets.manifest.json"
SAFE_AREA = {"canvas": 480, "safe": 380, "center": 300}

# activity_id -> beat_id -> (mode, [items], selected_item)
ROUND_PLANS: dict[str, dict[str, tuple[str, list[str], str]]] = {
    "activity_animal_sound_imitation": {
        "round_1": ("carousel", ["rabbit", "cat", "puppy"], "rabbit"),
        "round_2": ("carousel", ["rabbit", "cat", "puppy"], "cat"),
        "round_3": ("carousel", ["rabbit", "cat", "puppy"], "puppy"),
    },
    "activity_recognition_pop_challenge": {
        "round_1": ("choice2", ["apple", "car"], "apple"),
        "round_2": ("choice3", ["apple", "strawberry", "cherries"], "apple"),
        "round_3": ("choice2", ["apple", "basketball"], "apple"),
    },
    "activity_vegetable_sort": {
        "round_1": ("choice3", ["tomato", "broccoli", "carrot"], "tomato"),
        "round_2": ("choice3", ["potato", "cucumber", "carrot"], "potato"),
        "round_3": ("choice3", ["broccoli", "pumpkin", "corn"], "pumpkin"),
    },
}


def _item(activity_id: str, item_id: str, selected: bool) -> dict[str, object]:
    entry: dict[str, object] = {
        "id": item_id,
        "src": f"/activity-assets/{activity_id}/items/{item_id}.png",
        "shape": "circle",
        "label": item_id.replace("_", " ").title(),
    }
    if selected:
        entry["selected"] = True
    return entry


def apply() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    changed = []
    for activity in manifest["activities"]:
        plans = ROUND_PLANS.get(activity["id"])
        if not plans:
            continue
        for beat in activity["beats"]:
            plan = plans.get(beat["id"])
            if not plan:
                continue
            mode, items, selected = plan
            beat["layout"] = {
                "mode": mode,
                "selection": "none",
                "safeArea": dict(SAFE_AREA),
                "background": {"src": beat["src"], "fit": "cover"},
                "items": [_item(activity["id"], item, item == selected) for item in items],
            }
            changed.append(f"{activity['id']}/{beat['id']}={mode}")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("applied:", *changed, sep="\n  ")


if __name__ == "__main__":
    apply()
