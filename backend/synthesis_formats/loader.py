"""Synthesis format registry — loads and parses per-format markdown files.

Format files live in backend/synthesis_formats/*.md.  Each file has a YAML
frontmatter block followed by named body sections separated by bare headings
matching the regex ``^# (\\w+)$``.  Unknown sections are silently ignored;
missing required sections raise ``ValueError``.

Usage:
    from synthesis_formats import get_format, get_format_registry

    fmt = get_format("collaborative_story")
    print(fmt.system_prompt)
"""

import logging
import re
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping

import yaml
from pydantic import BaseModel, Field

try:
    from ..logger import setup_logger
except ImportError:
    from logger import setup_logger

logger: logging.Logger = setup_logger(__name__)

_FORMATS_DIR = Path(__file__).parent

# Matches a bare section heading: exactly "# word" with optional trailing \r
# (so CRLF-saved files still parse — without \r? the MULTILINE $ anchor leaves
# a trailing \r on the captured line and the split produces no sections).
_SECTION_HEADING_RE = re.compile(r"^# (\w+)[ \t]*\r?$", re.MULTILINE)

# Body sections that every format file must provide.
_REQUIRED_BODY_SECTIONS = frozenset({"system_prompt", "user_prompt", "direction_template"})


class SynthesisFormat(BaseModel):
    """Schema for one synthesis format loaded from a markdown file.

    Frontmatter fields supply structured metadata; body sections provide raw
    prompt strings that are consumed verbatim by the synthesis generator.
    """

    # --- Identity ---
    id: str
    display_name: str

    # --- Scene layout ---
    scene_count: int = Field(ge=1, le=5)
    scene_aspect_ratio: str = "16:9"
    achievement_aspect_ratio: str = "1:1"

    # --- LLM parameters ---
    max_tokens: int = 2048
    temperature: float = 0.7

    # --- Length constraints (keyed by tier: "T0", "T1", "T2") ---
    min_sentences_total: dict[str, int]
    direction_max_sentences: dict[str, int]
    direction_tier_sentences: dict[str, str]

    # --- Game behaviour flags ---
    is_naming_game: bool = True
    confirm_goes_to: Literal["child_try", "generate"] = "child_try"
    supports_delegation: bool = True

    # --- Invite templates ---
    invite_templates: list[str]
    invite_direction: str

    # --- Raw prompt bodies (populated from markdown body sections) ---
    # min_length=1 guards against a format file with a heading but empty body:
    # e.g. `# system_prompt\n\n# user_prompt` would otherwise build a format
    # with silently empty prompts.
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    direction_template: str = Field(min_length=1)


def _parse_format_file(path: Path) -> SynthesisFormat:
    """Parse a synthesis format markdown file and return a ``SynthesisFormat``.

    The file must begin with a ``---`` YAML frontmatter block.  The body that
    follows is split on bare section headings (lines matching ``^# (\\w+)$``).
    Unknown section names are silently ignored.  Missing required sections
    raise ``ValueError`` naming the missing section.

    Args:
        path: Absolute path to the ``.md`` format file.

    Returns:
        Populated ``SynthesisFormat`` instance.

    Raises:
        ValueError: If the file has no frontmatter, or is missing a required body section.
        pydantic.ValidationError: If the frontmatter contains invalid field values.
    """
    raw = path.read_text(encoding="utf-8")

    # --- Extract YAML frontmatter ---
    fm_match = re.match(r"^---\s*\n(.*?)\n---[ \t]*\n?", raw, re.DOTALL)
    if not fm_match:
        raise ValueError(f"Missing YAML frontmatter in {path.name}. File must start with ---.")

    frontmatter: dict = yaml.safe_load(fm_match.group(1)) or {}
    body = raw[fm_match.end() :]

    # --- Split body on bare section headings ---
    sections: dict[str, str] = {}
    parts = _SECTION_HEADING_RE.split(body)
    # parts[0] is text before the first heading (ignored); then alternating name/content pairs
    it = iter(parts[1:])
    for section_name, section_body in zip(it, it, strict=False):
        sections[section_name.strip()] = section_body.strip()

    # --- Validate required sections ---
    for required in _REQUIRED_BODY_SECTIONS:
        if required not in sections:
            raise ValueError(f"Synthesis format file '{path.name}' is missing required body section: # {required}")

    # --- Merge frontmatter + body sections into the model ---
    data = {**frontmatter, **{k: v for k, v in sections.items() if k in _REQUIRED_BODY_SECTIONS}}
    return SynthesisFormat.model_validate(data)


def load_all_formats() -> dict[str, "SynthesisFormat"]:
    """Scan ``synthesis_formats/*.md``, parse each file, and return ``{id: SynthesisFormat}``.

    On parse failure, logs the filename and re-raises so misconfigured format
    files are surfaced immediately at startup rather than silently omitted.

    Returns:
        Mapping from format id to ``SynthesisFormat``.

    Raises:
        ValueError: If any format file fails to parse.
        pydantic.ValidationError: If any format file has invalid field values.
    """
    registry: dict[str, SynthesisFormat] = {}
    for md_path in sorted(_FORMATS_DIR.glob("*.md")):
        try:
            fmt = _parse_format_file(md_path)
            registry[fmt.id] = fmt
            logger.info("Loaded synthesis format: %s (%s)", fmt.id, md_path.name)
        except Exception as exc:
            logger.error("Failed to load synthesis format from %s: %s", md_path.name, exc)
            raise
    return registry


@lru_cache(maxsize=1)
def get_format_registry() -> Mapping[str, "SynthesisFormat"]:
    """Return the memoized synthesis format registry as a read-only mapping.

    Calls ``load_all_formats()`` on the first invocation and caches the result.
    Subsequent calls return the same ``MappingProxyType`` view so external
    callers cannot mutate the shared cached dict.

    Returns:
        Read-only mapping from format id to ``SynthesisFormat``.
    """
    return MappingProxyType(load_all_formats())


def get_format(format_id: str) -> "SynthesisFormat":
    """Look up a synthesis format by id, raising ``ValueError`` if not found.

    Args:
        format_id: The ``id`` field of the desired format (e.g. ``"collaborative_story"``).

    Returns:
        The matching ``SynthesisFormat``.

    Raises:
        ValueError: If ``format_id`` is not in the registry, with the registered ids listed.
    """
    registry = get_format_registry()
    if format_id not in registry:
        registered = sorted(registry.keys())
        raise ValueError(f"Unknown synthesis format '{format_id}'. Registered formats: {registered}")
    return registry[format_id]
