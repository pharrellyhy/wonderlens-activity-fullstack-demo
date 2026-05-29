"""Build reusable WonderLens activity screen item assets and manifest layouts."""

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = REPO_ROOT / "frontend" / "public" / "activity-assets"
MANIFEST_PATH = ASSET_ROOT / "activity-assets.manifest.json"
SAFE_AREA = {"canvas": 480, "safe": 380, "center": 300}


ItemCrop = tuple[str, tuple[int, int, int, int]]


ITEM_CROPS: dict[str, dict[str, ItemCrop]] = {
    "activity_animal_sound_imitation": {
        "rabbit": ("intro.png", (0, 180, 185, 405)),
        "cat": ("intro.png", (155, 165, 355, 390)),
        "puppy": ("intro.png", (320, 175, 512, 405)),
    },
    "activity_constellation_star_count": {
        "stars_4": ("round_1.png", (90, 95, 420, 350)),
        "stars_6": ("round_2.png", (90, 95, 420, 350)),
        "stars_many": ("round_3.png", (90, 95, 420, 350)),
    },
    "activity_emotion_reader": {
        "face": ("round_1.png", (65, 65, 360, 395)),
        "feeling": ("round_2.png", (190, 315, 345, 485)),
        "heart": ("round_3.png", (10, 320, 175, 500)),
        "help": ("round_3.png", (350, 300, 512, 500)),
    },
    "activity_partial_reveal_guess": {
        "ears": ("round_3.png", (120, 115, 370, 315)),
        "paws": ("round_2.png", (135, 160, 350, 330)),
        "cat": ("round_3.png", (105, 130, 395, 405)),
    },
    "activity_recognition_pop_challenge": {
        "apple": ("round_2.png", (0, 185, 185, 390)),
        "car": ("round_1.png", (335, 190, 505, 375)),
        "strawberry": ("round_2.png", (185, 205, 335, 380)),
        "cherries": ("round_2.png", (330, 190, 512, 390)),
        "basketball": ("round_3.png", (350, 190, 512, 380)),
    },
    "activity_story_challenge_unlock": {
        "fox": ("round_2.png", (30, 185, 210, 390)),
        "owl": ("round_2.png", (290, 130, 455, 325)),
        "moon": ("round_3.png", (190, 20, 325, 155)),
        "star": ("round_3.png", (165, 245, 350, 420)),
    },
    "activity_travel_planner": {
        "map": ("round_1.png", (95, 95, 330, 300)),
        "sun": ("round_1.png", (340, 85, 505, 245)),
        "hat": ("round_1.png", (60, 270, 245, 470)),
        "glasses": ("round_1.png", (270, 295, 465, 445)),
        "umbrella": ("round_2.png", (70, 260, 245, 455)),
        "boots": ("round_2.png", (285, 265, 470, 455)),
        "car": ("round_3.png", (15, 240, 240, 430)),
        "gift": ("round_3.png", (335, 210, 500, 380)),
    },
    "activity_vegetable_sort": {
        "tomato": ("round_1.png", (35, 110, 185, 275)),
        "broccoli": ("round_1.png", (185, 105, 330, 275)),
        "carrot": ("round_1.png", (340, 105, 485, 275)),
        "potato": ("round_2.png", (45, 105, 195, 270)),
        "cucumber": ("round_2.png", (190, 105, 330, 270)),
        "pumpkin": ("round_3.png", (190, 105, 330, 270)),
        "corn": ("round_3.png", (335, 100, 500, 275)),
    },
    "activity_word_echo_practice": {
        "word": ("round_1.png", (115, 105, 345, 255)),
        "echo": ("round_2.png", (145, 130, 365, 300)),
        "sound": ("rules.png", (330, 120, 510, 275)),
    },
}


LABELS = {
    "alarm": "Alarm",
    "apple": "Apple",
    "ball": "Ball",
    "banana": "Banana",
    "basket": "Basket",
    "basketball": "Ball",
    "book": "Book",
    "boots": "Boots",
    "broccoli": "Broccoli",
    "car": "Car",
    "carrot": "Carrot",
    "cat": "Cat",
    "cherries": "Cherries",
    "cucumber": "Cucumber",
    "corn": "Corn",
    "cup": "Cup",
    "drawing": "Drawing",
    "ears": "Ears",
    "echo": "Echo",
    "face": "Face",
    "feeling": "Feeling",
    "firefighter": "Helper",
    "fox": "Fox",
    "gift": "Gift",
    "glasses": "Shades",
    "hat": "Hat",
    "heart": "Care",
    "help": "Help",
    "hose": "Hose",
    "leaf": "Leaf",
    "map": "Map",
    "moon": "Moon",
    "oil": "Oil",
    "outside": "Outside",
    "owl": "Owl",
    "paper": "Paper",
    "paws": "Paws",
    "pencil": "Pencil",
    "phone": "Call",
    "potato": "Potato",
    "puppy": "Puppy",
    "pumpkin": "Pumpkin",
    "rabbit": "Rabbit",
    "sock": "Sock",
    "sound": "Sound",
    "spoon": "Spoon",
    "star": "Star",
    "stars_4": "Four",
    "stars_6": "Six",
    "stars_many": "Many",
    "strawberry": "Berry",
    "sun": "Sun",
    "tomato": "Tomato",
    "toy_car": "Toy car",
    "umbrella": "Umbrella",
    "word": "Word",
}


SHAPES = {
    "map": "rect3x4",
    "paper": "rect3x4",
    "drawing": "rect3x4",
    "word": "rect3x4",
    "echo": "rect3x4",
    "stars_4": "rect3x4",
    "stars_6": "rect3x4",
    "stars_many": "rect3x4",
}


def item_path(activity_id: str, item_id: str) -> str:
    return f"/activity-assets/{activity_id}/items/{item_id}.png"


def crop_item(activity_id: str, item_id: str, crop: ItemCrop) -> None:
    source_name, box = crop
    source = ASSET_ROOT / activity_id / source_name
    destination = ASSET_ROOT / activity_id / "items" / f"{item_id}.png"
    destination.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        cropped = image.convert("RGB").crop(box)
        contained = ImageOps.contain(cropped, (512, 512), method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (512, 512), cropped.getpixel((0, 0)))
        canvas.paste(contained, ((512 - contained.width) // 2, (512 - contained.height) // 2))
        canvas.save(destination)


def build_items() -> None:
    for activity_id, items in ITEM_CROPS.items():
        for item_id, crop in items.items():
            crop_item(activity_id, item_id, crop)


def make_item(activity_id: str, item_id: str, selected: bool = False) -> dict[str, Any]:
    result = {
        "id": item_id,
        "src": item_path(activity_id, item_id),
        "shape": SHAPES.get(item_id, "circle"),
        "label": LABELS[item_id],
    }
    if selected:
        result["selected"] = True
    return result


def make_layout(activity_id: str, beat_src: str, mode: str = "single", items: list[str] | None = None, selected: str = "") -> dict:
    layout_items = [
        make_item(activity_id, item_id, selected=item_id == selected)
        for item_id in (items or [])
    ]
    return {
        "mode": mode,
        "selection": "device-scroll" if len(layout_items) > 1 else "none",
        "safeArea": SAFE_AREA,
        "background": {"src": beat_src, "fit": "cover"},
        "items": layout_items,
    }


def plan_for(activity_id: str, beat_id: str, beat_src: str) -> dict:
    round_plans = {
        "activity_animal_sound_imitation": {
            "round_1": ("carousel", ["rabbit", "cat", "puppy"], "rabbit"),
            "round_2": ("carousel", ["rabbit", "cat", "puppy"], "cat"),
            "round_3": ("carousel", ["rabbit", "cat", "puppy"], "puppy"),
        },
        "activity_career_decision_role_play": {
            "round_1": ("choice2", ["alarm", "phone"], "alarm"),
            "round_2": ("choice2", ["hose", "oil"], "hose"),
            "round_3": ("choice2", ["outside", "firefighter"], "outside"),
        },
        "activity_constellation_star_count": {
            "round_1": ("carousel", ["stars_4", "stars_6", "stars_many"], "stars_4"),
            "round_2": ("carousel", ["stars_4", "stars_6", "stars_many"], "stars_6"),
            "round_3": ("carousel", ["stars_4", "stars_6", "stars_many"], "stars_many"),
        },
        "activity_emotion_reader": {
            "round_1": ("choice2", ["face", "help"], "face"),
            "round_2": ("choice3", ["face", "feeling", "help"], "feeling"),
            "round_3": ("choice3", ["heart", "face", "help"], "help"),
        },
        "activity_guided_drawing": {
            "round_1": ("choice2", ["paper", "pencil"], "paper"),
            "round_2": ("choice2", ["paper", "pencil"], "pencil"),
            "round_3": ("choice2", ["drawing", "pencil"], "drawing"),
        },
        "activity_partial_reveal_guess": {
            "round_1": ("choice3", ["ears", "paws", "cat"], "ears"),
            "round_2": ("choice3", ["ears", "paws", "cat"], "paws"),
            "round_3": ("choice3", ["ears", "paws", "cat"], "cat"),
        },
        "activity_phoneme_treasure_hunt": {
            "round_1": ("choice3", ["ball", "cup", "book"], "ball"),
            "round_2": ("choice3", ["banana", "spoon", "leaf"], "banana"),
            "round_3": ("choice3", ["basket", "toy_car", "sock"], "basket"),
            "synthesis": ("carousel", ["ball", "book", "banana"], "book"),
        },
        "activity_recognition_pop_challenge": {
            "round_1": ("choice2", ["apple", "car"], "apple"),
            "round_2": ("choice3", ["apple", "strawberry", "cherries"], "apple"),
            "round_3": ("choice2", ["apple", "basketball"], "apple"),
        },
        "activity_story_challenge_unlock": {
            "round_1": ("choice3", ["fox", "moon", "star"], "moon"),
            "round_2": ("choice3", ["fox", "owl", "moon"], "owl"),
            "round_3": ("choice3", ["fox", "owl", "star"], "star"),
        },
        "activity_travel_planner": {
            "round_1": ("choice3", ["map", "sun", "hat"], "sun"),
            "round_2": ("choice3", ["map", "umbrella", "boots"], "umbrella"),
            "round_3": ("choice3", ["car", "map", "gift"], "gift"),
        },
        "activity_vegetable_sort": {
            "round_1": ("choice3", ["tomato", "broccoli", "carrot"], "tomato"),
            "round_2": ("choice3", ["potato", "cucumber", "carrot"], "potato"),
            "round_3": ("choice3", ["broccoli", "pumpkin", "corn"], "pumpkin"),
        },
        "activity_word_echo_practice": {
            "round_1": ("carousel", ["word", "echo", "sound"], "word"),
            "round_2": ("carousel", ["word", "echo", "sound"], "echo"),
            "round_3": ("carousel", ["word", "echo", "sound"], "sound"),
        },
    }

    plan = round_plans.get(activity_id, {}).get(beat_id)
    if not plan:
        return make_layout(activity_id, beat_src)
    mode, items, selected = plan
    return make_layout(activity_id, beat_src, mode=mode, items=items, selected=selected)


def update_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["screen_style"] = {
        "name": "nordic-light-3d",
        "safe_area": SAFE_AREA,
        "layouts": ["single", "choice2", "choice3", "carousel"],
    }

    for activity in manifest["activities"]:
        activity_id = activity["id"]
        for beat in activity["beats"]:
            beat["layout"] = plan_for(activity_id, beat["id"], beat["src"])

    MANIFEST_PATH.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")


def main() -> None:
    build_items()
    update_manifest()


if __name__ == "__main__":
    main()
