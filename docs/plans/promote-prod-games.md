# Plan: Promote Prod Game Design Docs to Playable Demo Games

## Context

We have 12 `*_prod.md` design docs in `backend/games/` that contain rich pedagogical content (KUD, dialogue trees, screen descriptions) but no YAML frontmatter. They can't be loaded as playable demo games. Meanwhile, the 5 existing demo games prove the MD-with-frontmatter pattern works. The goal is to make it easy to promote any prod design doc into a playable demo by adding frontmatter — ideally with a script that extracts what it can from the prose and scaffolds the rest.

## Problem

Manually writing ~110 lines of YAML frontmatter per game is tedious and error-prone. The prod docs already contain most of the data needed (tier, IB concepts, game style, round scenarios, dialogue), but in prose form — not structured YAML. A conversion tool would:
1. Parse the existing prose tables and sections
2. Generate frontmatter with sensible defaults
3. Flag fields that need human input (entity photos, collection catalogs, keywords)

## Scope

- **Build:** A CLI script `scripts/generate_game_frontmatter.py` that reads a `*_prod.md` file and outputs a complete MD file with YAML frontmatter + original prose
- **Schema updates:** Add `prediction_game` and `helper_hotline` to `Cat1CreativeSlots.game_mechanic` Literal type (used by 3 prod games)
- **Do NOT** auto-promote all 12 games — the script generates a draft that a human reviews before it becomes a live demo
- **Do NOT** modify existing demo games or the parser/loader infrastructure

## Data Mapping: Prose → Frontmatter

Fields extractable from the prod MD prose tables:

| Frontmatter Field | Source in Prod MD | Extraction Method |
|---|---|---|
| `activity_type` | Filename stem (e.g. `lion_cat5_prod` → `brave_things_hunt_lion`) | Derive from Activity Name + entity |
| `entity_name` | Filename stem (e.g. `lion_cat5_prod` → `lion`) | Parse from filename |
| `category` | Activity Category row | `"Collection/Tracking" → "category_5"`, `"Sustained Verbal" → "category_1"` |
| `display_label` | Entity name, capitalized | Derive from entity_name |
| `tier` | Recommended Tier row | Parse `T0`/`T1`/`T2` |
| `ib_theme` | — | Lookup from IB concept → theme mapping |
| `ib_key_concept` | Core IB Key Concepts row (first concept) | Parse |
| `concepts_earned` | Core IB Key Concepts row (all) | Parse as list |
| `creative_slots.game_mechanic` / `synthesis_type` | Game Style row | Direct mapping |
| `creative_slots.role_title` | Step 4/5 text (e.g. "BRAVE SCOUT") | Regex from celebration dialogue |
| `creative_slots.round_scenarios` | Round headers in Step 3 | Parse round titles |

Fields that **cannot** be extracted and need human input:

| Field | Why |
|---|---|
| `keywords` | Not in prose — depends on vision matching strategy |
| `feature_keywords` | Not in prose — depends on photo features |
| `photo_features` | Not in prose — requires actual photo analysis |
| `creative_slots.metaphor` | Could approximate from Step 1 dialogue, but needs review |
| `creative_slots.observation_detail` | Cat1 only — needs photo-specific detail |
| `creative_slots.escalation_axis` | Could approximate from round structure |
| `step_instructions.*` | Goals/constraints must be authored for the LLM, not copied from example dialogue |
| `screen_frames` | Widget/animation/sfx choices are design decisions |
| `celebration_frame` | Badge design decisions |
| `collection_catalog` | Cat5 only — correct items and distractors need curation |

## Implementation

### Step 1: Add missing game mechanics to schema

**File:** `backend/schemas/creative_slots.py`

Add `"prediction_game"` and `"helper_hotline"` to `Cat1CreativeSlots.game_mechanic` Literal type. These are used by `sunflower_cat1_prod.md`, `green_apple_cat1_prod.md`, and `stop_sign_cat1_prod.md`.

### Step 2: Create IB concept → theme lookup

A small mapping dict used by the script:

```python
IB_CONCEPT_TO_THEME = {
    "Perspective": "Who We Are",
    "Reflection": "Who We Are",
    "Change": "How the World Works",
    "Causation": "How the World Works",
    "Form": "How We Express Ourselves",
    "Connection": "Sharing the Planet",
    "Function": "How the World Works",
    "Responsibility": "Sharing the Planet",
}
```

### Step 3: Create `scripts/generate_game_frontmatter.py`

CLI script: `python scripts/generate_game_frontmatter.py backend/games/lion_cat5_prod.md`

Logic:
1. Read the prod MD file
2. Parse the Basic Info table to extract: Activity Name, Activity Category, Tier, IB Concepts, Game Style
3. Derive `entity_name` from filename (strip `_cat[15]_prod`)
4. Derive `category` from Activity Category text
5. Derive `activity_type` from Activity Name (slugify) or prompt user
6. Build a frontmatter template with:
   - Extracted fields filled in
   - Placeholder fields marked with `# TODO` comments
   - Cat1 vs Cat5 creative_slots structure based on category
   - Step instruction stubs with goals/constraints as `# TODO`
   - Screen frame stubs with `# TODO` for widget choices
7. Write output to `backend/games/{activity_type}.md` with frontmatter + original prose body
8. Print a summary of what was extracted vs what needs manual authoring

**Output format:**
```yaml
---
activity_type: brave_things_hunt_lion  # TODO: confirm activity_type
entity_name: lion
category: category_5
display_label: Lion
tier: T0
ib_theme: "How the World Works"  # auto-derived from Form
ib_key_concept: Form
concepts_earned: [Form, Function]
keywords: [lion]  # TODO: add more keywords for vision matching
feature_keywords: []  # TODO: add feature keywords
photo_features: []  # TODO: add visible features from photo

creative_slots:
  observation_angle: form  # TODO: confirm observation angle
  collection_criterion: "Find things that look big, strong, or tough"  # TODO: refine
  collection_count: 2
  mission_metaphor: "You are a Brave Things Scout!"  # extracted from prose
  role_title: Brave Things Scout  # extracted from prose
  synthesis_type: comparison_chart
  stuck_hint: ""  # TODO: write stuck hint
  naming_prompt: ""  # TODO: write naming prompt

step_instructions:
  hook:
    goal: ""  # TODO: write hook goal
    constraint: "T0 max 2 sentences"
    emotion_tag: excited
  # ... (remaining steps as stubs)

screen_frames: []  # TODO: define screen frames

celebration_frame:  # TODO: define celebration frame
  widget: badge_award
  widget_params:
    title: "Brave Things Scout"
    concepts: [Form, Function]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---
(original prose content preserved below)
```

### Step 4: Add step instruction fragment files for new mechanics

For `prediction_game` and `helper_hotline`, create fragment files following the existing pattern:
- `backend/skills/step_instructions/cat1_step2_rules__prediction_game.md`
- `backend/skills/step_instructions/cat1_step3_round__prediction_game.md`
- `backend/skills/step_instructions/cat1_step2_rules__helper_hotline.md`
- `backend/skills/step_instructions/cat1_step3_round__helper_hotline.md`

### Step 5: Frontend updates for new games

When a generated game is reviewed and finalized, these frontend steps are also needed:

1. **Icon file** (required): Place `frontend/public/icons/{entity_name}.png` — this is the photo shown in the selector and sent to `/api/start`
2. **Fallback categories** (required): Add the entity to `FALLBACK_CATEGORIES` in `frontend/src/components/PhotoSelector.jsx` so it appears even if the API fetch fails
3. **React SVG icon** (optional): For category header decoration, create `frontend/src/icons/{EntityName}Icon.jsx`, export in `frontend/src/icons/index.js`, and add to `CATEGORY_ICONS` map in `PhotoSelector.jsx`

Note: the script itself does NOT make these changes — they're manual steps after a game is promoted. The script should print a reminder checklist at the end.

### Step 6: Generate Cat5 collection item icons

For new Cat5 games, each `collection_catalog` entry needs an icon in `frontend/public/icons/`. The existing pipeline uses `scripts/generate_cat5_icons_gemini.py` (which imports `ASSETS` and `build_prompt` from `scripts/generate_cat5_icons_openai.py`).

When the frontmatter script generates a Cat5 game:
1. Add the new game's collection items (correct + distractors) to the `ASSETS` tuple in `scripts/generate_cat5_icons_openai.py`
2. Run `python scripts/generate_cat5_icons_gemini.py --mode auto` to generate the icons
3. Alternatively, the frontmatter script could auto-append `AssetPrompt` entries to the OpenAI script — but this is fragile; better to print a checklist

The frontmatter script should detect Cat5 games and print:
```
Cat5 game detected! After filling in the collection_catalog, you'll need to:
  1. Add collection item prompts to scripts/generate_cat5_icons_openai.py ASSETS
  2. Run: python scripts/generate_cat5_icons_gemini.py --mode auto --overwrite
```

### Step 7: Tests

- Test the script runs on each of the 12 prod files without errors
- Test that output files have valid YAML frontmatter (parseable by `yaml.safe_load`)
- Test that extracted fields match expected values (spot-check 2-3 files)

## Files to Create

| File | Purpose |
|---|---|
| `scripts/generate_game_frontmatter.py` | CLI tool to scaffold frontmatter from prod MD |
| `backend/skills/step_instructions/cat1_step2_rules__prediction_game.md` | Fragment for prediction_game mechanic |
| `backend/skills/step_instructions/cat1_step3_round__prediction_game.md` | Fragment for prediction_game mechanic |
| `backend/skills/step_instructions/cat1_step2_rules__helper_hotline.md` | Fragment for helper_hotline mechanic |
| `backend/skills/step_instructions/cat1_step3_round__helper_hotline.md` | Fragment for helper_hotline mechanic |

## Files to Modify

| File | Change |
|---|---|
| `backend/schemas/creative_slots.py` | Add `prediction_game`, `helper_hotline` to game_mechanic Literal |

## Unchanged

- `backend/game_parser.py`, `backend/game_loader.py`, `backend/entity_registry.py` — no changes needed, already handle any valid frontmatter
- Existing 5 demo game MD files — untouched
- Frontend — zero changes

## Verification

1. `python scripts/generate_game_frontmatter.py backend/games/lion_cat5_prod.md` — produces valid output with extracted fields
2. `python scripts/generate_game_frontmatter.py backend/games/bicycle_cat1_prod.md` — produces valid Cat1 output
3. `uv run ruff check backend/schemas/creative_slots.py` — passes with new mechanic types
4. `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py -v` — existing tests still pass
5. Manual: fill in TODOs for one game (e.g. lion), rename to `brave_things_hunt_lion.md`, restart server → game appears in demo
