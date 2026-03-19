# Plan: Game MD Files as Single Source of Truth for Demo Entities

## Context

Demo entity data is currently spread across 3 manually-synced sources: `entity_registry.py` (hardcoded config), `recipes/*.json` (step instructions + screen frames), and `scenarios/*.yaml` (interaction scripts). Adding or modifying a game requires updating all three. This plan consolidates everything into a single markdown file per game with YAML frontmatter, so that adding a new demo game = creating one MD file.

## Decisions Made

- **Scope:** Replace all 3 sources for demo entities. Live pipeline (custom photo uploads) unchanged.
- **Parsing:** YAML frontmatter parsed into existing Pydantic models at server startup.
- **Games:** Migrate existing 5 demo entities. Other 25 `*_prod.md` files remain design docs.
- **File naming:** `{activity_type}.md` (e.g., `mood_changer_dog.md`). Photo derived from `entity_name` field in frontmatter → `{entity_name}.png`.
- **Keywords/vision matching:** Not needed for demo entities (fixed photo filenames).

## MD File Format

Each demo game MD file has YAML frontmatter (all structured data) + prose body (human-readable documentation, not parsed):

```markdown
---
activity_type: mood_changer_dog
entity_name: dog
category: category_1
display_label: Stuffed Dog
tier: T0
ib_theme: "Who We Are"
ib_key_concept: Perspective
concepts_earned: [Perspective]
photo_features: [floppy ears, soft fur, cute face, fluffy body]

creative_slots:
  game_mechanic: voice_acting
  metaphor: "This fluffy dog friend has so many feelings inside!"
  role_title: Emotion Translator
  round_scenarios:
    - warm sunshine on belly
    - tripped and went bump
    - favorite treat arrives
  escalation_axis: comfortable to excited
  observation_detail: "those cute floppy ears and super soft fur"

step_instructions:
  hook:
    goal: "React with wonder to the stuffed dog..."
    constraint: "T0 max 2 sentences..."
    emotion_tag: excited
  transition:
    goal: "Introduce the voice_acting game..."
    constraint: "T0 max 3 sentences..."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Set the scene vividly: warm sunshine..."
      scenario: "Morning! The warm sunshine lands on the doggy's belly..."
      constraint: "T0 max 2 sentences..."
      emotion_tag: warm
      acceptable_themes: [happy, cozy, warm, comfy, nice, sleepy, relaxed]
      escalation_note: "comfortable, familiar - easiest round"
    - round_number: 2
      ...
    - round_number: 3
      ...
  celebrate:
    goal: "Award the child the title 'Emotion Translator'..."
    constraint: "T0 max 2 sentences..."
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: Perspective..."
    constraint: "T0 max 2 sentences..."
    emotion_tag: warm
  early_exit:
    goal: "Gentle goodbye..."
    constraint: "T0 max 2 sentences..."
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Photo of the stuffed dog with soft golden glow"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Your Fluffy Friend"
    animation_label: "Sparkle highlight"
  - widget: character_display
    ...

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Emotion Translator"
    concepts: [Perspective]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Mood Changer

### A. Basic Info
(human-readable table — not parsed)

### B. Activity Overview
(prose — not parsed)

### C. Interaction Flow
(example dialogues — not parsed)
```

For Cat5 entities, the frontmatter additionally includes:
- `creative_slots.observation_angle`, `collection_criterion`, `collection_count`, `mission_metaphor`, `synthesis_type`, `stuck_hint`, `naming_prompt`
- `collection_catalog.correct[]` and `collection_catalog.distractors[]` with `id`, `label`, `image` per item
- `step_instructions.synthesis` step goal

## Implementation Steps

### Step 1: Create `backend/game_parser.py` (new)

Pure parsing module, no side effects.

```
parse_game_file(path: Path) -> tuple[EntityConfig, InstructionRecipe]
```

Logic:
1. Read file content, split on first `---` pair to extract YAML frontmatter
2. `yaml.safe_load()` the frontmatter into a dict
3. Build `EntityConfig` from top-level fields + `creative_slots`:
   - Derive `demo_filename` from `entity_name` → `{entity_name}.png`
   - Derive `icon_src` from `entity_name` → `/icons/{entity_name}.png`
   - Set `keywords` and `feature_keywords` to empty lists (not needed for demo entities)
   - Determine Cat1 vs Cat5 creative slots from `category` field
   - Parse `collection_catalog` if present (Cat5 only)
4. Build `InstructionRecipe` from `step_instructions`, `screen_frames`, `celebration_frame`, and metadata fields:
   - `activity_type` from frontmatter
   - `metadata` = `RecipeMetadata(tier, ib_theme, ib_key_concept, concepts_earned, round_count=len(rounds))`
   - `step_instructions` = `StepInstruction` validated from frontmatter dict
   - `screen_frames` = list of `ScreenFrame` from frontmatter
   - `celebration_frame` = `ScreenFrame` from frontmatter
   - `photo_features` from frontmatter
   - `collection_items` from `collection_catalog` if Cat5

Reuse existing models:
- `backend/schemas/step_instruction.py` → `StepGoal`, `RoundInstruction`, `StepInstruction`
- `backend/schemas/visual_composition.py` → `ScreenFrame`
- `backend/schemas/recipe.py` → `InstructionRecipe`, `RecipeMetadata`
- `backend/schemas/creative_slots.py` → `Cat1CreativeSlots`, `Cat5CreativeSlots`
- `backend/entity_registry.py` → `EntityConfig`, `CollectionItem`, `CollectionCatalog`

### Step 2: Create 5 demo game MD files in `backend/games/`

Mechanical data migration — combine data from 3 current sources into one MD file per entity:

- `backend/games/mood_changer_dog.md`
- `backend/games/dream_whisperer_cat.md`
- `backend/games/time_machine_dinosaur.md`
- `backend/games/polka_dot_patrol.md`
- `backend/games/fluffy_expedition_dandelion.md`

Data sources for each:
- Entity config fields → from `entity_registry.py` ENTITY_REGISTRY list
- Step instructions + screen frames + metadata → from `backend/recipes/{activity_type}.json`
- Prose sections (B, C) → write new or adapt from existing similar `*_prod.md` files

### Step 3: Create `backend/game_loader.py` (new)

Module-level loader that scans `backend/games/` at import time.

```python
_GAMES_DIR = Path(__file__).parent / "games"

_entity_configs: dict[str, EntityConfig] = {}
_instruction_recipes: dict[str, InstructionRecipe] = {}

def _load_demo_games() -> None:
    """Scan games/ for MD files with YAML frontmatter, parse and register."""
    for md_path in sorted(_GAMES_DIR.glob("*.md")):
        text = md_path.read_text()
        if not text.startswith("---"):
            continue  # Skip prose-only design docs (no frontmatter)
        entity_config, recipe = parse_game_file(md_path)
        _entity_configs[entity_config.activity_type] = entity_config
        _instruction_recipes[entity_config.activity_type] = recipe

_load_demo_games()

def get_demo_entities() -> list[EntityConfig]: ...
def get_demo_recipe(activity_type: str) -> InstructionRecipe | None: ...
```

Key behavior: files without `---` frontmatter are silently skipped (the 25 existing `*_prod.md` design docs).

### Step 4: Modify `backend/entity_registry.py`

- Remove the hardcoded `ENTITY_REGISTRY` list (lines 63-202)
- Import `get_demo_entities()` from `game_loader`
- Populate `ENTITY_REGISTRY` from `game_loader.get_demo_entities()`
- All public API functions remain unchanged (they read from `ENTITY_REGISTRY` and derived lookups)
- `validate_registry()` checks for game MD files instead of recipe JSON + scenario YAML

### Step 5: Modify `backend/recipe_loader.py`

- `load_instruction_recipe()` checks `game_loader.get_demo_recipe(activity_type)` first
- Falls back to JSON file for non-demo entities (if any in future)
- Eventually remove JSON fallback after confirming all demo entities work from MD

### Step 6: Tests

- `backend/tests/test_game_parser.py` — Parse each of the 5 demo MD files, assert output matches current hardcoded data from entity_registry + recipe JSONs
- Run existing tests (`uv run pytest`) to confirm zero behavioral regression

### Step 7: Cleanup

- Delete 5 demo recipe JSON files from `backend/recipes/` (keep `polka_dot_patrol_hard.json` if it's separate)
- Delete 5 demo scenario YAML files from `backend/scenarios/` (keep variant files like `_silent_exit`, `_hard`)
- Remove hardcoded entity data from `entity_registry.py`

## Files to Create

| File | Purpose |
|------|---------|
| `backend/game_parser.py` | Parse MD frontmatter → EntityConfig + InstructionRecipe |
| `backend/game_loader.py` | Scan games/, load demo entities at startup |
| `backend/games/mood_changer_dog.md` | Demo game: stuffed dog (Cat1, voice_acting) |
| `backend/games/dream_whisperer_cat.md` | Demo game: cat (Cat1, storytelling_chain) |
| `backend/games/time_machine_dinosaur.md` | Demo game: dinosaur (Cat1, voice_acting) |
| `backend/games/polka_dot_patrol.md` | Demo game: ladybug (Cat5, comparison_chart) |
| `backend/games/fluffy_expedition_dandelion.md` | Demo game: dandelion (Cat5, naming_story) |
| `backend/tests/test_game_parser.py` | Golden-snapshot parser tests |

## Files to Modify

| File | Change |
|------|--------|
| `backend/entity_registry.py` | Remove hardcoded ENTITY_REGISTRY, import from game_loader |
| `backend/recipe_loader.py` | Check game_loader before JSON fallback |

## Files to Delete (Step 7)

| File | Reason |
|------|--------|
| `backend/recipes/mood_changer_dog.json` | Replaced by MD |
| `backend/recipes/dream_whisperer_cat.json` | Replaced by MD |
| `backend/recipes/time_machine_dinosaur.json` | Replaced by MD |
| `backend/recipes/polka_dot_patrol.json` | Replaced by MD |
| `backend/recipes/fluffy_expedition_dandelion.json` | Replaced by MD |

## Unchanged

- All Pydantic schemas in `backend/schemas/`
- Agent modules (`director.py`, `script_agent.py`, `visual_agent.py`, `recipe_assembler.py`)
- `backend/server.py` — endpoints unchanged, same function calls
- Step instruction fragments (`backend/skills/step_instructions/`)
- Frontend (zero changes)
- Live pipeline for custom photo uploads
- Existing 25 `*_prod.md` design docs in `backend/games/` (no frontmatter, skipped by loader)
- Non-demo scenario variants (`_silent_exit.yaml`, `_hard.yaml`)

## Verification

1. **Parse test:** `uv run pytest backend/tests/test_game_parser.py -v` — confirm each MD produces identical EntityConfig + InstructionRecipe as current hardcoded data
2. **Lint/type check:** `uv run ruff check . && uv run mypy .`
3. **Full test suite:** `uv run pytest` — zero regressions
4. **Manual smoke test:** Start backend (`uv run uvicorn server:app --reload --port 8000`), start frontend (`npm run dev`), select each of the 5 demo photos, verify activity runs normally with correct dialogue, screen frames, and celebration
5. **Validate registry:** Confirm `validate_registry()` passes at server startup (logged on boot)
