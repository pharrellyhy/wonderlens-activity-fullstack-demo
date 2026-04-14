"""Pure helpers for writing tester feedback bundles to disk."""

import re
from datetime import datetime
from pathlib import Path

FEEDBACK_DIR: Path = Path(__file__).resolve().parent / "feedback"

_NON_ALNUM_DASH = re.compile(r"[^a-z0-9-]+")


def slugify_alias(raw: str | None) -> str:
    """Normalize a tester alias for use in folder names."""
    if not raw:
        return "anon"
    lowered = raw.strip().lower().replace(" ", "-")
    cleaned = _NON_ALNUM_DASH.sub("", lowered).strip("-")
    return cleaned or "anon"


def short_session_id(session_id: str) -> str:
    """Return the first 6 characters of a session id, lowercased."""
    return (session_id or "nosess")[:6].lower()


def build_folder_name(ended_at: datetime, alias: str, session_id: str) -> str:
    """Compose the on-disk folder name for a feedback bundle."""
    stamp = ended_at.strftime("%Y-%m-%d-%H%M")
    return f"{stamp}-{slugify_alias(alias)}-{short_session_id(session_id)}"


def _resolve_safe(bundle_root: Path, relative: str) -> Path:
    """Resolve a relative path against the bundle root, rejecting escapes."""
    if not relative:
        raise ValueError("screenshot path must be non-empty")
    candidate = (bundle_root / relative).resolve()
    root = bundle_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"unsafe screenshot path: {relative}") from exc
    if candidate == root:
        raise ValueError(f"screenshot path resolves to bundle root: {relative}")
    return candidate


def write_feedback_bundle(
    base_dir: Path,
    folder_name: str,
    feedback_json: str,
    screenshots: dict[str, bytes],
) -> Path:
    """Write feedback.json and screenshot blobs into a new bundle directory."""
    bundle_root = base_dir / folder_name
    bundle_root.mkdir(parents=True, exist_ok=True)
    (bundle_root / "screenshots").mkdir(parents=True, exist_ok=True)

    resolved_targets = {rel: _resolve_safe(bundle_root, rel) for rel in screenshots}

    (bundle_root / "feedback.json").write_text(feedback_json, encoding="utf-8")

    for relative, target in resolved_targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(screenshots[relative])

    return bundle_root
