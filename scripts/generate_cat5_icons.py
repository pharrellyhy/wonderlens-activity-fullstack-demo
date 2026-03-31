#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SIZE = 256
ICON_BOUNDS = (16, 16, 240, 240)
OUTLINE = (96, 73, 44, 255)
SHADOW = (70, 106, 48, 72)
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "frontend" / "public" / "icons"


def rgb(hex_value: str) -> tuple[int, int, int, int]:
    hex_value = hex_value.lstrip("#")
    return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4)) + (255,)


def mix(c1: tuple[int, int, int, int], c2: tuple[int, int, int, int], amount: float) -> tuple[int, int, int, int]:
    return tuple(int(a + (b - a) * amount) for a, b in zip(c1, c2))


def make_canvas(background: str = "mint") -> Image.Image:
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    themes = {
        "mint": (rgb("#eef8dd"), rgb("#d9edbf")),
        "sun": (rgb("#f7f2d8"), rgb("#e6efc6")),
    }
    top, bottom = themes[background]

    gradient = Image.new("RGBA", (SIZE, SIZE), top)
    gradient_draw = ImageDraw.Draw(gradient)
    for y in range(SIZE):
        color = mix(top, bottom, y / (SIZE - 1))
        gradient_draw.line((0, y, SIZE, y), fill=color)

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(ICON_BOUNDS, radius=36, fill=255)
    base.paste(gradient, (0, 0), mask)

    border = ImageDraw.Draw(base)
    border.rounded_rectangle(ICON_BOUNDS, radius=36, outline=rgb("#d0e8b6"), width=3)

    glaze = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glaze_draw = ImageDraw.Draw(glaze)
    glaze_draw.ellipse((42, 18, 214, 126), fill=(255, 255, 255, 34))
    glaze = glaze.filter(ImageFilter.GaussianBlur(8))
    base.alpha_composite(glaze)
    return base


def shadow_ellipse(
    image: Image.Image, box: tuple[int, int, int, int], fill: tuple[int, int, int, int] = SHADOW
) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse(box, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    image.alpha_composite(layer)


def stroke_line(
    draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill: tuple[int, int, int, int], width: int
) -> None:
    draw.line(points, fill=OUTLINE, width=width + 4, joint="curve")
    draw.line(points, fill=fill, width=width, joint="curve")


def leaf_polygon(cx: float, cy: float, width: float, height: float) -> list[tuple[float, float]]:
    return [
        (cx, cy - height / 2),
        (cx + width / 2, cy - height / 5),
        (cx + width / 3, cy + height / 3),
        (cx, cy + height / 2),
        (cx - width / 3, cy + height / 3),
        (cx - width / 2, cy - height / 5),
    ]


def draw_leaf(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    width: float,
    height: float,
    fill: tuple[int, int, int, int],
    spots: list[tuple[int, int, int, int, tuple[int, int, int, int]]] | None = None,
) -> None:
    points = leaf_polygon(cx, cy, width, height)
    draw.polygon(points, fill=fill, outline=OUTLINE)
    stroke_line(draw, [(cx, cy - height / 2 + 8), (cx, cy + height / 2 - 2)], mix(fill, rgb("#587d2a"), 0.45), 4)
    vein_color = mix(fill, rgb("#eaf6b9"), 0.25)
    stroke_line(draw, [(cx, cy), (cx + width / 5, cy - height / 6)], vein_color, 3)
    stroke_line(draw, [(cx, cy + 8), (cx + width / 4, cy + height / 8)], vein_color, 3)
    stroke_line(draw, [(cx, cy), (cx - width / 5, cy - height / 6)], vein_color, 3)
    stroke_line(draw, [(cx, cy + 8), (cx - width / 4, cy + height / 8)], vein_color, 3)
    if spots:
        for sx, sy, rx, ry, color in spots:
            draw.ellipse((sx - rx, sy - ry, sx + rx, sy + ry), fill=color, outline=OUTLINE, width=2)


def draw_mushroom(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 184, 186, 208))
    draw = ImageDraw.Draw(image)
    moss = rgb("#8ebd54")
    draw.ellipse((72, 176, 154, 210), fill=moss, outline=OUTLINE, width=3)
    draw.ellipse((112, 174, 188, 210), fill=rgb("#7eae47"), outline=OUTLINE, width=3)
    draw.rounded_rectangle((110, 108, 146, 186), radius=16, fill=rgb("#f0ead8"), outline=OUTLINE, width=4)
    draw.ellipse((62, 72, 194, 148), fill=rgb("#f7efe2"), outline=OUTLINE, width=4)
    draw.ellipse((74, 92, 182, 148), fill=rgb("#e6d4bc"), outline=OUTLINE, width=3)
    for x, y, r in ((92, 94, 10), (116, 112, 8), (147, 96, 11), (170, 114, 8), (133, 86, 9)):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=rgb("#a97a4d"), outline=OUTLINE, width=2)
    draw.ellipse((84, 78, 136, 106), fill=(255, 255, 255, 70))


def draw_dotted_pebble(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 176, 186, 206))
    draw = ImageDraw.Draw(image)
    draw.ellipse((70, 88, 190, 184), fill=rgb("#b4a78f"), outline=OUTLINE, width=4)
    draw.ellipse((82, 100, 178, 174), fill=rgb("#cabda6"), outline=OUTLINE, width=2)
    circles = [
        (97, 116, 10, rgb("#8d7a65")),
        (128, 108, 12, rgb("#a89783")),
        (154, 126, 9, rgb("#89725c")),
        (117, 144, 8, rgb("#92806d")),
        (146, 152, 7, rgb("#7d6c58")),
    ]
    for x, y, r, color in circles:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=OUTLINE, width=2)
    draw.ellipse((90, 96, 132, 118), fill=(255, 255, 255, 50))


def draw_speckled_leaf(image: Image.Image) -> None:
    shadow_ellipse(image, (68, 188, 188, 210))
    draw = ImageDraw.Draw(image)
    draw_leaf(
        draw,
        128,
        128,
        108,
        146,
        rgb("#6caf46"),
        spots=[
            (99, 110, 8, 6, rgb("#ccbe59")),
            (146, 98, 7, 5, rgb("#d68a45")),
            (138, 142, 8, 6, rgb("#b95f49")),
            (110, 152, 6, 5, rgb("#ceb760")),
            (155, 124, 5, 4, rgb("#d7ca74")),
        ],
    )
    stroke_line(draw, [(128, 192), (128, 212)], rgb("#6b8f39"), 5)


def draw_circle_flower(image: Image.Image) -> None:
    shadow_ellipse(image, (74, 188, 186, 208))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(128, 180), (128, 104)], rgb("#79a646"), 8)
    draw_leaf(draw, 96, 182, 38, 52, rgb("#7fb34a"))
    draw_leaf(draw, 160, 182, 38, 52, rgb("#7fb34a"))
    for angle in range(0, 360, 30):
        radians = math.radians(angle)
        cx = 128 + math.cos(radians) * 34
        cy = 104 + math.sin(radians) * 34
        draw.ellipse((cx - 15, cy - 15, cx + 15, cy + 15), fill=rgb("#fffaf2"), outline=OUTLINE, width=3)
    draw.ellipse((106, 82, 150, 126), fill=rgb("#f2c83f"), outline=OUTLINE, width=4)
    draw.ellipse((112, 86, 137, 102), fill=(255, 255, 255, 60))


def draw_straight_stick(image: Image.Image) -> None:
    shadow_ellipse(image, (68, 184, 188, 206))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(78, 164), (186, 106)], rgb("#a27144"), 14)
    stroke_line(draw, [(78, 164), (186, 106)], rgb("#b98556"), 8)
    for offset in (-10, 0, 10):
        stroke_line(draw, [(96, 154 + offset / 3), (170, 116 + offset / 3)], rgb("#8a5f38"), 2)


def draw_plain_bark(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 184, 184, 206))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((84, 56, 172, 190), radius=22, fill=rgb("#9a6d45"), outline=OUTLINE, width=4)
    for x in (102, 121, 141, 158):
        stroke_line(draw, [(x, 68), (x - 2, 180)], rgb("#7d5637"), 5)
    stroke_line(draw, [(112, 80), (108, 166)], rgb("#bb8a5e"), 3)
    stroke_line(draw, [(148, 76), (144, 170)], rgb("#bb8a5e"), 3)


def draw_long_grass(image: Image.Image) -> None:
    shadow_ellipse(image, (74, 188, 184, 208))
    draw = ImageDraw.Draw(image)
    blade_colors = [rgb("#6ead4a"), rgb("#81bc54"), rgb("#5e9640"), rgb("#8fc75f"), rgb("#74a948")]
    paths = [
        [(112, 194), (92, 164), (86, 116)],
        [(122, 194), (114, 150), (118, 92)],
        [(132, 194), (140, 150), (154, 96)],
        [(142, 194), (160, 164), (172, 124)],
        [(100, 194), (106, 160), (100, 126)],
    ]
    for color, path in zip(blade_colors, paths):
        stroke_line(draw, path, color, 8)


def draw_smooth_stone(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 186, 186, 208))
    draw = ImageDraw.Draw(image)
    draw.ellipse((78, 102, 184, 182), fill=rgb("#9aa7b3"), outline=OUTLINE, width=4)
    draw.ellipse((92, 114, 174, 176), fill=rgb("#b8c4cf"), outline=OUTLINE, width=2)
    draw.ellipse((98, 112, 138, 132), fill=(255, 255, 255, 55))


def draw_pine_needle(image: Image.Image) -> None:
    shadow_ellipse(image, (70, 190, 188, 208))
    draw = ImageDraw.Draw(image)
    stem = (128, 186)
    for angle in (-66, -46, -24, 0, 22, 42, 62):
        length = 86 if angle not in (-24, 22) else 76
        radians = math.radians(angle)
        end = (stem[0] + math.cos(radians) * length, stem[1] - math.sin(radians) * length)
        stroke_line(draw, [stem, end], rgb("#567a30"), 6)
    draw.ellipse((118, 180, 138, 198), fill=rgb("#8a6541"), outline=OUTLINE, width=3)


def draw_plain_leaf(image: Image.Image) -> None:
    shadow_ellipse(image, (70, 188, 188, 210))
    draw = ImageDraw.Draw(image)
    draw_leaf(draw, 128, 128, 106, 144, rgb("#74b24a"))
    stroke_line(draw, [(128, 190), (128, 212)], rgb("#6b8f39"), 5)


def draw_forked_twig(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 186, 188, 208))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(128, 190), (128, 128)], rgb("#8f6339"), 14)
    stroke_line(draw, [(128, 132), (90, 92)], rgb("#8f6339"), 12)
    stroke_line(draw, [(128, 132), (166, 88)], rgb("#8f6339"), 12)
    stroke_line(draw, [(128, 190), (128, 128)], rgb("#ad7b4c"), 8)


def draw_acorn_cap(image: Image.Image) -> None:
    shadow_ellipse(image, (84, 186, 174, 206))
    draw = ImageDraw.Draw(image)
    draw.pieslice((82, 92, 174, 176), start=0, end=180, fill=rgb("#b18b5b"), outline=OUTLINE, width=4)
    draw.arc((82, 92, 174, 176), start=0, end=180, fill=OUTLINE, width=4)
    for row_y in (118, 136, 154):
        stroke_line(draw, [(92, row_y), (164, row_y - 10)], rgb("#8c6741"), 3)
    for col_x in (98, 116, 134, 152):
        stroke_line(draw, [(col_x, 112), (col_x - 10, 168)], rgb("#c79a67"), 3)


def draw_fuzzy_moss(image: Image.Image) -> None:
    shadow_ellipse(image, (70, 188, 188, 208))
    draw = ImageDraw.Draw(image)
    blobs = [
        (98, 150, 34, 28, rgb("#7fb849")),
        (128, 132, 42, 34, rgb("#90c857")),
        (160, 152, 32, 26, rgb("#74ad44")),
        (128, 164, 46, 28, rgb("#7eb54a")),
    ]
    for cx, cy, rx, ry, color in blobs:
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=color, outline=OUTLINE, width=4)
    for x in range(86, 174, 10):
        for y in range(114, 182, 11):
            stroke_line(draw, [(x, y + 5), (x - 2, y - 7)], rgb("#bfe58a"), 2)


def draw_fluffy_seed(image: Image.Image) -> None:
    shadow_ellipse(image, (84, 186, 172, 204))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(128, 176), (128, 124)], rgb("#7ca04d"), 5)
    draw.ellipse((120, 170, 136, 186), fill=rgb("#a57a54"), outline=OUTLINE, width=3)
    for angle in range(0, 360, 18):
        radians = math.radians(angle)
        outer = (128 + math.cos(radians) * 52, 118 + math.sin(radians) * 52)
        mid = (128 + math.cos(radians) * 36, 118 + math.sin(radians) * 36)
        stroke_line(draw, [(128, 118), mid], rgb("#f8fbf3"), 3)
        draw.ellipse(
            (outer[0] - 5, outer[1] - 5, outer[0] + 5, outer[1] + 5), fill=rgb("#fffef9"), outline=OUTLINE, width=2
        )
    draw.ellipse((108, 98, 144, 130), fill=(255, 255, 255, 35))


def draw_soft_petal(image: Image.Image) -> None:
    shadow_ellipse(image, (82, 188, 174, 206))
    draw = ImageDraw.Draw(image)
    points = [(128, 76), (170, 120), (152, 184), (128, 202), (102, 184), (84, 122)]
    draw.polygon(points, fill=rgb("#f3a8be"), outline=OUTLINE)
    draw.polygon(
        [(128, 92), (152, 124), (140, 176), (128, 186), (116, 176), (102, 124)],
        fill=rgb("#f7c5d2"),
        outline=(0, 0, 0, 0),
    )
    stroke_line(draw, [(128, 92), (128, 184)], rgb("#f9dbe5"), 4)
    stroke_line(draw, [(128, 122), (146, 152)], rgb("#f6d7e2"), 3)
    stroke_line(draw, [(128, 128), (110, 156)], rgb("#f6d7e2"), 3)


def draw_woolly_caterpillar(image: Image.Image) -> None:
    shadow_ellipse(image, (62, 188, 194, 208))
    draw = ImageDraw.Draw(image)
    segments = [
        (88, 150, 24, rgb("#9d5b2e")),
        (114, 142, 25, rgb("#c06d30")),
        (142, 144, 25, rgb("#7f4d25")),
        (168, 154, 23, rgb("#b86933")),
    ]
    for cx, cy, r, color in segments:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=OUTLINE, width=4)
        for dx in range(-r + 6, r - 4, 8):
            stroke_line(draw, [(cx + dx, cy - r + 4), (cx + dx - 2, cy - r - 10)], mix(color, rgb("#f2cb8b"), 0.3), 2)
            stroke_line(draw, [(cx + dx, cy + r - 4), (cx + dx + 1, cy + r + 10)], mix(color, rgb("#f2cb8b"), 0.3), 2)
    draw.ellipse((72, 132, 108, 166), fill=rgb("#d3843b"), outline=OUTLINE, width=4)
    draw.ellipse((83, 142, 90, 149), fill=rgb("#2c2216"))
    draw.ellipse((95, 142, 102, 149), fill=rgb("#2c2216"))


def draw_hard_rock(image: Image.Image) -> None:
    shadow_ellipse(image, (68, 186, 188, 208))
    draw = ImageDraw.Draw(image)
    points = [(82, 174), (66, 132), (98, 92), (152, 82), (190, 118), (180, 174), (132, 194)]
    draw.polygon(points, fill=rgb("#8a9199"), outline=OUTLINE)
    draw.polygon(
        [(96, 164), (86, 132), (106, 108), (142, 100), (166, 126), (160, 164), (128, 176)],
        fill=rgb("#a2aab2"),
        outline=(0, 0, 0, 0),
    )
    stroke_line(draw, [(100, 160), (120, 136), (148, 146)], rgb("#737a82"), 4)


def draw_spiky_pinecone(image: Image.Image) -> None:
    shadow_ellipse(image, (78, 186, 178, 206))
    draw = ImageDraw.Draw(image)
    draw.ellipse((94, 74, 162, 186), fill=rgb("#9c6b3c"), outline=OUTLINE, width=4)
    scale_centers = [
        (128, 94),
        (114, 114),
        (142, 114),
        (102, 136),
        (128, 136),
        (154, 136),
        (114, 158),
        (142, 158),
    ]
    for cx, cy in scale_centers:
        points = [(cx, cy - 16), (cx + 14, cy + 4), (cx, cy + 18), (cx - 14, cy + 4)]
        draw.polygon(points, fill=rgb("#b58453"), outline=OUTLINE)
        stroke_line(draw, [(cx, cy + 6), (cx, cy + 18)], rgb("#7a532f"), 2)


def draw_rough_bark(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 184, 184, 206))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((84, 54, 172, 192), radius=20, fill=rgb("#765031"), outline=OUTLINE, width=4)
    cracks = [
        [(104, 72), (112, 102), (96, 136), (110, 172)],
        [(128, 68), (120, 106), (136, 140), (126, 178)],
        [(152, 76), (142, 110), (156, 148), (146, 180)],
    ]
    for path in cracks:
        stroke_line(draw, path, rgb("#5b3a21"), 6)
    stroke_line(draw, [(116, 90), (130, 116), (122, 150)], rgb("#9b6d45"), 3)
    stroke_line(draw, [(146, 96), (134, 126), (144, 160)], rgb("#9b6d45"), 3)


def draw_sharp_thorn(image: Image.Image) -> None:
    shadow_ellipse(image, (66, 188, 188, 208))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(78, 178), (182, 96)], rgb("#7e9f47"), 12)
    for x, y, dx, dy in ((112, 154, -18, -10), (138, 132, -8, -20), (154, 120, 18, -10), (96, 166, 10, 18)):
        draw.polygon([(x, y), (x + dx, y + dy), (x + dx // 2, y + dy // 2 + 12)], fill=rgb("#d8dccd"), outline=OUTLINE)


def draw_dry_leaf(image: Image.Image) -> None:
    shadow_ellipse(image, (72, 188, 188, 208))
    draw = ImageDraw.Draw(image)
    points = [(126, 74), (170, 102), (184, 150), (152, 192), (112, 186), (78, 150), (90, 102)]
    draw.polygon(points, fill=rgb("#c58a42"), outline=OUTLINE)
    draw.polygon(
        [(126, 86), (154, 110), (164, 148), (144, 176), (114, 172), (92, 146), (102, 110)],
        fill=rgb("#e0a15a"),
        outline=(0, 0, 0, 0),
    )
    stroke_line(draw, [(126, 82), (128, 186)], rgb("#8f5b2e"), 4)
    stroke_line(draw, [(128, 120), (150, 100)], rgb("#a66a35"), 3)
    stroke_line(draw, [(128, 138), (102, 114)], rgb("#a66a35"), 3)
    stroke_line(draw, [(128, 150), (150, 160)], rgb("#8c5528"), 3)


def draw_smooth_pebble(image: Image.Image) -> None:
    shadow_ellipse(image, (82, 188, 174, 206))
    draw = ImageDraw.Draw(image)
    draw.ellipse((90, 104, 168, 176), fill=rgb("#97a5af"), outline=OUTLINE, width=4)
    draw.ellipse((102, 114, 162, 168), fill=rgb("#b7c4ce"), outline=(0, 0, 0, 0))
    draw.ellipse((106, 114, 132, 130), fill=(255, 255, 255, 75))


def draw_stiff_branch(image: Image.Image) -> None:
    shadow_ellipse(image, (64, 186, 192, 208))
    draw = ImageDraw.Draw(image)
    stroke_line(draw, [(76, 170), (184, 108)], rgb("#7a532f"), 18)
    stroke_line(draw, [(126, 140), (148, 92)], rgb("#7a532f"), 12)
    stroke_line(draw, [(76, 170), (184, 108)], rgb("#9a6a3d"), 10)
    draw.polygon([(180, 108), (194, 102), (188, 120)], fill=rgb("#e9ddca"), outline=OUTLINE)


def draw_brittle_shell(image: Image.Image) -> None:
    shadow_ellipse(image, (82, 188, 176, 206))
    draw = ImageDraw.Draw(image)
    draw.ellipse((94, 94, 168, 178), fill=rgb("#f0e6d1"), outline=OUTLINE, width=4)
    draw.ellipse((112, 112, 156, 162), fill=rgb("#d8ccb2"), outline=OUTLINE, width=3)
    draw.arc((104, 102, 160, 166), start=20, end=320, fill=rgb("#c1b195"), width=4)
    draw.arc((114, 110, 150, 156), start=40, end=320, fill=rgb("#b6a484"), width=4)
    draw.polygon([(146, 130), (176, 120), (166, 154)], fill=rgb("#f8f3ea"), outline=OUTLINE)


ASSETS = {
    "spotted_mushroom.png": ("mint", draw_mushroom),
    "dotted_pebble.png": ("mint", draw_dotted_pebble),
    "speckled_leaf.png": ("mint", draw_speckled_leaf),
    "circle_flower.png": ("mint", draw_circle_flower),
    "straight_stick.png": ("mint", draw_straight_stick),
    "plain_bark.png": ("mint", draw_plain_bark),
    "long_grass.png": ("mint", draw_long_grass),
    "smooth_stone.png": ("mint", draw_smooth_stone),
    "pine_needle.png": ("mint", draw_pine_needle),
    "plain_leaf.png": ("mint", draw_plain_leaf),
    "forked_twig.png": ("mint", draw_forked_twig),
    "acorn_cap.png": ("mint", draw_acorn_cap),
    "fuzzy_moss.png": ("sun", draw_fuzzy_moss),
    "fluffy_seed.png": ("sun", draw_fluffy_seed),
    "soft_petal.png": ("sun", draw_soft_petal),
    "woolly_caterpillar.png": ("sun", draw_woolly_caterpillar),
    "hard_rock.png": ("sun", draw_hard_rock),
    "spiky_pinecone.png": ("sun", draw_spiky_pinecone),
    "rough_bark.png": ("sun", draw_rough_bark),
    "sharp_thorn.png": ("sun", draw_sharp_thorn),
    "dry_leaf.png": ("sun", draw_dry_leaf),
    "smooth_pebble.png": ("sun", draw_smooth_pebble),
    "stiff_branch.png": ("sun", draw_stiff_branch),
    "brittle_shell.png": ("sun", draw_brittle_shell),
}


def render_asset(filename: str, background: str, painter) -> None:
    image = make_canvas(background)
    painter(image)
    image.save(OUT_DIR / filename)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (background, painter) in ASSETS.items():
        render_asset(filename, background, painter)
    print(f"Generated {len(ASSETS)} icons in {OUT_DIR}")


if __name__ == "__main__":
    main()
