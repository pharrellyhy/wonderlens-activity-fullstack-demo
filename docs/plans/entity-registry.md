# Entity Registry — Consolidate Scattered Entity Config

## Context

Adding a new entity currently requires editing 5-6 files with hardcoded dicts that must stay in sync (`scenarios.py`, `recipe_loader.py`, `server.py`, recipe JSON, `PhotoSelector.jsx`). No validation catches missing pieces. This plan consolidates entity config into a single registry module with startup validation.

## Approach

Create `backend/entity_registry.py` — a Python module with Pydantic models that is the single source of truth for all entity configuration. Other modules import from it instead of maintaining their own dicts. Frontend reads entity list from a new `/api/entities` endpoint.

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/entity_registry.py` | **CREATE** — registry module with all entity config |
| `backend/scenarios.py` | Modify — replace `_ENTITY_SCENARIO_MAP` and `SCENARIO_CATEGORIES` with registry imports |
| `backend/recipe_loader.py` | Modify — remove 4 hardcoded dicts, use registry accessors |
| `backend/server.py` | Modify — remove `COLLECTION_CATALOGS` + `generate_round_items()`, add `/api/entities`, add startup validation |
| `frontend/src/components/PhotoSelector.jsx` | Modify — fetch from `/api/entities` instead of hardcoding |
| `tests/test_entity_registry.py` | **CREATE** — registry tests |
| `tests/test_api.py` | Modify — add `/api/entities` test |

## Task 1: Create `backend/entity_registry.py`

Define Pydantic models:

```python
class CollectionItem(BaseModel):
    id: str
    label: str
    image: str  # e.g. "/icons/spotted_mushroom.png"

class CollectionCatalog(BaseModel):
    correct: list[CollectionItem]
    distractors: list[CollectionItem]

class EntityConfig(BaseModel):
    activity_type: str              # "mood_changer_dog"
    category: str                   # "category_1" or "category_5"
    entity_name: str                # "dog"
    demo_filename: str              # "dog.png"
    display_label: str              # "Stuffed Dog" (for frontend)
    icon_src: str                   # "/icons/dog.png"
    keywords: list[str]             # ["dog", "puppy", "stuffed dog", "toy dog"]
    feature_keywords: list[str]     # ["plush", "stuffed", "toy"] — for fuzzy matching
    creative_slots: Cat1CreativeSlots | Cat5CreativeSlots
    collection_catalog: CollectionCatalog | None = None  # cat5 only
```

Populate `ENTITY_REGISTRY: list[EntityConfig]` with all 5 entities (data copied from existing scattered dicts).

Build derived lookup helpers at module load time:
- `get_entity(activity_type) -> EntityConfig`
- `get_creative_slots(activity_type) -> CreativeSlots`
- `get_collection_catalog(activity_type) -> CollectionCatalog | None`
- `is_demo_entity(filename) -> bool`
- `entity_name_for_filename(filename) -> str`
- `keyword_to_activity_type(keyword) -> str | None`
- `all_entities_for_api() -> dict` — structured for frontend consumption

Move `generate_round_items()` here from `server.py` (it operates purely on catalog data).

Add `validate_registry()` — checks that every registered entity has a recipe JSON and scenario YAML on disk, cat5 entities have collection catalogs, and all entities have keywords.

## Task 2: Update `backend/scenarios.py`

- Remove `_ENTITY_SCENARIO_MAP` dict (lines 19-35)
- Remove `SCENARIO_CATEGORIES` dict (lines 38-44)
- Import keyword map and categories from `entity_registry`
- Re-export `SCENARIO_CATEGORIES` for backward compatibility (used by `director.py`, `pipeline.py`, `recipe_loader.py`)
- Update `match_scenario()` to use registry keyword map
- Update feature-based matching (lines 71-78) to use `EntityConfig.feature_keywords` from registry

## Task 3: Update `backend/recipe_loader.py`

- Remove `_DEMO_FILENAMES`, `_FILENAME_ENTITIES`, `_CAT1_SLOTS`, `_CAT5_SLOTS` (lines 31-91)
- Remove `is_demo_entity()` function (lines 94-96)
- Import `is_demo_entity`, `entity_name_for_filename`, `get_creative_slots`, `get_category` from `entity_registry`
- Update `recipe_to_session_state()` to use registry accessors instead of local dicts
- Keep `load_instruction_recipe()` unchanged — recipe JSON files stay as separate concern

## Task 4: Update `backend/server.py`

- Remove `COLLECTION_CATALOGS` dict (lines 122-159)
- Remove `generate_round_items()` function (lines 162-181)
- Import `generate_round_items` from `entity_registry`
- Update `is_demo_entity` import: from `entity_registry` instead of `recipe_loader`
- Add `GET /api/entities` endpoint (returns categories + photos for frontend)
- Call `validate_registry()` in `lifespan()` startup

## Task 5: Update `frontend/src/components/PhotoSelector.jsx`

- Replace hardcoded `CATEGORIES` array with API fetch to `/api/entities`
- `useEffect` on mount → fetch → setState
- Keep current hardcoded array as fallback if fetch fails
- Loading state while fetching

## Task 6: Tests

- Create `tests/test_entity_registry.py`:
  - All entities have required fields
  - Lookup functions return correct results
  - `validate_registry()` passes
  - `generate_round_items()` returns correct structure
  - Cat5 entities have collection catalogs
- Add `/api/entities` endpoint test to `tests/test_api.py`
- Run existing test suite — no tests should break since `SCENARIO_CATEGORIES` is re-exported

## Import Dependency Graph (no cycles)

```
schemas.creative_slots (leaf)
     ↑
entity_registry ← scenarios.py ← recipe_loader.py
     ↑                              ↑
     └──────── server.py ───────────┘
```

`agents/director.py` and `agents/pipeline.py` import `SCENARIO_CATEGORIES` from `scenarios.py` — unchanged (re-exported).

## After This Change: Adding a New Entity

1. Add one `EntityConfig` to `ENTITY_REGISTRY` in `entity_registry.py`
2. Create `backend/recipes/{activity_type}.json`
3. Create `backend/scenarios/{activity_type}.yaml`
4. Add icon to `frontend/public/icons/`
5. Start server — `validate_registry()` catches anything missing

**4 artifacts instead of 5-6 scattered dicts, with startup validation.**

## Verification

```bash
cd backend
uv run pytest ../tests/ -v          # all tests pass
uv run ruff check .                 # lint clean
uv run ruff format --check .        # format clean
uv run mypy .                       # types check
uv run uvicorn server:app --port 8000  # server starts (validation passes)
curl http://localhost:8000/api/entities  # returns entity list
```

Frontend: open http://localhost:5173, verify PhotoSelector loads entities from API.
