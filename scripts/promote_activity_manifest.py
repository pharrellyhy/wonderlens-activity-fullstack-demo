"""Promote a non-pilot activity's manifest entry to representative single-layout beats.

Rewrites the activity's beats to [intro, rules, round_1..N, celebrate, closing], each a
flat `single` scene layout (background = the beat png) matching the career pilot shape.

Usage: python scripts/promote_activity_manifest.py <activity_id> [round_count]
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "frontend" / "public" / "activity-assets" / "activity-assets.manifest.json"
SAFE_AREA = {"canvas": 480, "safe": 380, "center": 300}
BEAT_USAGE = {
    "intro": "hook",
    "rules": "setup",
    "celebrate": "celebration",
    "closing": "closing",
}


def _beat(activity_id: str, beat_id: str) -> dict:
    src = f"/activity-assets/{activity_id}/{beat_id}.png"
    usage = BEAT_USAGE.get(beat_id, "round")
    return {
        "id": beat_id,
        "src": src,
        "usage": usage,
        "layout": {
            "mode": "single",
            "selection": "none",
            "safeArea": dict(SAFE_AREA),
            "background": {"src": src, "fit": "cover"},
            "items": [],
        },
    }


def promote(activity_id: str, round_count: int) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = next((a for a in manifest["activities"] if a["id"] == activity_id), None)
    if entry is None:
        raise SystemExit(f"activity {activity_id} not found in manifest")

    beat_ids = ["intro", "rules", *[f"round_{index}" for index in range(1, round_count + 1)], "celebrate", "closing"]
    entry["beats"] = [_beat(activity_id, beat_id) for beat_id in beat_ids]

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"promoted {activity_id}: {beat_ids}")


if __name__ == "__main__":
    activity = sys.argv[1]
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    promote(activity, rounds)
