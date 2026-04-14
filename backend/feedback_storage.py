"""Pure helpers for reading and writing tester feedback bundles on disk."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FEEDBACK_DIR: Path = Path(__file__).resolve().parent / "feedback"

_NON_ALNUM_DASH = re.compile(r"[^a-z0-9-]+")
_FOLDER_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

logger = logging.getLogger(__name__)

_SESSION_META_KEYS: tuple[str, ...] = (
    "session_id",
    "tester_alias",
    "app_mode",
    "activity",
    "session_started_at",
    "session_ended_at",
)


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


def _is_safe_folder_name(folder_name: str) -> bool:
    """Reject folder names that contain path separators or traversal markers."""
    if not folder_name or folder_name.startswith("."):
        return False
    return _FOLDER_NAME_RE.match(folder_name) is not None


def list_all_feedback(base_dir: Path | None = None) -> list[dict[str, Any]]:
    """Scan ``base_dir`` and return every flag flattened with its session metadata.

    Each entry has the shape::

        {
            "flag": {...},                 # one FeedbackFlag dict
            "session": {
                "session_id": str,
                "tester_alias": str,
                "app_mode": str,
                "activity": {...},
                "session_started_at": str,
                "session_ended_at": str,
                "folder_name": str,
            },
        }

    Folders whose ``feedback.json`` is missing or malformed are skipped with a
    warning; callers receive a best-effort list. Sorting is the caller's job.
    """
    root = (base_dir or FEEDBACK_DIR).resolve()
    if not root.exists():
        return []

    entries: list[dict[str, Any]] = []
    for bundle_dir in sorted(root.iterdir()):
        if not bundle_dir.is_dir():
            continue
        feedback_json = bundle_dir / "feedback.json"
        if not feedback_json.exists():
            continue
        try:
            payload = json.loads(feedback_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("skipping malformed feedback bundle %s: %s", bundle_dir.name, exc)
            continue

        if not isinstance(payload, dict):
            logger.warning("skipping feedback bundle %s: top-level is not a mapping", bundle_dir.name)
            continue

        session_meta = {key: payload.get(key) for key in _SESSION_META_KEYS}
        session_meta["folder_name"] = bundle_dir.name

        flags = payload.get("flags")
        if not isinstance(flags, list):
            logger.warning("skipping feedback bundle %s: flags is not a list", bundle_dir.name)
            continue

        for flag in flags:
            if not isinstance(flag, dict):
                continue
            entries.append({"flag": flag, "session": session_meta})

    return entries


def read_feedback_image(
    folder_name: str,
    relative_path: str,
    base_dir: Path | None = None,
) -> bytes | None:
    """Read a screenshot from a feedback bundle with strict path validation.

    Raises ``ValueError`` if ``folder_name`` looks unsafe, the bundle resolves
    outside the feedback root (symlink escape), or ``relative_path`` escapes
    the bundle root. Returns ``None`` if the file does not exist.
    """
    if not _is_safe_folder_name(folder_name):
        raise ValueError(f"unsafe feedback folder name: {folder_name!r}")

    root = (base_dir or FEEDBACK_DIR).resolve()
    bundle_root = (root / folder_name).resolve()
    if not bundle_root.is_relative_to(root):
        raise ValueError(f"feedback bundle escapes root: {folder_name!r}")

    target = _resolve_safe(bundle_root, relative_path)
    if not target.is_file():
        return None
    return target.read_bytes()
