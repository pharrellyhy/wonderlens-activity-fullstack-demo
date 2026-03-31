"""Regression checks for vertical centering in the device panel."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEVICE_SCREEN_PATH = REPO_ROOT / "frontend" / "src" / "components" / "DeviceScreen.jsx"
ANIMATION_OVERLAY_PATH = REPO_ROOT / "frontend" / "src" / "widgets" / "AnimationOverlay.jsx"
PHOTO_GALLERY_PATH = REPO_ROOT / "frontend" / "src" / "components" / "PhotoGallery.jsx"
INDEX_CSS_PATH = REPO_ROOT / "frontend" / "src" / "index.css"


def test_device_screen_keeps_widget_area_centered_on_tall_viewports() -> None:
    source = DEVICE_SCREEN_PATH.read_text(encoding="utf-8")

    assert 'className="flex-1 min-h-0 grid place-items-center' in source
    assert (
        '<AnimationOverlay animation={overlayAnimation} className="flex h-full w-full items-center justify-center">'
        in source
    )


def test_animation_overlay_accepts_layout_class_name() -> None:
    source = ANIMATION_OVERLAY_PATH.read_text(encoding="utf-8")

    assert "export default function AnimationOverlay({ animation, className = '', children })" in source
    assert "const classes = [className, 'transition-all duration-500', animClass]" in source


def test_photo_gallery_centers_by_default_and_only_top_aligns_on_short_viewports() -> None:
    gallery_source = PHOTO_GALLERY_PATH.read_text(encoding="utf-8")
    css_source = INDEX_CSS_PATH.read_text(encoding="utf-8")

    assert 'className="device-gallery-layout flex flex-col items-center justify-center' in gallery_source
    assert "@media (max-height: 760px)" in css_source
    assert ".device-gallery-layout" in css_source
    assert "justify-content: flex-start;" in css_source
