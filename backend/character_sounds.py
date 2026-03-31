"""Character & environment sound library — loads YAML config, validates cues, formats for prompts."""

import random
from functools import lru_cache
from pathlib import Path

import yaml

try:
    from .schemas.turn_response import CharacterSfxCue
except ImportError:
    from schemas.turn_response import CharacterSfxCue

_DATA_PATH = Path(__file__).parent / "data" / "character_sounds.yaml"

# Max 2 cues: 1 character intro + 1 ambient overlay
_MAX_CUES_PER_TURN = 2
_AMBIENT_CATEGORIES = {"environment", "nature"}


@lru_cache(maxsize=1)
def load_character_sound_library() -> dict[str, list[dict]]:
    """Load and cache the character sound YAML config.

    Returns:
        Mapping of activity_type to list of sound definitions.
    """
    with open(_DATA_PATH) as f:
        data = yaml.safe_load(f) or {}
    return {activity: entry.get("sounds", []) for activity, entry in data.items()}


def validate_character_sfx(
    activity_type: str,
    cues: list[CharacterSfxCue],
) -> list[CharacterSfxCue]:
    """Validate cue IDs against activity's library.

    Drops invalid cue IDs (LLM hallucinations), normalises timing values,
    and caps at MAX_CUES_PER_TURN.
    """
    library = load_character_sound_library()
    sounds_by_id = {s["id"]: s for s in library.get(activity_type, [])}
    result: list[CharacterSfxCue] = []
    for cue in cues:
        sound = sounds_by_id.get(cue.cue)
        if not sound:
            continue
        # Character sounds → intro (plays before narrator voice-acts the same sound)
        # Environment/nature sounds → overlay (plays during speech as atmosphere)
        timing = "overlay" if sound["category"] in _AMBIENT_CATEGORIES else "intro"
        result.append(CharacterSfxCue(cue=cue.cue, timing=timing))
        if len(result) >= _MAX_CUES_PER_TURN:
            break
    return result


def pick_fallback_cue(activity_type: str) -> list[CharacterSfxCue]:
    """Pick a safe ambient overlay when the LLM returns no cues.

    Only picks low-energy environment/nature sounds as overlays — never
    character reaction sounds (barks, roars, etc.) since those need
    conversational context to feel natural.
    """
    library = load_character_sound_library()
    sounds = library.get(activity_type, [])
    if not sounds:
        return []

    # Only use ambient sounds for fallback — character sounds without context feel random
    ambient_categories = {"environment", "nature"}
    ambient_sounds = [s for s in sounds if s.get("category") in ambient_categories]
    if not ambient_sounds:
        return []

    picked = random.choice(ambient_sounds)
    return [CharacterSfxCue(cue=picked["id"], timing="overlay")]


def get_sound_list_for_prompt(activity_type: str) -> str:
    """Format the available sounds as a text block for prompt injection.

    Includes sound ID, category, and energy so the LLM can reason
    about variety and intensity matching.
    """
    library = load_character_sound_library()
    sounds = library.get(activity_type, [])
    if not sounds:
        return "No character sounds available for this activity."

    lines = []
    for s in sounds:
        line = f"- {s['id']}  — use when: {s['when']}" if s.get("when") else f"- {s['id']}"
        lines.append(line)
    return "\n".join(lines)
