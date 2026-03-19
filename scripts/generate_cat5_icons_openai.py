import argparse
import base64
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import httpx
from openai import BadRequestError, OpenAI
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
OUT_DIR = ROOT / "frontend" / "public" / "icons"
TARGET_SIZE = (256, 256)
MODEL = "gpt-image-1.5"


@dataclass(frozen=True)
class AssetPrompt:
    filename: str
    description: str
    game_theme: str


PHOTO_ASSETS: tuple[AssetPrompt, ...] = (
    # --- Polka-Dot Patrol: correct ---
    AssetPrompt(
        "spotted_mushroom_photo.png",
        "A small wild mushroom with a pale cream cap covered in brown spots and speckles, growing on forest floor among moss and fallen leaves. Macro close-up, natural outdoor lighting.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "dotted_pebble_photo.png",
        "A smooth river pebble with natural dot-like speckles and circular mineral patterns on its surface, sitting on dirt and gravel. Warm sunlight, child's-eye perspective looking down.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "speckled_leaf_photo.png",
        "A green leaf with natural speckled markings — small dots of yellow, brown, or red scattered across the surface. Lying on the ground, natural light.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "circle_flower_photo.png",
        "A daisy or similar flower with circular petals arranged in a radial pattern around a round center disc. Shot from above looking down at the circular form. Garden setting, natural light.",
        "Polka-Dot Patrol",
    ),
    # --- Polka-Dot Patrol: distractors ---
    AssetPrompt(
        "straight_stick_photo.png",
        "A plain straight wooden stick or twig lying on the ground. No spots, no dots — just smooth bark with linear grain. Natural forest floor setting.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_bark_photo.png",
        "A piece of tree bark with rough linear texture but no spots or dots. Vertical ridges and furrows. Close-up of a tree trunk, natural lighting.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "long_grass_photo.png",
        "A few blades of tall grass or a small tuft of grass showing long linear shapes with no circular patterns. Outdoor meadow setting, natural light.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "smooth_stone_photo.png",
        "A completely smooth plain grey stone with no markings, spots, or patterns. Uniform color and texture, sitting on dirt or sand.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "pine_needle_photo.png",
        "A small cluster of long thin pine needles lying on the forest floor, fanning out from a single bundle point. Dark green with smooth linear texture, no spots or dots.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_leaf_photo.png",
        "A single plain green leaf with smooth uniform color — no speckles, no spots. Simple oval shape with visible veins but no dot patterns. Lying on brown soil, natural light.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "forked_twig_photo.png",
        "A small Y-shaped twig or forked branch lying on the ground. Smooth brown bark with a clear fork and split. No spots or circular markings. Natural forest floor.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "acorn_cap_photo.png",
        "A single acorn cap (the bumpy cup without the nut) sitting on fallen leaves. Rough cross-hatched texture on the cap surface. Natural outdoor light.",
        "Polka-Dot Patrol",
    ),
    # --- Fluffy Expedition: correct ---
    AssetPrompt(
        "fuzzy_moss_photo.png",
        "A patch of soft fuzzy green moss growing on a rock or tree base. Velvety texture clearly visible in macro close-up. Damp forest setting, soft diffused light.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "fluffy_seed_photo.png",
        "A single fluffy seed like a dandelion seed or milkweed fluff floating or caught on a branch. Wispy white filaments catching the light. Macro close-up, backlit with golden light.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "soft_petal_photo.png",
        "A single velvety flower petal (rose or peony) lying on the ground. Soft silky texture visible. Pastel pink or lavender color. Close-up with soft natural lighting.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "woolly_caterpillar_photo.png",
        "A fuzzy woolly bear caterpillar with visible soft furry bristles crawling on a leaf or twig. Macro close-up showing the fluffy texture, warm outdoor lighting.",
        "Fluffy Expedition Dandelion",
    ),
    # --- Fluffy Expedition: distractors ---
    AssetPrompt(
        "hard_rock_photo.png",
        "A hard angular rock with rough rigid surface. Clearly solid and unyielding. Sitting on dry ground, natural outdoor lighting.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "spiky_pinecone_photo.png",
        "A pinecone with sharp pointed scales sticking out. Prickly texture clearly visible. Lying on forest floor among pine needles. Natural lighting.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "rough_bark_photo.png",
        "Close-up of rough coarse tree bark with deep cracks and rigid texture. Hard and scratchy looking. Natural lighting on tree trunk.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "sharp_thorn_photo.png",
        "A thorny branch or stem with visible sharp thorns and spines. Clearly pointy and prickly. Close-up, natural outdoor setting with green blurred background.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "dry_leaf_photo.png",
        "A single dry crunchy autumn leaf curled at the edges. Brittle brown and orange color with visible cracking and stiff veins. Lying on dry ground. Natural light.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "smooth_pebble_photo.png",
        "A small smooth river-washed pebble with a hard polished surface. Cool grey or beige, sitting on sand or gravel. Natural outdoor light.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "stiff_branch_photo.png",
        "A short rigid tree branch — thick, woody, and unbending. Dark brown bark, snapped end visible. Lying on forest floor. Natural light.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "brittle_shell_photo.png",
        "A thin brittle snail shell or broken eggshell fragment on the ground. Hard, fragile, and delicate. Pale cream and white color on soil. Natural outdoor light.",
        "Fluffy Expedition Dandelion",
    ),
)

ASSETS: tuple[AssetPrompt, ...] = (
    AssetPrompt(
        "spotted_mushroom.png",
        "A cute round mushroom with a creamy-white cap dotted with warm brown spots, sitting on soft green moss.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "dotted_pebble.png",
        "A friendly round pebble with charming circular dot patterns in earth tones like brown, grey, and cream.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "speckled_leaf.png",
        "A bright green leaf with playful polka-dot-like speckles in gold and russet, with visible veins.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "circle_flower.png",
        "A cheerful round daisy-like flower with white petals radiating from a bright yellow circular center.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "straight_stick.png",
        "A simple brown stick with straight wood grain lines and no dots or circles.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_bark.png",
        "A section of tree trunk bark with vertical groove patterns in brown tones, showing lines and ridges instead of dots.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "long_grass.png",
        "A small tuft of tall green grass blades growing from the ground, swaying gently with flowing linear strokes and no dots or circles.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "smooth_stone.png",
        "A perfectly smooth, plain grey-blue stone with no decoration, spots, or patterns.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "pine_needle.png",
        "A neat bundle of dark green pine needles splaying outward like a tiny broom, clearly spiky and line-shaped.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_leaf.png",
        "A simple solid green leaf with clean edges and visible veins running in straight lines, with no speckles or spots.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "forked_twig.png",
        "A cute Y-shaped twig in warm brown, emphasizing the angular branching shape with no dots or circles.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "acorn_cap.png",
        "A small acorn cap in warm tan-brown with a bumpy cross-hatch texture that looks woven or scaly, not dotted.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "fuzzy_moss.png",
        "A close-up patch of soft fuzzy green moss growing on a rock, with velvety plush texture clearly visible.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "fluffy_seed.png",
        "A whimsical floating seed with delicate white fluffy filaments spreading like a tiny parachute.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "soft_petal.png",
        "A plush rounded flower petal in soft pink or lavender with a satiny, touchable quality.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "woolly_caterpillar.png",
        "A cute woolly caterpillar with fluffy orange and brown fur and a friendly child-safe expression.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "hard_rock.png",
        "A chunky angular rock in grey-brown tones with sharp edges, clearly hard and solid.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "spiky_pinecone.png",
        "A detailed pinecone with pointy spiky scales in warm brown, clearly sharp rather than soft.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "rough_bark.png",
        "A section of rough cracked tree bark in dark brown with jagged ridges and a hard scratchy feel.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "sharp_thorn.png",
        "A branch with prominent sharp thorns pointing outward, clearly spiky and the opposite of soft.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "dry_leaf.png",
        "A curled crispy autumn leaf in warm orange-brown with visible cracks and stiff edges.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "smooth_pebble.png",
        "A perfectly round smooth pebble in cool grey-blue tones with a hard shiny surface.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "stiff_branch.png",
        "A sturdy thick brown branch with rough bark and a snapped end, rigid and woody.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "brittle_shell.png",
        "A small spiral snail shell or cracked eggshell fragment in pale cream, thin, hard, and brittle.",
        "Fluffy Expedition Dandelion",
    ),
    # --- Brave Things Hunt (Lion): correct ---
    AssetPrompt(
        "big_rock.png",
        "A large sturdy boulder in warm grey-brown tones, solid and heavy-looking with rough texture.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "thick_trunk.png",
        "A wide thick tree trunk section in rich brown bark, clearly strong and massive with deep ridges.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "sturdy_fence.png",
        "A solid wooden fence post in weathered brown, thick and strong-looking with grain visible.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "heavy_log.png",
        "A thick heavy fallen log in dark brown with rough bark, looking big and strong on the ground.",
        "Brave Things Hunt",
    ),
    # --- Brave Things Hunt (Lion): distractors ---
    AssetPrompt(
        "soft_flower.png",
        "A delicate soft flower with thin petals in pale pink, clearly fragile and gentle.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "thin_grass.png",
        "A few thin wispy blades of grass, clearly light and bendable, swaying gently.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "small_feather.png",
        "A single small fluffy feather in soft white, light and airy with delicate barbs.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "light_leaf.png",
        "A single thin delicate leaf in bright green, clearly flimsy and easy to tear.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "wispy_dandelion.png",
        "A dandelion puff with wispy white seeds ready to blow away, fragile and ethereal.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "tiny_pebble.png",
        "A very small round pebble in light grey, clearly tiny and easy to pick up with two fingers.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "delicate_butterfly.png",
        "A small butterfly with thin translucent wings in pastel colors, clearly delicate and light.",
        "Brave Things Hunt",
    ),
    AssetPrompt(
        "flimsy_paper.png",
        "A crumpled piece of paper or tissue caught on a branch, clearly thin and tearable.",
        "Brave Things Hunt",
    ),
    # --- Color Friends Adventure (Crayons): correct ---
    AssetPrompt(
        "red_flower.png",
        "A bright red flower with vivid red petals, clearly and unmistakably red in color.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "red_berry.png",
        "A cluster of bright red berries on a green stem, round and shiny and deeply red.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "red_bucket.png",
        "A child's small red plastic bucket or pail, solidly bright red with a handle.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "red_leaf.png",
        "A single autumn leaf in vivid red-crimson, clearly matching a red crayon color.",
        "Color Friends Adventure",
    ),
    # --- Color Friends Adventure (Crayons): distractors ---
    AssetPrompt(
        "green_leaf.png",
        "A single bright green leaf with visible veins, clearly green and not red.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "yellow_dandelion.png",
        "A cheerful bright yellow dandelion flower, clearly yellow and sunny colored.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "brown_stick.png",
        "A plain brown stick or twig, earth-toned and woody in brown color.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "white_stone.png",
        "A smooth white stone or pale quartz pebble, clearly white or cream colored.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "blue_pebble.png",
        "A smooth blue-grey pebble with cool blue tones, clearly not red.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "grey_rock.png",
        "A plain grey rock with uniform dull grey color, no red tones at all.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "orange_peel.png",
        "A piece of orange citrus peel on the ground, clearly orange and not red.",
        "Color Friends Adventure",
    ),
    AssetPrompt(
        "purple_flower.png",
        "A small purple wildflower with violet petals, clearly purple not red.",
        "Color Friends Adventure",
    ),
    # --- Circle Spotter Challenge (Eye): correct ---
    AssetPrompt(
        "round_flower_center.png",
        "A daisy or sunflower viewed from above showing the round spiral center with concentric ring patterns.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "wheel_hub.png",
        "A bicycle or wagon wheel hub showing circular spokes radiating from a round center ring.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "snail_shell.png",
        "A spiral snail shell with concentric circular whorls, showing the beautiful round-inside-round pattern.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "tree_rings.png",
        "A cut tree stump showing concentric growth rings, circles within circles in warm brown tones.",
        "Circle Spotter Challenge",
    ),
    # --- Circle Spotter Challenge (Eye): distractors ---
    AssetPrompt(
        "straight_fence.png",
        "A section of straight wooden fence with vertical slats, all lines and no circles.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "square_brick.png",
        "A rectangular red brick with sharp square corners, clearly angular with no curves.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "triangle_sign.png",
        "A triangular warning sign shape in yellow, with three straight sides and pointed corners.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "flat_board.png",
        "A flat rectangular wooden board with straight edges, no round shapes at all.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "long_branch.png",
        "A long straight branch with no curves or circular shapes, extending in one direction.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "pointed_leaf.png",
        "A narrow pointed leaf with sharp tip and angular shape, no circular elements.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "jagged_rock.png",
        "A rock with jagged angular edges and sharp points, clearly not round or circular.",
        "Circle Spotter Challenge",
    ),
    AssetPrompt(
        "rectangular_door.png",
        "A simple rectangular door shape in warm wood tones with straight lines and right angles.",
        "Circle Spotter Challenge",
    ),
    # --- Neighborhood Safety Patrol (Firefighter): correct ---
    AssetPrompt(
        "fire_hydrant.png",
        "A bright red fire hydrant with its characteristic barrel shape and side outlets, clearly a safety device.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "stop_sign_post.png",
        "A red octagonal stop sign on a metal pole, the classic traffic safety sign.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "crosswalk_stripes.png",
        "White painted crosswalk stripes on a road surface, the pedestrian safety markings.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "streetlight.png",
        "A tall streetlight with a glowing lamp at the top, illuminating the road for safety at night.",
        "Neighborhood Safety Patrol",
    ),
    # --- Neighborhood Safety Patrol (Firefighter): distractors ---
    AssetPrompt(
        "park_bench.png",
        "A wooden park bench for sitting, comfortable but not a safety device.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "mailbox.png",
        "A blue or green mailbox on a post, for sending letters but not for safety.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "garden_hose.png",
        "A coiled green garden hose on the ground, for watering but not safety equipment.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "flower_pot.png",
        "A terracotta flower pot with a cheerful plant, decorative but not safety-related.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "trash_can.png",
        "A curbside trash can or bin, useful for cleanliness but not a safety device.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "bird_feeder.png",
        "A hanging bird feeder with seeds, for feeding birds but not for safety.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "rain_puddle.png",
        "A shallow rain puddle on a sidewalk, natural but not a safety feature.",
        "Neighborhood Safety Patrol",
    ),
    AssetPrompt(
        "fallen_leaf_pile.png",
        "A small pile of fallen autumn leaves on the ground, natural but not safety equipment.",
        "Neighborhood Safety Patrol",
    ),
    # --- Sound Detective Agency (Piano): correct ---
    AssetPrompt(
        "metal_railing.png",
        "A shiny metal railing or handrail that would make a clear clang when tapped.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "wooden_bench.png",
        "A sturdy wooden park bench that would make a solid knock when tapped.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "hollow_pipe.png",
        "A short hollow metal or plastic pipe that would resonate with a deep tone when tapped.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "wind_chimes.png",
        "A set of small wind chimes with dangling metal or bamboo tubes that ring in the breeze.",
        "Sound Detective Agency",
    ),
    # --- Sound Detective Agency (Piano): distractors ---
    AssetPrompt(
        "soft_moss_pad.png",
        "A thick cushion of soft green moss, silent and absorbent when touched.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "still_puddle.png",
        "A calm still puddle of water on the ground, quiet and makes no sound.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "spongy_mushroom.png",
        "A soft spongy mushroom cap, silent and cushiony when pressed.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "quiet_feather.png",
        "A single soft feather lying on the ground, completely silent and weightless.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "limp_cloth.png",
        "A piece of soft limp fabric or cloth caught on a bush, silent and floppy.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "flat_sand.png",
        "A patch of flat smooth sand, soft and silent when touched.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "cotton_seedpod.png",
        "A fluffy cotton-like seed pod from a tree, soft and completely silent.",
        "Sound Detective Agency",
    ),
    AssetPrompt(
        "silent_stone.png",
        "A smooth flat stone half-buried in soft earth, muted and barely makes sound when tapped.",
        "Sound Detective Agency",
    ),
    # --- Rain Guard Patrol (Raincoat): correct ---
    AssetPrompt(
        "big_leaf_shelter.png",
        "A large broad leaf like a banana leaf or burdock, big enough to hold over your head as shelter.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "tree_canopy.png",
        "A thick leafy tree canopy seen from below, providing natural shade and rain protection.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "roof_overhang.png",
        "A building roof overhang or porch cover, providing clear dry shelter from above.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "umbrella_bush.png",
        "A wide dense bush or shrub with thick leaf coverage, shaped like a natural umbrella.",
        "Rain Guard Patrol",
    ),
    # --- Rain Guard Patrol (Raincoat): distractors ---
    AssetPrompt(
        "thin_wire.png",
        "A thin wire or string stretched between posts, clearly cannot block rain.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "open_fence.png",
        "An open wooden or chain-link fence with gaps, rain passes right through.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "mesh_net.png",
        "A mesh or netting material with small holes, clearly cannot block water.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "bare_branch.png",
        "A bare tree branch with no leaves, offers no rain protection at all.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "sparse_grass.png",
        "A few sparse blades of grass, too thin and low to shelter anything from rain.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "flat_stone_slab.png",
        "A flat stone slab lying on the ground, not overhead so it cannot shelter from rain.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "chain_link.png",
        "A section of chain-link fence with diamond-shaped holes, rain passes right through.",
        "Rain Guard Patrol",
    ),
    AssetPrompt(
        "shallow_puddle.png",
        "A shallow puddle of water on the ground, caused by rain rather than protecting from it.",
        "Rain Guard Patrol",
    ),
)


def load_env_file(path: Path) -> dict[str, str]:
    def parse_value(raw_value: str) -> str:
        value = raw_value.strip()
        if not value:
            return ""
        if value[0] in {'"', "'"}:
            quote = value[0]
            end = value.find(quote, 1)
            if end != -1:
                return value[1:end]
        return value.split(" #", 1)[0].strip().strip('"').strip("'")

    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = parse_value(value)
    return values


def build_prompt(asset: AssetPrompt) -> str:
    return (
        f"Create a square illustrated icon for a children's outdoor collection game named {asset.game_theme}. "
        f"Main subject: {asset.description} "
        "Use a warm children's-book illustration style with gentle outlines, soft painterly shading, and natural earth-toned colors. "
        "Show exactly one main object centered and large in frame, with a simple soft outdoor background and no text. "
        "The background must extend to ALL edges of the image — no black borders, no white borders, no empty margins, no rounded corner mask. "
        "Keep the silhouette very clear and easy to recognize at small UI icon size for ages 2-8. "
        "Do not add extra objects, characters, labels, borders, frames, or watermarks."
    )


def build_prompt_photo(asset: AssetPrompt) -> str:
    return (
        f"A close-up photograph of {asset.description} found outdoors in a garden, park, or forest. "
        "Natural warm lighting, shallow depth of field with soft blurred green background. "
        "Child's-eye perspective looking down. Shot on iPhone, candid nature photography style. "
        "The subject must fill most of the frame — large and close-up, edge-to-edge, with minimal background padding. "
        "The image must have sharp square corners with NO rounded corners, NO border radius, NO vignette, and NO card-like framing. "
        "Square format. No text, no labels, no watermarks."
    )


def decode_png(b64_json: str) -> Image.Image:
    return Image.open(BytesIO(base64.b64decode(b64_json))).convert("RGBA")


def load_from_url(url: str) -> Image.Image:
    response = httpx.get(url, timeout=180.0)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")


def save_icon(image: Image.Image, out_path: Path) -> None:
    resized = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    resized.save(out_path, format="PNG")


def get_client(base_url_override: str | None = None) -> OpenAI:
    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)
    api_key = env.get("OPENAI_API_KEY", "")
    base_url = base_url_override or env.get("OPENAI_BASE_URL", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing from backend/.env")
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs, timeout=180.0, max_retries=0)


def render_one(client: OpenAI, asset: AssetPrompt, size: str, quality: str, overwrite: bool) -> None:
    out_path = OUT_DIR / asset.filename
    if out_path.exists() and not overwrite:
        print(f"skip {asset.filename} (exists)")
        return

    prompt = build_prompt(asset)
    started = time.perf_counter()
    request_kwargs = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "background": "opaque",
        "output_format": "png",
        "response_format": "b64_json",
    }
    try:
        response = client.images.generate(**request_kwargs)
    except BadRequestError as exc:
        message = str(exc)
        if "Unknown parameter: 'response_format'" not in message:
            raise
        request_kwargs.pop("response_format")
        response = client.images.generate(**request_kwargs)
    if not response.data:
        raise RuntimeError(
            f"No image bytes returned for {asset.filename}. "
            "The configured OpenAI-compatible base URL appears to advertise the model but not implement image generation."
        )
    item = response.data[0]
    if getattr(item, "b64_json", None):
        image = decode_png(item.b64_json)
    elif getattr(item, "url", None):
        image = load_from_url(item.url)
    else:
        raise RuntimeError(
            f"No image bytes returned for {asset.filename}. "
            "The configured OpenAI-compatible base URL appears to advertise the model but not implement image generation."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_icon(image, out_path)
    elapsed = time.perf_counter() - started
    print(f"generated {asset.filename} in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cat 5 icons with gpt-image-1.5.")
    parser.add_argument("--only", help="Single filename to generate, e.g. spotted_mushroom.png")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    parser.add_argument("--base-url", help="Optional override for OPENAI_BASE_URL without editing backend/.env")
    parser.add_argument("--size", default="1024x1024", choices=("256x256", "512x512", "1024x1024"))
    parser.add_argument("--quality", default="medium", choices=("low", "medium", "high"))
    args = parser.parse_args()

    client = get_client(args.base_url)
    assets = ASSETS
    if args.only:
        assets = tuple(asset for asset in ASSETS if asset.filename == args.only)
        if not assets:
            raise SystemExit(f"Unknown filename: {args.only}")

    for asset in assets:
        render_one(client, asset, size=args.size, quality=args.quality, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
