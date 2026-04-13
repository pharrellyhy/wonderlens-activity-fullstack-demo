"""Synthesis format registry — data-driven Cat5 synthesis format definitions.

Format files live in backend/synthesis_formats/*.md.  Import this package to
load and access registered formats.

Exports:
    SynthesisFormat  — Pydantic model for one format's metadata and prompts.
    get_format       — Look up a format by id; raises ValueError if not found.
    get_format_registry — Return the memoized {id: SynthesisFormat} mapping.
    load_all_formats — Load all *.md files and return the mapping (uncached).
"""

from .loader import SynthesisFormat, get_format, get_format_registry, load_all_formats

__all__ = [
    "SynthesisFormat",
    "get_format",
    "get_format_registry",
    "load_all_formats",
]
