# Synthesis Format Registry — Data-Driven Game Expansion

**Date:** 2026-04-10
**Status:** Draft — not implemented
**Worktree:** `.worktrees/feat/edu-content-feedback`
**Branch:** `feat/edu-content-feedback`

---

## TL;DR

Today, adding a new Cat5 synthesis format (e.g. `timeline_reveal`, `sorting_challenge`) requires Python edits in 5+ files. This plan refactors the code so **adding a format = dropping one markdown file** into `backend/synthesis_formats/{format_id}.md` with no Python changes required.

The two existing formats (`collaborative_story` for dandelion, `comparison_reveal` for ladybug) get migrated 1:1 to the new system. A third format is added at the end purely via markdown as the proof.

---

## Context (read this first if you're a fresh session)

**Project:** WonderLens Activity Demo. Multi-agent pipeline generates a Cat5 scavenger-hunt activity. After collecting items (STEP_3_COLLECT_1..N), children reach a synthesis step (STEP_4_SYNTHESIS) where the AI produces narration + images summarizing what they found.

**Two synthesis formats exist today**, selected per-game via YAML frontmatter in `backend/games/*.md`:

1. **`collaborative_story`** (e.g. `backend/games/fluffy_expedition_dandelion.md`) — generates a 3-scene story with characters who have names + traits. Delivered scene-by-scene with an image per scene.
2. **`comparison_reveal`** (e.g. `backend/games/polka_dot_patrol.md`) — generates 1 "reveal" scene showing all items side-by-side, narrating how they differ on a dimension (the "observation angle"). The child doesn't name items here; they describe observations.

Both formats end with a generated achievement image at STEP_5_CELEBRATE / STEP_6_CLOSING.

**The synthesis flow end-to-end:**

1. Last collection round advances to STEP_4_SYNTHESIS (`synthesis_phase="invite"` is skipped; phase is set directly to `"evaluate"`).
2. Child says "yes" / "sure" → Turn Director fast-path → `action=advance`.
3. `_resolve_turn_with_directive` at STEP_4_SYNTHESIS → calls `_loading_result(state)` which shows `story_loading` widget + sets `synthesis_phase="generate"` + returns `auto_advance=True`.
4. Next turn arrives → `core.py` bypass sees `synthesis_phase="generate"` → calls `_resolve_synthesis_turn` → calls the inner `_generate_and_advance()`.
5. `_generate_and_advance()` chooses structured generator by format:
   - `collaborative_story` → `_generate_structured_story` (3 scenes)
   - otherwise → `_generate_comparison_reveal` (1 scene)
6. Result is a `StructuredStory` pydantic model with N scenes + an achievement image data URL.
7. `_deliver_scene(state, 1)` delivers scene 1. Each scene auto-advances to the next. The final scene advances state to STEP_5_CELEBRATE.
8. Celebrate/closing read `state.structured_story.achievement_image_data_url` to show the achievement image.

**Key terminology:**
- **Synthesis format** = the shape of the synthesis output (scene count, narrative style, image composition).
- **Creative slots** = Director Agent's per-session output bundled into `Cat5CreativeSlots`. Contains a `story_scaffold` sub-object with `synthesis_format`.
- **Observation angle** = the dimension children observe across collected items (color, pattern, texture, etc.) — a field on `Cat5CreativeSlots`.
- **Story scaffold** = `StoryScaffold` pydantic model, a sub-object of `Cat5CreativeSlots` that includes `synthesis_format`, `premise`, `synthesis_goal`, `story_themes`.
- **Cat5** = "Category 5" out-of-device collection activities. All synthesis format work is Cat5-only; Cat1 (in-device verbal) is out of scope.

---

## Problem — where the branching lives today

Exhaustive list of every place synthesis format is hardcoded. Each of these is a thing a fresh format currently has to touch.

### 1. `backend/schemas/creative_slots.py:31`

```python
synthesis_format: Literal["collaborative_story", "comparison_reveal", "sorting_challenge"] = Field(
    description="Structural format for synthesis"
)
```

A new format must extend this Literal. A runtime-registry check can replace this with `str` + validation at session start.

### 2. `backend/turn_handling/synthesis.py`

Two full generator functions with prompts embedded in Python f-strings:

- **`_generate_structured_story` (lines 133–235)**: 3-scene story prompt. Key sections:
  - Lines 158–161: system prompt.
  - Lines 163–185: user prompt with hardcoded SCENE STRUCTURE (Opening + Surprise, Try and Struggle, Breakthrough + Warm Ending) and RULES.
  - Lines 195–205: LLM call, `max_tokens=2048`.
  - Line 220: hardcoded `len(story.scenes) != 3` check.
  - Lines 224–233: image generation, always 3 scene descs + 1 achievement.

- **`_generate_comparison_reveal` (lines 238–346)**: 1-scene reveal prompt. Key sections:
  - Lines 264–267: system prompt.
  - Lines 269–290: user prompt with NARRATION RULES, REVEAL IMAGE, ACHIEVEMENT IMAGE.
  - Lines 300–309: LLM call, `max_tokens=1024`.
  - Lines 331–334: image generation, 1 scene + 1 achievement.

- **`_generate_and_advance` inside `_resolve_synthesis_turn` (lines ~417–480 after latest edits)**: branches on `is_story`:

```python
is_story = bool(scaffold and scaffold.synthesis_format == "collaborative_story")
if is_story:
    structured = await _generate_structured_story(state)
else:
    structured = await _generate_comparison_reveal(state)
```

- **`_MIN_STORY_SENTENCES` constant (line 59)**: `{"T0": 7, "T1": 9, "T2": 12}` — only applied when `is_story` is True. Non-story formats skip the length regeneration loop.

- **`_SYNTHESIS_INVITE_TEMPLATES` (lines 53–57)**: 3 story-centric templates ("make up a little story about {names}"). Not used by comparison format at all (comparison has its own invite direction built in directive.py fast-path).

### 3. `backend/turn_handling/directive.py`

- **`_build_story_direction` (lines 104–209)**: 100-line function with `if synthesis_format == "collaborative_story": ... else: ...` split. Both branches build the response direction the Speaker reads. The `else` branch (lines 171–207) handles comparison_reveal/sorting_challenge.
  - Line 123: `synthesis_format = scaffold.synthesis_format if scaffold else "collaborative_story"`
  - Line 133: `if synthesis_format == "collaborative_story":`

- **Fast-path synthesis invite (lines 365–403)**: branches on `is_story_game`:
  - Line 373: `is_story_game = scaffold and scaffold.synthesis_format == "collaborative_story"`
  - Lines 375–387: different direction text for story vs comparison.

- **Fast-path confirm at STEP_4_SYNTHESIS (lines ~304–344)**: `if is_story_game and state.synthesis_phase not in ("child_try", "theme_choice", "generate"):` routes story games to `child_try` (inviting the child to try making a story first). Comparison games skip straight to generate.

- **Detail phase non-answer handling (lines 629–635)**: `if scaffold and scaffold.synthesis_format != "collaborative_story": is_naming_game = False` — controls whether the detail phase asks for a name or just an observation.

- **Synthesis advance handler (lines ~928–940)** in `_resolve_turn_with_directive`: calls `_loading_result(state)` unconditionally. No branching here (good), but this is where the registry needs to be accessible when the loader reports an invalid format.

### 4. `backend/turn_handling/helpers.py`

- `_MIN_STORY_SENTENCES` is actually in `synthesis.py` (see above), but helpers.py has related behavior in `_get_screen_frame` and response type helpers that assume the synthesis flow produces widgets matching a specific naming convention. Should not need changes, but verify.

### 5. `backend/skills/step_instructions/cat5_step4_synthesis__*.md`

These are ScriptAgent prompt fragments (different code path — the ScriptAgent is used as the fallback when structured JSON generation fails). Naming pattern today:

```
backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md
backend/skills/step_instructions/cat5_step4_synthesis__comparison_reveal.md  (if it exists)
```

**Decision:** these stay separate from the new `synthesis_formats/` directory for now. They serve the monolithic ScriptAgent fallback path, not the direct JSON-mode generators. Revisit after the format registry lands if the two paths converge.

### 6. `backend/schemas/structured_story.py`

Already flexible — `scenes: list[StoryScene]` accepts any count. The docstring on line 17 (after the 2026-04-10 edit) mentions "3 for story, 1 for comparison reveal" — update when a new scene count lands.

---

## Goals & non-goals

### Goals

1. **Adding a new synthesis format requires zero Python changes in the common case.** A content author drops a markdown file and optionally a game YAML.
2. **Existing behavior for collaborative_story and comparison_reveal is preserved byte-for-byte** (LLM prompts, invite direction, fast-path routing, scene count, image aspect ratios).
3. **Invalid formats fail loud at session start**, not mid-turn — unknown `synthesis_format` in a game YAML should raise at session creation with a clear error listing registered formats.
4. **The refactor is incremental** — each phase is independently shippable and revertible.

### Non-goals

- **Not touching Cat1** (in-device verbal games) — scope is Cat5 synthesis only.
- **Not changing the game YAML format** — games stay as `backend/games/*.md` with their current frontmatter schema. They just reference `synthesis_format` by id (they already do).
- **Not merging ScriptAgent step instructions** (`skills/step_instructions/*.md`) with the new format files.
- **Not adding hot-reload** for format files. Restart the dev server, same as game YAML changes today.
- **Not adding a templating engine** (Jinja). Use Python `str.format` with a fixed variable vocabulary. Escalate to Jinja only if a future format genuinely needs conditionals.
- **Not refactoring animation/sfx cues** out of `backend/state_machine.py`. Stays as-is.
- **Not rewriting the frontend.** It already consumes `StructuredStory` generically.

---

## Design

### Format file specification

**Path:** `backend/synthesis_formats/{format_id}.md`

**Shape:** YAML frontmatter (config) + named markdown sections (prompts and templates). Sections are separated by `^# section_name$` lines. Unknown sections are ignored.

#### Example: `backend/synthesis_formats/collaborative_story.md` (full migration of today's code)

```markdown
---
id: collaborative_story
display_name: "Collaborative Story"

# Scene delivery config
scene_count: 3
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"

# LLM request config
max_tokens: 2048
temperature: 0.7

# Narration constraints
min_sentences_total:
  T0: 7
  T1: 9
  T2: 12

# Direction builder config (used by directive.py speaker direction)
direction_max_sentences:
  T0: 8
  T1: 11
  T2: 14
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"

# Fast-path behavior flags (used by directive.py fast paths)
is_naming_game: true              # detail phase collects a name after the description
confirm_goes_to: "child_try"      # at invite, "yes" → invite child to try story first
supports_delegation: true         # honor "you tell me" → skip to generate

# Fast-path templates (rendered with template variables — see below)
invite_templates:
  - "[gentle] Would you like to make up a little story about {names}?"
  - "[curious] What if {names} went on an adventure? Would you like to tell that story?"
  - "[whispering] I wonder what {names} would do together... would you like to imagine?"

# Fast-path invite direction (used when fast-path returns stay/invite)
invite_direction: |
  Invite the child to make up a little story about {names}.
  Keep it warm and simple — ask if they'd like to imagine what {names} might do together.
---

# system_prompt
You are a warm storyteller for young children.
Generate a structured 3-scene story as a JSON object. Output ONLY valid JSON.

# user_prompt
Characters: {characters}
Sensory details the child shared: {details}
Tier: {tier}
Child's story attempt to expand (if any): {child_story}

Generate a JSON object with this EXACT structure:
{{"scenes": [
  {{"narration": "Scene 1 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}},
  {{"narration": "Scene 2 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}},
  {{"narration": "Scene 3 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}}
], "achievement_description": "All characters together in a warm celebratory scene"}}

SCENE STRUCTURE:
Scene 1 — Opening + Surprise: Set the scene. Something unexpected happens.
Scene 2 — Try and Struggle: A character tries to solve it. It doesn't work. Another has an idea.
Scene 3 — Breakthrough + Warm Ending: They figure it out together. End with comfort.

RULES:
- Use ALL characters by name. Every character appears in at least 2 scenes.
- Start scene 1 narration with an emotion tag like [gentle] or [warm].
- Real emotions (scared, proud, cozy), real dialogue in quotes.
- Warm ending on comfort, not excitement.
- Image descriptions: watercolor storybook style. Characters are NOT human — they are the actual items listed above (petals, caterpillars, moss, seeds, etc.) drawn as cute animated versions. Include character names + physical traits, mood/lighting cues, no text in images.
- Achievement description: show ALL characters together in a warm scene.

# direction_template
Tell a COMPLETE story about {chars_desc}. The story must have:
- BEGINNING: Set the scene. The characters are together and something happens{theme_suffix}.
- MIDDLE: Each character uses their special trait to help. Show what each one DOES, not just what they are.
- END: The problem is solved and the friends celebrate together.

{premise_line}{child_story_line}
Length: {tier_sentences} sentences. Do NOT end with a question. End the story with a warm conclusion.
```

Note the `{{ }}` escape for literal braces in the JSON example — that's how Python `str.format` handles them.

#### Example: `backend/synthesis_formats/comparison_reveal.md`

```markdown
---
id: comparison_reveal
display_name: "Comparison Reveal"

scene_count: 1
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"

max_tokens: 1024
temperature: 0.7

min_sentences_total:
  T0: 3
  T1: 3
  T2: 3

direction_max_sentences:
  T0: 6
  T1: 8
  T2: 11
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"

is_naming_game: false
confirm_goes_to: "generate"
supports_delegation: true

invite_templates:
  - "[curious] Would you like to see how the {obs_angle} looks different on each one?"

invite_direction: |
  Invite the child to compare all their finds together.
  Ask if they'd like to see how the {obs_angle} looks different on each one.
---

# system_prompt
You are a warm guide for young children exploring patterns and observations.
Generate a JSON object. Output ONLY valid JSON.

# user_prompt
Items collected: {items}
Observation angle: {obs_angle}
Details the child noticed: {details}
Tier: {tier}

Generate a JSON object with this EXACT structure:
{{"scenes": [
  {{"narration": "Comparison text (3-5 sentences)", "image_description": "Reveal image description under 50 words"}}
], "achievement_description": "Achievement image description under 50 words"}}

NARRATION RULES:
- Start with an emotion tag like [excited] or [curious]
- Help the child compare the {obs_angle} across all {count} items
- Point out how the {obs_angle} looks different on each
- Reference the child's observations when possible
- 3-5 warm sentences, end with celebration (not a question)

REVEAL IMAGE: Watercolor storybook illustration showing all {count} items ({items}) arranged side by side in a row, each clearly showing their different {obs_angle}. Soft pastel tones, warm lighting. No text in image.

ACHIEVEMENT IMAGE: Watercolor celebratory scene with all {count} items ({items}) grouped together as friends who explored together. Warm lighting, storybook style. No text in image.

# direction_template
Guide a fun comparison of all the finds. Observations collected: {obs_list}.
Help the child see how the same thing ({obs_angle}) looks DIFFERENT on each item.{theme_suffix}{sorting_suffix}{goal_suffix}

Then invite the child to give each find a fun creative name (e.g. 'Freckle Stone', 'Polka Petal').
Length: {tier_sentences} sentences. End warmly — do NOT end with a question.
```

**Notice the unified JSON output shape.** Both formats now return `{"scenes": [...], "achievement_description": "..."}` — the comparison format just has `scenes` of length 1. This means the loader + generator code can be format-agnostic. The previous `comparison_reveal` return shape (`narration` + `reveal_description` + `achievement_description` at the top level) was a special case that complicated the code.

### Template variable vocabulary

Every template in every format file uses these keys with `str.format`. This is the **contract** between format files and the loader.

| Variable | Type | Built from | Example |
|---|---|---|---|
| `{characters}` | str | story_elements mapped to `"{name} ({trait})"`, else collected_names, else "the collected friends" | `"Peter (soft), Sam (wiggly)"` |
| `{chars_desc}` | str | same as `{characters}` | (same) |
| `{items}` | str | `", ".join(p.replace("_", " ") for p in collected_photos)` | `"speckled leaf, circle flower"` |
| `{count}` | int | `len(collected_photos)` | `3` |
| `{names}` | str | `", ".join(collected_names)` or "the friends" | `"Peter, Sam, Moss"` |
| `{details}` | str | `"; ".join(collected_details)` or "no details" | `"soft; fluffy; wiggly"` |
| `{obs_list}` | str | `"; ".join(f"Find {i+1}: {d}" for i, d in enumerate(collected_details))` | `"Find 1: big; Find 2: small"` |
| `{obs_angle}` | str | `state.creative_slots.observation_angle` (Cat5) or `"feature"` | `"pattern"` |
| `{tier}` | str | `state.tier` | `"T1"` |
| `{tier_sentences}` | str | `direction_tier_sentences[tier]` from format config | `"6-10"` |
| `{theme}` | str | chosen_theme or random from scaffold.story_themes or "" | `"One friend can't sleep..."` |
| `{theme_suffix}` | str | `f" ({theme})"` if theme else `""` | `" (One friend can't sleep)"` |
| `{premise_line}` | str | `f"Premise: {scaffold.premise}. Goal: {scaffold.synthesis_goal}.\n"` if scaffold else `""` | `"Premise: ...\n"` |
| `{child_story}` | str | `state.synthesis_child_story or "none"` | `"Sam flies in the wind"` |
| `{child_story_line}` | str | f'The child tried to tell a story: "{child_story}". Weave their idea into the story...\n' if child_story else "" | (long sentence) |
| `{sorting_suffix}` | str | `f" Sort by: {sorting_criterion}."` if sorting_criterion else `""` | `" Sort by: size."` |
| `{goal_suffix}` | str | `f"\nGoal: {scaffold.synthesis_goal}. "` if scaffold else `""` | `"\nGoal: ..."` |
| `{child_story_for_weave}` | str | `f' The child tried: "{child_story}". Weave it in.'` or `""` | |

**Rule:** all variables always exist in the render dict (never `KeyError`). Suffix variables are empty strings when not applicable. The format file decides whether to use them.

**Why suffix variables instead of conditionals?** No templating engine. `str.format` is dumb. Having `{theme_suffix}` in the template lets the format file place the optional text without needing `{% if theme %}`.

### `SynthesisFormat` pydantic model

**New file:** `backend/synthesis_formats/loader.py`

```python
"""Loader + registry for synthesis format markdown files."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

try:
    from ..logger import setup_logger
except ImportError:
    from logger import setup_logger

logger = setup_logger(__name__)

_FORMATS_DIR = Path(__file__).parent


class SynthesisFormat(BaseModel):
    """A synthesis format loaded from a markdown file."""

    # --- Frontmatter config ---
    id: str
    display_name: str

    scene_count: int = Field(ge=1, le=5)
    scene_aspect_ratio: str = "16:9"
    achievement_aspect_ratio: str = "1:1"

    max_tokens: int = 2048
    temperature: float = 0.7

    min_sentences_total: dict[str, int]       # tier -> min sentence count
    direction_max_sentences: dict[str, int]   # tier -> max_sentences for directive
    direction_tier_sentences: dict[str, str]  # tier -> "6-10" style hint

    is_naming_game: bool = True
    confirm_goes_to: Literal["child_try", "generate"] = "child_try"
    supports_delegation: bool = True

    invite_templates: list[str]
    invite_direction: str

    # --- Body sections (raw strings, rendered with str.format at call time) ---
    system_prompt: str
    user_prompt: str
    direction_template: str


def _parse_format_file(path: Path) -> SynthesisFormat:
    """Parse a single synthesis format markdown file.

    File structure:
        ---
        <yaml frontmatter>
        ---

        # section_name_1
        <section body>

        # section_name_2
        <section body>
    """
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")

    _, frontmatter_yaml, rest = text.split("---\n", 2)
    frontmatter = yaml.safe_load(frontmatter_yaml) or {}

    # Parse body sections: split on ^# section_name$
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for line in rest.splitlines():
        if line.startswith("# ") and " " not in line[2:]:
            # Flush previous section
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = line[2:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()

    required_sections = ("system_prompt", "user_prompt", "direction_template")
    for name in required_sections:
        if name not in sections:
            raise ValueError(f"{path}: missing required section '# {name}'")

    return SynthesisFormat(
        **frontmatter,
        system_prompt=sections["system_prompt"],
        user_prompt=sections["user_prompt"],
        direction_template=sections["direction_template"],
    )


def load_all_formats() -> dict[str, SynthesisFormat]:
    """Scan synthesis_formats/*.md and parse each."""
    registry: dict[str, SynthesisFormat] = {}
    for path in sorted(_FORMATS_DIR.glob("*.md")):
        try:
            fmt = _parse_format_file(path)
            registry[fmt.id] = fmt
            logger.info("Loaded synthesis format: %s (%d scenes)", fmt.id, fmt.scene_count)
        except Exception as exc:
            logger.error("Failed to load synthesis format %s: %s", path.name, exc)
            raise
    return registry


@lru_cache(maxsize=1)
def get_format_registry() -> dict[str, SynthesisFormat]:
    return load_all_formats()


def get_format(format_id: str) -> SynthesisFormat:
    registry = get_format_registry()
    if format_id not in registry:
        raise ValueError(
            f"Unknown synthesis_format: {format_id!r}. "
            f"Registered formats: {sorted(registry.keys())}"
        )
    return registry[format_id]
```

### Variable builder

Put the template variable construction in one place so every code site uses identical keys.

**New function in `backend/turn_handling/synthesis.py`:**

```python
def _build_template_variables(
    state: SessionStateModel,
    fmt: SynthesisFormat,
    *,
    chosen_theme: str = "",
) -> dict[str, str | int]:
    """Build the canonical template variable dict for a format render."""
    slots = state.creative_slots if isinstance(state.creative_slots, Cat5CreativeSlots) else None
    scaffold = slots.story_scaffold if slots else None

    items = [p.replace("_", " ") for p in state.collected_photos]
    items_str = ", ".join(items) if items else "the finds"
    count = len(state.collected_photos)

    # Characters (story mode): map names to item types
    char_parts: list[str] = []
    for i, name in enumerate(state.collected_names):
        photo_id = state.collected_photos[i] if i < len(state.collected_photos) else ""
        item_type = photo_id.replace("_", " ") if photo_id else "unknown creature"
        char_parts.append(f"{name} (a {item_type})")
    characters = ", ".join(char_parts) if char_parts else "the characters"

    # Story elements -> chars_desc for direction template
    chars_desc_parts = [
        f"{e.character_name or f'Friend {e.round_number}'} ({e.trait_or_detail or 'soft'})"
        for e in state.story_elements
    ]
    chars_desc = ", ".join(chars_desc_parts) if chars_desc_parts else (
        ", ".join(state.collected_names) if state.collected_names else "the collected friends"
    )

    details = "; ".join(state.collected_details) if state.collected_details else "no details"
    obs_list = "; ".join(
        f"Find {i+1}: {e.trait_or_detail or e.child_words or f'find {i+1}'}"
        for i, e in enumerate(state.story_elements)
    ) if state.story_elements else (
        "; ".join(state.collected_details) if state.collected_details else "the collected finds"
    )

    obs_angle = slots.observation_angle if slots else "feature"
    sorting_criterion = slots.sorting_criterion if slots else ""
    theme = chosen_theme
    if not theme and scaffold and scaffold.story_themes:
        import random
        theme = random.choice(scaffold.story_themes)

    tier_sentences = fmt.direction_tier_sentences.get(state.tier, "6-10")
    child_story = state.synthesis_child_story or "none"

    return {
        # Core
        "characters": characters,
        "chars_desc": chars_desc,
        "items": items_str,
        "count": count,
        "names": ", ".join(state.collected_names) if state.collected_names else "the friends",
        "details": details,
        "obs_list": obs_list,
        "obs_angle": obs_angle,
        "tier": state.tier,
        "tier_sentences": tier_sentences,
        "theme": theme,
        "child_story": child_story,

        # Optional suffixes — empty string when not applicable
        "theme_suffix": f" ({theme})" if theme else "",
        "premise_line": (f"Premise: {scaffold.premise}. Goal: {scaffold.synthesis_goal}.\n" if scaffold else ""),
        "child_story_line": (
            f'\nThe child tried to tell a story: "{state.synthesis_child_story}". '
            f"Weave their idea into the story — honor what they said and expand it.\n"
            if state.synthesis_child_story else ""
        ),
        "sorting_suffix": f" Sort by: {sorting_criterion}." if sorting_criterion else "",
        "goal_suffix": f"\nGoal: {scaffold.synthesis_goal}. " if scaffold else "",
        "child_story_for_weave": (
            f' The child tried: "{state.synthesis_child_story}". Weave it in.'
            if state.synthesis_child_story else ""
        ),
    }
```

**Move the `random` import to the top of the file.** Inline imports inside functions violate `CLAUDE.md` ("All imports at the top of the file").

### Generic generator

Replaces `_generate_structured_story` + `_generate_comparison_reveal`.

**New function in `synthesis.py`:**

```python
async def _generate_structured_output(
    state: SessionStateModel,
    fmt: SynthesisFormat,
) -> StructuredStory | None:
    """Format-agnostic structured generation.

    Renders fmt.system_prompt + fmt.user_prompt with state-derived variables,
    calls the LLM in JSON mode, parses into StructuredStory, then generates
    scene images + achievement image using fmt.scene_aspect_ratio and
    fmt.achievement_aspect_ratio.
    """
    settings = get_settings()
    variables = _build_template_variables(state, fmt)

    try:
        system_prompt = fmt.system_prompt.format(**variables)
        user_prompt = fmt.user_prompt.format(**variables)
    except KeyError as exc:
        logger.error("Format %s template missing variable: %s", fmt.id, exc)
        return None

    try:
        start = time.perf_counter()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=fmt.temperature,
            max_tokens=fmt.max_tokens,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )
        raw_text = response.choices[0].message.content or ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Synthesis LLM [%s] response (%dms): %s", fmt.id, latency_ms, raw_text[:200])

        raw = json.loads(raw_text)
        story = StructuredStory.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Failed to parse %s JSON: %s", fmt.id, exc)
        return None
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        logger.error("%s LLM call failed: %s", fmt.id, exc)
        return None

    if len(story.scenes) != fmt.scene_count:
        logger.warning(
            "Format %s: expected %d scenes, got %d — falling back",
            fmt.id, fmt.scene_count, len(story.scenes),
        )
        return None

    # Generate images (N scene descriptions + 1 achievement) in parallel
    scene_descs = [s.image_description for s in story.scenes]
    scene_images, achievement_image = await generate_scene_images(
        scene_descs, story.achievement_description, session_id=state.session_id
    )
    for i, scene in enumerate(story.scenes):
        scene.image_data_url = scene_images[i] if i < len(scene_images) else None
    story.achievement_image_data_url = achievement_image

    return story
```

**`_generate_and_advance` becomes:**

```python
async def _generate_and_advance() -> TurnResult:
    state.synthesis_phase = "generate"

    format_id = _resolve_format_id(state)
    fmt = get_format(format_id)

    structured = await _generate_structured_output(state, fmt)
    if structured and structured.scenes:
        state.structured_story = structured
        state.current_scene = 1
        state.synthesis_phase = "scene_1"
        return _deliver_scene(state, 1)

    # Monolithic ScriptAgent fallback (unchanged)
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)

    # Length check uses format's min_sentences_total
    min_sentences = fmt.min_sentences_total.get(state.tier, 6)
    sentences = [s.strip() for s in re.split(r"[.!?]+", turn_response.dialogue) if s.strip()]
    if len(sentences) < min_sentences:
        logger.warning(
            "Synthesis [%s] too short (%d sentences, need %d), regenerating",
            fmt.id, len(sentences), min_sentences,
        )
        hint = ConversationTurn(
            role="child",
            text=f"[system: Output is too short. Generate at least {min_sentences} sentences.]",
            step=state.current_step,
        )
        state.conversation_history.append(hint)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        state.conversation_history = [t for t in state.conversation_history if t != hint]

    return _synthesis_result(
        state,
        turn_response,
        advance=True,
        debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
    )
```

**`_resolve_format_id` helper** (in synthesis.py):

```python
def _resolve_format_id(state: SessionStateModel) -> str:
    """Get the format id from creative_slots, defaulting to collaborative_story."""
    if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
        return state.creative_slots.story_scaffold.synthesis_format
    return "collaborative_story"
```

### Directive.py changes

**`_build_story_direction` becomes:**

```python
def _build_story_direction(state: SessionStateModel, chosen_theme: str = "") -> tuple[str, int]:
    """Build response direction using the format's direction_template."""
    from .synthesis import _build_template_variables, _resolve_format_id  # avoid circular import at module level
    from ..synthesis_formats.loader import get_format

    fmt = get_format(_resolve_format_id(state))
    variables = _build_template_variables(state, fmt, chosen_theme=chosen_theme)
    direction = fmt.direction_template.format(**variables)
    max_s = fmt.direction_max_sentences.get(state.tier, 11)
    return direction, max_s
```

**Note:** the cross-module imports need to be top-of-file per CLAUDE.md. The example above shows in-function imports only to avoid a circular-import pitfall; refactor the module structure (e.g., move `_build_template_variables` and `_resolve_format_id` into a new `turn_handling/synthesis_common.py`) to keep all imports at the top. Check at implementation time whether the circular import is actually real.

**Fast-path synthesis invite (directive.py:365–403) becomes:**

```python
if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "invite":
    fmt = get_format(_resolve_format_id(state))
    variables = _build_template_variables(state, fmt)
    direction = fmt.invite_direction.format(**variables)
    state.synthesis_phase = "evaluate"
    state.synthesis_prompt_count += 1
    logger.info(
        "turn_director: step=%s action=stay (fast-path invite) format=%s",
        state.current_step, fmt.id,
    )
    return TurnDirective(
        action="stay",
        reasoning="Synthesis invite phase — asking child before generating.",
        response_direction=direction,
        emotion_tag="gentle",
        stay_on_step=True,
        max_sentences=2,
    )
```

**Fast-path confirm at STEP_4_SYNTHESIS (directive.py:304–344):** replace `is_story_game` check with `fmt.confirm_goes_to`:

```python
if state.current_step == "STEP_4_SYNTHESIS":
    if state.synthesis_phase == "invite":
        return None

    fmt = get_format(_resolve_format_id(state))
    if fmt.confirm_goes_to == "child_try" and state.synthesis_phase not in ("child_try", "theme_choice", "generate"):
        state.synthesis_phase = "child_try"
        variables = _build_template_variables(state, fmt)
        names = variables["names"]
        direction = (
            f"The child wants a story about {names}! "
            f"Encourage the child to try making one up. "
            f"Ask: what happens to {names}? "
            f"Keep it simple and inviting — they can say anything."
        )
        return TurnDirective(
            action="stay",
            reasoning="Child confirmed synthesis. Inviting them to try a story first.",
            response_direction=direction,
            emotion_tag="excited",
            stay_on_step=True,
            max_sentences=2,
        )

    # Fallback: generate directly
    story_dir, max_s = _build_story_direction(state)
    return TurnDirective(
        action="advance",
        reasoning="Generating synthesis output.",
        response_direction=story_dir,
        emotion_tag="playful",
        max_sentences=max_s,
    )
```

**Detail phase naming check (directive.py:629–635):**

```python
fmt = get_format(_resolve_format_id(state))
is_naming_game = fmt.is_naming_game
```

### Creative slots schema change

`backend/schemas/creative_slots.py:31`:

```python
# BEFORE
synthesis_format: Literal["collaborative_story", "comparison_reveal", "sorting_challenge"] = Field(...)

# AFTER
synthesis_format: str = Field(description="Structural format id — must be registered in synthesis_formats/")
```

Add session-start validation in `backend/server.py` (or wherever `creative_slots` is finalized):

```python
from synthesis_formats.loader import get_format
# At session init, after creative_slots is built:
if isinstance(creative_slots, Cat5CreativeSlots) and creative_slots.story_scaffold:
    get_format(creative_slots.story_scaffold.synthesis_format)  # raises ValueError if unknown
```

This preserves fail-fast behavior without needing the Literal.

---

## Migration phases

Each phase is a single PR / commit. Tests must pass at every phase boundary. Revert to the previous phase must be a pure `git revert`.

### Phase 1 — Loader scaffolding (no behavior change)

**Adds:**
- `backend/synthesis_formats/__init__.py`
- `backend/synthesis_formats/loader.py` (full implementation above)
- `backend/tests/test_synthesis_format_loader.py` — unit tests parsing a fixture file

**Fixture:** `backend/tests/fixtures/synthesis_formats/test_format.md` — a minimal valid format file used by tests only.

**Verification:**
```bash
cd backend
uv run pytest tests/test_synthesis_format_loader.py -v
uv run ruff check synthesis_formats/
uv run mypy synthesis_formats/
```

**Nothing else changes.** No existing code imports the loader. Behavior identical. Purpose: land the infrastructure in isolation.

### Phase 2 — Migrate `collaborative_story.md`, wire registry for story only

**Adds:**
- `backend/synthesis_formats/collaborative_story.md` (full format file above, migrated byte-for-byte from `synthesis.py:158–185`)
- `_build_template_variables` and `_resolve_format_id` in `synthesis.py` (or extract to `turn_handling/synthesis_common.py` if circular imports bite)
- `_generate_structured_output` in `synthesis.py`

**Changes:**
- `_generate_and_advance` branches: if `is_story`, call `_generate_structured_output(state, get_format("collaborative_story"))` instead of `_generate_structured_story`. Comparison path untouched.
- Add a unit test that renders `collaborative_story.md`'s prompts with a sample state and diffs against the pre-refactor Python f-string output. Bytes must match.

**Does NOT change:**
- `_generate_structured_story` still exists (unused by the story path but kept as a safety net). Delete in phase 3.
- `_generate_comparison_reveal` unchanged.
- `directive.py` unchanged.
- `creative_slots.py` still has the Literal.

**Verification:**
```bash
cd backend
uv run pytest tests/ --ignore=tests/test_ai_quality.py -v
uv run ruff check .
```

**E2E check:** start a dandelion session, run through the flow, verify 3 scene images render and the achievement image appears at celebrate. Compare LLM responses to a pre-refactor baseline (capture 3 runs before starting phase 2 and 3 runs after — the prompts must be textually identical at the wire).

### Phase 3 — Migrate `comparison_reveal.md`, delete old generators

**Adds:**
- `backend/synthesis_formats/comparison_reveal.md`

**Changes:**
- `_generate_and_advance` always uses `_generate_structured_output(state, get_format(_resolve_format_id(state)))` — no branching.
- Delete `_generate_structured_story` (synthesis.py:133–235).
- Delete `_generate_comparison_reveal` (synthesis.py:238–346).
- Delete `_MIN_STORY_SENTENCES` constant (use `fmt.min_sentences_total` instead).

**Verification:**
```bash
cd backend
uv run pytest tests/ --ignore=tests/test_ai_quality.py -v
uv run ruff check .
```

**E2E check:** run ladybug (polka_dot_patrol) game through synthesis. Verify 1 reveal image + achievement image. Run dandelion again to confirm story path still works.

### Phase 4 — Refactor directive.py fast paths

**Changes:**
- `_build_story_direction` (directive.py:104–209) → uses `fmt.direction_template.format(**variables)`. Delete the `if synthesis_format == "collaborative_story": ... else: ...` split.
- Fast-path synthesis invite (directive.py:365–403) → uses `fmt.invite_direction` and `fmt.invite_templates`.
- Fast-path confirm at STEP_4_SYNTHESIS (directive.py:304–344) → uses `fmt.confirm_goes_to`.
- Detail phase naming check (directive.py:629–635) → uses `fmt.is_naming_game`.

**Verification:**
```bash
cd backend
uv run pytest tests/ --ignore=tests/test_ai_quality.py -v
uv run ruff check turn_handling/directive.py
uv run mypy turn_handling/directive.py
```

**E2E check:** run both games. Verify invite language, confirm routing (story goes to `child_try`, comparison goes straight to generate), and detail-phase behavior (story asks for names; comparison doesn't) are all unchanged from phase 3.

### Phase 5 — Drop the Literal enum

**Changes:**
- `backend/schemas/creative_slots.py:31` — replace `Literal[...]` with `str`.
- `backend/server.py` (or wherever `creative_slots` is finalized in session start) — add a registry-validation call that raises on unknown format.

**Verification:**
- Try starting a session with a game YAML that has `synthesis_format: nonexistent` — should fail at session start with a clear error naming the available formats.
- Existing games still work.

```bash
cd backend
uv run pytest tests/ --ignore=tests/test_ai_quality.py -v
uv run mypy .
```

### Phase 6 — Add a third format as proof (markdown only)

**Choose a format.** Candidates:
- `sorting_challenge` — 1 scene showing items sorted by a criterion.
- `timeline_reveal` — 1 scene showing items in an order with labels.

**Adds:**
- `backend/synthesis_formats/sorting_challenge.md` (or chosen format)
- Optionally, `backend/games/<new_game>.md` that uses the new format.

**Does NOT change:** any Python file. If this phase requires a Python edit, the refactor in phases 1–5 was incomplete.

**Verification:** start a session for the new game, run through to synthesis, verify behavior matches the format file.

---

## Test strategy

### Unit tests to add

- `tests/test_synthesis_format_loader.py`:
  - Parses a valid fixture file → correct `SynthesisFormat` instance.
  - Fixture missing `---` frontmatter → raises `ValueError`.
  - Fixture missing a required section (e.g. `# user_prompt`) → raises `ValueError`.
  - Fixture with unknown `confirm_goes_to` value → pydantic validation error.
  - `get_format("unknown")` → `ValueError` listing registered ids.
  - Registry is populated with `collaborative_story` and `comparison_reveal` after phases 2–3.

- `tests/test_template_variables.py`:
  - Given a synthetic `SessionStateModel`, `_build_template_variables` produces exact expected values for every key.
  - Missing `collected_names` → `characters` defaults to "the characters".
  - Missing scaffold → `premise_line`, `goal_suffix` are empty strings.
  - Missing `story_elements` → `chars_desc` falls back to `collected_names`.

- `tests/test_format_rendering.py`:
  - Render `collaborative_story.md` system_prompt + user_prompt with a sample state.
  - Compare byte-for-byte against a golden file captured from the pre-refactor `_generate_structured_story` output.
  - Do the same for `comparison_reveal.md`.

### Golden-file baseline (capture BEFORE phase 2)

```bash
# On main (pre-refactor), run the generators with a fixed sample state
# and save their prompts to disk.
cd backend
uv run python -c "
from turn_handling.synthesis import _generate_structured_story
# ... monkey-patch to print the prompt instead of calling the LLM ...
" > tests/fixtures/golden/story_prompt_before.txt
```

These goldens ensure zero prompt drift during migration.

### E2E tests

`tests/test_ai_quality.py` already runs end-to-end against a live backend for both games. Run it after every phase (requires `uvicorn server:app` in another terminal):

```bash
cd backend
uv run uvicorn server:app --port 8000 &  # or in a separate terminal
uv run pytest tests/test_ai_quality.py -v
```

Capture the final JSON recipes and diff them across phases — the recipes should be identical pre- and post-refactor for phases 2–4.

### Lint / type / format

After every phase:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest tests/ --ignore=tests/test_ai_quality.py
```

All must pass. No `# noqa` or `# type: ignore` per CLAUDE.md.

---

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Prompt drift during migration changes LLM behavior | Medium | High — may silently degrade story quality | Golden-file tests diff rendered prompts byte-for-byte against pre-refactor baselines. E2E runs capture 3 sessions per format pre- and post-migration. |
| Circular imports between `directive.py` ↔ `synthesis.py` ↔ `synthesis_formats.loader` | Medium | Medium — blocks clean import layout | Extract `_build_template_variables` and `_resolve_format_id` into a new `turn_handling/synthesis_common.py` that neither directive nor synthesis import each other through. |
| Template `str.format` crashes on missing variable | High | Low — fail-fast at render time | Wrap `.format(**variables)` in `try/except KeyError` with a clear log. Add a rendering test that uses every key in the vocabulary. |
| `str.format` conflicts with literal braces in JSON examples | Medium | Low — easy fix with `{{` / `}}` | Documented in the format file spec section. Add a test that renders `collaborative_story.md` and checks the output is valid JSON example syntax. |
| Unknown format in an existing game YAML during phase 5 | Low | Medium — session start fails | Phase 5 runs session validation in CI for all `backend/games/*.md` before merge. |
| Content author writes a format with invalid pydantic config | Medium | Low — fails at startup with pydantic error | Loader logs which file failed and re-raises. |

---

## Open questions

1. **Should `is_naming_game` be per-format or per-game?** Today it's derived from `synthesis_format == "collaborative_story"`, which means all story games are naming games and all comparison games aren't. Is there a future game where this decoupling matters? If yes, move `is_naming_game` to `Cat5CreativeSlots` instead of the format file.

2. **What does `invite_templates` (the list) vs `invite_direction` (the string) actually control?** Today `_SYNTHESIS_INVITE_TEMPLATES` in synthesis.py is referenced by `_synthesis_invite_prompt` in the non-directive code path. `invite_direction` is what the directive fast path uses. Verify whether both paths are actually live (the directive path is feature-flagged by `settings.turn_director_enabled`). If the non-directive path is dead code, simplify by only keeping `invite_direction`.

3. **Do step instructions move?** `backend/skills/step_instructions/cat5_step4_synthesis__*.md` feed the ScriptAgent (monolithic fallback path). They duplicate some of what the format file now holds. Decision deferred to post-refactor review — revisit once phases 1–5 land.

4. **Should the format file include image style guidance as a separate section?** Today both formats inline the style directly in the user prompt. A dedicated `# image_style` section would let non-prompt code (e.g. image_gen.py) apply a global style prefix. Deferred — not needed for format parity.

5. **Does the game YAML `synthesis_format` field name stay?** Yes — no reason to rename.

---

## File layout after refactor

```
backend/
├── synthesis_formats/                   # NEW
│   ├── __init__.py
│   ├── loader.py                        # SynthesisFormat, _parse_format_file, get_format
│   ├── collaborative_story.md           # migrated from synthesis.py:158-185
│   └── comparison_reveal.md             # migrated from synthesis.py:264-290
├── turn_handling/
│   ├── synthesis.py                     # ~200 lines smaller; one generic generator
│   ├── synthesis_common.py              # NEW if needed for circular-import break
│   ├── directive.py                     # ~50 lines smaller; no is_story_game branching
│   └── ...
├── schemas/
│   ├── creative_slots.py                # Literal → str + runtime validation
│   └── structured_story.py              # unchanged
├── games/                               # unchanged
│   ├── polka_dot_patrol.md              # still references synthesis_format: comparison_reveal
│   └── fluffy_expedition_dandelion.md   # still references synthesis_format: collaborative_story
└── tests/
    ├── test_synthesis_format_loader.py  # NEW
    ├── test_template_variables.py       # NEW
    ├── test_format_rendering.py         # NEW with golden files
    └── fixtures/
        ├── synthesis_formats/
        │   └── test_format.md           # NEW — unit test fixture
        └── golden/
            ├── story_prompt_before.txt  # NEW — captured pre-refactor
            └── comparison_prompt_before.txt
```

---

## Success criteria

1. **`backend/synthesis_formats/sorting_challenge.md` can be added in phase 6 with zero Python changes**, and the game using it works end-to-end (loading screen → scenes → achievement image → celebrate → closing).
2. **`grep -rn "collaborative_story" backend/` returns only:** the format file, game YAMLs, and the fallback default in `_resolve_format_id`. No business logic branches remain.
3. **`grep -rn "is_story_game" backend/` returns nothing.**
4. **`grep -rn 'synthesis_format ==' backend/` returns nothing.**
5. **Golden-file prompt diffs are zero bytes** across phases 2–4 for both existing formats.
6. **Full test suite passes** after every phase: `uv run pytest tests/ --ignore=tests/test_ai_quality.py` (479 tests as of 2026-04-10).
7. **Lint, format, and type checks pass:** `uv run ruff check . && uv run ruff format --check . && uv run mypy .`
8. **Session start fails fast** for unknown `synthesis_format` values with an error message naming all registered formats.

---

## Reference: exact file paths and line numbers (2026-04-10 snapshot)

For a fresh-session executor — these are the lines to touch. Line numbers will drift; use the functions/strings as anchors.

| What | File | Lines | Anchor |
|---|---|---|---|
| `synthesis_format` Literal | `backend/schemas/creative_slots.py` | 31 | `synthesis_format: Literal[...]` |
| `_generate_structured_story` | `backend/turn_handling/synthesis.py` | 133–235 | `async def _generate_structured_story` |
| `_generate_comparison_reveal` | `backend/turn_handling/synthesis.py` | 238–346 | `async def _generate_comparison_reveal` |
| `_generate_and_advance` inner fn | `backend/turn_handling/synthesis.py` | ~417–480 | `async def _generate_and_advance` (inside `_resolve_synthesis_turn`) |
| `_MIN_STORY_SENTENCES` | `backend/turn_handling/synthesis.py` | 59 | `_MIN_STORY_SENTENCES: dict[str, int]` |
| `_SYNTHESIS_INVITE_TEMPLATES` | `backend/turn_handling/synthesis.py` | 53–57 | `_SYNTHESIS_INVITE_TEMPLATES = [` |
| `_build_story_direction` | `backend/turn_handling/directive.py` | 104–209 | `def _build_story_direction` |
| Fast-path confirm at STEP_4 | `backend/turn_handling/directive.py` | 304–344 | `if state.current_step == "STEP_4_SYNTHESIS":` inside `_fast_path_directive` confirm branch |
| Fast-path invite at STEP_4 | `backend/turn_handling/directive.py` | 365–403 | `if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "invite":` in `_get_turn_directive` |
| Detail phase naming check | `backend/turn_handling/directive.py` | 629–635 | `if scaffold and scaffold.synthesis_format != "collaborative_story":` |
| Synthesis advance handler | `backend/turn_handling/directive.py` | ~928–940 | `if state.current_step == "STEP_4_SYNTHESIS":` inside `_resolve_turn_with_directive` advance branch (calls `_loading_result`) |
| `StructuredStory` / `StoryScene` | `backend/schemas/structured_story.py` | 1–27 | whole file |
| `StoryScaffold.synthesis_format` | `backend/schemas/creative_slots.py` | 31 | inside `class StoryScaffold` |
| Game YAMLs referencing formats | `backend/games/polka_dot_patrol.md` | frontmatter `story_scaffold.synthesis_format` | line ~40 |
| Game YAMLs referencing formats | `backend/games/fluffy_expedition_dandelion.md` | frontmatter `story_scaffold.synthesis_format` | line ~40 |

---

## Commands summary for a fresh session

```bash
# Setup
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/edu-content-feedback
git status                           # confirm on feat/edu-content-feedback
cat docs/plans/2026-04-10-synthesis-format-registry.md  # this file

# Capture pre-refactor baselines (Phase 0)
cd backend
uv run pytest tests/ --ignore=tests/test_ai_quality.py -v > /tmp/tests_before.txt
# TODO: add a script to capture rendered prompts from the current generators

# Work through phases 1–6, verifying after each:
uv run pytest tests/ --ignore=tests/test_ai_quality.py -q
uv run ruff check .
uv run ruff format --check .
uv run mypy .

# E2E verification after phases 2, 3, 4 (requires Vertex AI credentials)
uv run uvicorn server:app --port 8000 &
uv run pytest tests/test_ai_quality.py -v
```
