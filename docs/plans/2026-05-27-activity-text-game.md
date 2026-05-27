# Activity Text Game Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone backend-backed WonderLens activity text game for 12 exported activities, with text-only child interaction and style-consistent static display assets.

**Architecture:** Add explicit backend activity APIs and recipe definitions, then add a new frontend activity game surface that calls those APIs through `/api/start-activity` and `/api/turn`. Preserve existing Cat1/Cat5 runtime behavior, add the minimum Cat3 build flow for Guided Drawing, and keep static assets visible through committed files plus a manifest.

**Tech Stack:** FastAPI, Pydantic, pytest, React 19, Vite, Vitest, Testing Library, Tailwind CSS 4, Codex internal imagegen.

---

## Preconditions

- Work in this worktree: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game`.
- Do not edit the main checkout or the unrelated dirty `AGENTS.md` there.
- Do not edit or print `backend/.env` or `backend/.elaborate-baton-480304-r8-a8a39bcb34f1.json`.
- For live backend verification, source backend env and set the backend credential JSON path without echoing values.
- Follow TDD for code changes: failing test, minimal implementation, passing test, commit.
- Commit after each completed task with conventional commit format.

## Confirmed Product Rules

- User-facing wording says "activity", not "concept", except for "Core IB Key Concepts".
- V1 child interaction is typed text input and AI text output only.
- No mic, TTS, audio controls, image upload, or camera recognition in this surface.
- Static image/icon assets are in scope, generated with Codex internal imagegen during implementation, committed under project paths, and described by a manifest.
- Runtime must not generate activity display assets invisibly.
- Lens phase images should align to runtime beats, not a fixed count.
- Device frame must preserve the screenshot proportions and include the top-right scroll control.

## Activity Slugs

Use clean product activity slugs for runtime IDs and keep source export IDs as metadata:

| Runtime `activity_type` | Source export ID |
|---|---|
| `activity_phoneme_treasure_hunt` | `concept_phoneme_hunt_collect` |
| `activity_partial_reveal_guess` | `concept_partial_reveal_deduce` |
| `activity_animal_sound_imitation` | `concept_animal_sound_motion_voice` |
| `activity_word_echo_practice` | `concept_word_echo_remember` |
| `activity_emotion_reader` | `concept_emotion_reader_care` |
| `activity_constellation_star_count` | `concept_constellation_star_count_enumerate` |
| `activity_career_decision_role_play` | `concept_career_decision_decide` |
| `activity_vegetable_sort` | `concept_vegetable_sort_sort` |
| `activity_travel_planner` | `concept_travel_planner_predict` |
| `activity_guided_drawing` | `concept_guided_drawing_probe` |
| `activity_story_challenge_unlock` | `concept_story_unlock_probe` |
| `activity_recognition_pop_challenge` | `concept_recognition_pop_probe` |

---

### Task 1: Backend Activity API Contract

**Files:**
- Create: `backend/tests/test_activity_text_game_api.py`
- Modify: `backend/server.py`
- Modify: `backend/entity_registry.py`
- Create: `backend/activity_catalog.py`

**Step 1: Write failing tests for catalog and start endpoint**

Create `backend/tests/test_activity_text_game_api.py`:

```python
from fastapi.testclient import TestClient

from server import app


def test_activity_catalog_returns_exported_activities() -> None:
    client = TestClient(app)

    response = client.get("/api/activities")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 12
    assert body["activities"][0]["kind"] == "activity"
    assert {activity["id"] for activity in body["activities"]} >= {
        "activity_phoneme_treasure_hunt",
        "activity_guided_drawing",
    }
    assert "Choose a concept" not in str(body)


def test_start_activity_rejects_unknown_activity() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/start-activity",
        json={"activity_type": "missing_activity", "tier": "T1", "interaction_mode": "text"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "unknown_activity"
```

**Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py -q
```

Expected: FAIL because `/api/activities` and `/api/start-activity` do not exist.

**Step 3: Implement minimal catalog scaffolding**

Add `backend/activity_catalog.py`:

```python
"""Activity catalog helpers for the standalone activity text game."""

from pydantic import BaseModel, Field

from entity_registry import ENTITY_REGISTRY, EntityConfig


ACTIVITY_TEXT_GAME_SET = "activity_text_game"


class ActivitySummary(BaseModel):
    """Frontend-safe activity metadata."""

    id: str
    kind: str = "activity"
    name: str
    source_export_id: str
    category: str
    mechanic: str
    tier: str
    premise: str
    core_ib_key_concepts: list[str] = Field(default_factory=list)
    asset_manifest_id: str = ""


def is_text_game_activity(entity: EntityConfig) -> bool:
    """Return whether an entity config belongs to the activity text game."""
    return entity.activity_set == ACTIVITY_TEXT_GAME_SET


def activity_summaries() -> list[ActivitySummary]:
    """Return stable activity summaries for the text game frontend."""
    summaries = [
        ActivitySummary(
            id=entity.activity_type,
            name=entity.display_label,
            source_export_id=entity.source_export_id,
            category=entity.category,
            mechanic=entity.mechanic,
            tier=entity.tier,
            premise=entity.plain_description,
            core_ib_key_concepts=entity.concepts_earned,
            asset_manifest_id=entity.activity_type,
        )
        for entity in ENTITY_REGISTRY
        if is_text_game_activity(entity)
    ]
    return sorted(summaries, key=lambda item: item.name)
```

Extend `EntityConfig` in `backend/entity_registry.py` with optional fields:

```python
activity_set: str = ""
source_export_id: str = ""
mechanic: str = ""
```

Update `_build_entity_summary()` to include those fields in returned summaries.

Add endpoints to `backend/server.py`:

```python
class ActivityStartRequest(BaseModel):
    activity_type: str
    tier: str = "T1"
    interaction_mode: str = "text"


@app.get("/api/activities")
async def list_activities() -> JSONResponse:
    summaries = [activity.model_dump() for activity in activity_summaries()]
    return JSONResponse({"count": len(summaries), "activities": summaries})


@app.post("/api/start-activity")
async def start_activity(req: ActivityStartRequest) -> JSONResponse:
    entity_config = get_entity_or_none(req.activity_type)
    if not entity_config or not is_text_game_activity(entity_config):
        return JSONResponse({"error": "unknown_activity"}, status_code=404)
    if req.interaction_mode != "text":
        return JSONResponse({"error": "unsupported_interaction_mode"}, status_code=422)
    return await _start_activity_session(entity_config, req.tier, interaction_mode="text")
```

Refactor the shared body from `/api/start-deep-link` into `_start_activity_session(...)` during Task 3 after activity definitions exist. For this task, it is acceptable for `/api/start-activity` to return 404 for unknown activity only.

**Step 4: Run tests**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py::test_start_activity_rejects_unknown_activity -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/tests/test_activity_text_game_api.py backend/server.py backend/entity_registry.py backend/activity_catalog.py
git commit -m "feat(activity): add catalog API shell"
```

---

### Task 2: Cat3 Schema And State Machine

**Files:**
- Modify: `backend/schemas/creative_slots.py`
- Modify: `backend/schemas/session_state.py`
- Modify: `backend/game_parser.py`
- Modify: `backend/recipe_loader.py`
- Modify: `backend/state_machine.py`
- Modify: `backend/agents/script_agent.py`
- Create: `backend/skills/step_instructions/cat3_step1_hook.md`
- Create: `backend/skills/step_instructions/cat3_step2_setup.md`
- Create: `backend/skills/step_instructions/cat3_step3_build.md`
- Create: `backend/skills/step_instructions/cat3_step4_celebrate.md`
- Create: `backend/skills/step_instructions/cat3_step5_closing.md`
- Test: `backend/tests/test_activity_text_game_cat3.py`

**Step 1: Write failing Cat3 tests**

Create `backend/tests/test_activity_text_game_cat3.py`:

```python
from pathlib import Path

from game_parser import parse_game_file
from state_machine import next_step, step_needs_user_input


def test_cat3_state_machine_steps() -> None:
    assert next_step("STEP_1_HOOK", "cat3", 0, 3) == "STEP_2_SETUP"
    assert next_step("STEP_2_SETUP", "cat3", 0, 3) == "STEP_3_BUILD_1"
    assert next_step("STEP_3_BUILD_1", "cat3", 1, 3) == "STEP_3_BUILD_2"
    assert next_step("STEP_3_BUILD_3", "cat3", 3, 3) == "STEP_4_CELEBRATE"
    assert next_step("STEP_4_CELEBRATE", "cat3", 3, 3) == "STEP_5_CLOSING"
    assert step_needs_user_input("STEP_4_CELEBRATE") is False


def test_guided_drawing_game_parses_as_cat3() -> None:
    path = Path("backend/games/activity_guided_drawing.md")

    entity, recipe = parse_game_file(path)

    assert entity.activity_type == "activity_guided_drawing"
    assert entity.category == "category_3"
    assert entity.creative_slots.game_mechanic == "build"
    assert recipe.metadata.round_count == 3
```

**Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_cat3.py -q
```

Expected: FAIL because `cat3` is not in type literals and the Guided Drawing game file does not exist.

**Step 3: Add Cat3 creative slots**

Extend `backend/schemas/creative_slots.py`:

```python
class Cat3CreativeSlots(BaseModel):
    """Creative slots for Category 3 guided build activities."""

    game_mechanic: Literal["build"] = Field(description="Guided build mechanic")
    metaphor: str = Field(description="Playful frame for the build")
    role_title: str = Field(description="Fun title awarded to the child")
    build_materials: list[str] = Field(default_factory=list, description="Suggested child materials")
    build_steps: list[str] = Field(description="One build step per round")
    escalation_axis: str = Field(description="How the build increases in complexity")
    observation_detail: str = Field(description="Visual or thematic anchor")


CreativeSlots = Union[Cat1CreativeSlots, Cat3CreativeSlots, Cat5CreativeSlots]
```

Update imports and `isinstance` branches in parser/loader/state machine/script agent.

**Step 4: Add Cat3 state machine behavior**

In `backend/state_machine.py`:

```python
CAT3_STEP_1_HOOK = "STEP_1_HOOK"
CAT3_STEP_2_SETUP = "STEP_2_SETUP"
CAT3_STEP_3_BUILD = "STEP_3_BUILD"
CAT3_STEP_4_CELEBRATE = "STEP_4_CELEBRATE"
CAT3_STEP_5_CLOSING = "STEP_5_CLOSING"
```

Add `_next_step_cat3()` and route `next_step(..., template_type="cat3")` to it. Update `_parse_round_step()` to accept `STEP_3_BUILD_`. Update `step_needs_user_input()` so Cat3 celebrate and closing auto-advance. Update `get_screen_frame()` to return a simple `activity_lens` or `character_display` frame for setup/build/celebrate/closing until the frontend lens widget is added.

**Step 5: Add Cat3 script instruction mapping**

In `backend/agents/script_agent.py`, map Cat3 steps:

```python
file_map.update({
    "STEP_2_SETUP": "cat3_step2_setup.md",
})
elif step.startswith("STEP_3_BUILD_"):
    filename = "cat3_step3_build.md"
```

Update template type label:

```python
template_labels = {"cat1": "Category 1", "cat3": "Category 3", "cat5": "Category 5"}
"{template_type}": f"{template_labels.get(state.template_type, 'Category')} ({state.template_type})"
```

**Step 6: Add Cat3 step instruction files**

Keep files concise and generic. Example for `cat3_step3_build.md`:

```markdown
# Cat3 Build Round

Guide one build step from the activity-specific instructions. The child is using typed text to report what they did.
Do not claim to see the drawing or paper. Ask for one short typed confirmation or description.
Keep the current build step visible and end with a simple question.
```

**Step 7: Run tests**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_cat3.py -q
```

Expected: first test passes. The parse test passes after Task 3 adds the Guided Drawing game file; if it still fails because that file is not created yet, mark that assertion as pending in this task and complete it in Task 3.

**Step 8: Commit**

```bash
git add backend/schemas/creative_slots.py backend/schemas/session_state.py backend/game_parser.py backend/recipe_loader.py backend/state_machine.py backend/agents/script_agent.py backend/skills/step_instructions/cat3_step*.md backend/tests/test_activity_text_game_cat3.py
git commit -m "feat(activity): add cat3 flow shell"
```

---

### Task 3: Add 12 Backend Activity Definitions

**Files:**
- Create: `backend/games/activity_phoneme_treasure_hunt.md`
- Create: `backend/games/activity_partial_reveal_guess.md`
- Create: `backend/games/activity_animal_sound_imitation.md`
- Create: `backend/games/activity_word_echo_practice.md`
- Create: `backend/games/activity_emotion_reader.md`
- Create: `backend/games/activity_constellation_star_count.md`
- Create: `backend/games/activity_career_decision_role_play.md`
- Create: `backend/games/activity_vegetable_sort.md`
- Create: `backend/games/activity_travel_planner.md`
- Create: `backend/games/activity_guided_drawing.md`
- Create: `backend/games/activity_story_challenge_unlock.md`
- Create: `backend/games/activity_recognition_pop_challenge.md`
- Modify: `backend/game_parser.py`
- Modify: `backend/entity_registry.py`
- Test: `backend/tests/test_activity_text_game_definitions.py`

**Step 1: Write failing definition tests**

Create `backend/tests/test_activity_text_game_definitions.py`:

```python
from game_loader import get_demo_recipe
from activity_catalog import activity_summaries


EXPECTED_IDS = {
    "activity_phoneme_treasure_hunt",
    "activity_partial_reveal_guess",
    "activity_animal_sound_imitation",
    "activity_word_echo_practice",
    "activity_emotion_reader",
    "activity_constellation_star_count",
    "activity_career_decision_role_play",
    "activity_vegetable_sort",
    "activity_travel_planner",
    "activity_guided_drawing",
    "activity_story_challenge_unlock",
    "activity_recognition_pop_challenge",
}


def test_activity_text_game_definitions_load() -> None:
    summaries = activity_summaries()

    assert {summary.id for summary in summaries} == EXPECTED_IDS
    assert all(summary.kind == "activity" for summary in summaries)
    assert all(summary.source_export_id.startswith("concept_") for summary in summaries)
    assert all(summary.premise for summary in summaries)


def test_each_activity_has_recipe() -> None:
    for activity_id in EXPECTED_IDS:
        recipe = get_demo_recipe(activity_id)
        assert recipe is not None
        assert recipe.metadata.round_count >= 3
```

**Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_definitions.py -q
```

Expected: FAIL because the new game files do not exist.

**Step 3: Extend game parser metadata**

In `backend/game_parser.py`, pass optional metadata into `EntityConfig`:

```python
activity_set=data.get("activity_set", ""),
source_export_id=data.get("source_export_id", ""),
mechanic=data.get("mechanic", data.get("creative_slots", {}).get("game_mechanic", "")),
```

**Step 4: Add game files**

Each file should use existing YAML-frontmatter game format. Required common fields:

```yaml
activity_set: activity_text_game
source_export_id: concept_...
mechanic: ...
activity_type: activity_...
entity_name: activity_...
display_label: Human Activity Name
tier: T1
plain_description: "Premise from the exported spec."
```

Use source package `prod.md` for step goals and rounds:

```bash
BASE=/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/runs/20260521_163621_workbook_review_packet_full/activity_packages
sed -n '1,220p' "$BASE/concept_phoneme_hunt_collect/prod.md"
```

Keep Cat1 mechanics as source mechanic IDs by extending `Cat1CreativeSlots.game_mechanic` literals. Activity-specific overlays carry the exact behavior, so no new per-mechanic fragment is required for v1.

For Cat5 Phoneme Treasure Hunt, create a collection catalog with text-compatible examples and distractors. For v1 these are fallbacks for non-text collection paths; typed text mode can collect arbitrary text.

**Step 5: Run tests**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add backend/games/activity_*.md backend/game_parser.py backend/entity_registry.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py
git commit -m "feat(activity): add exported recipes"
```

---

### Task 4: Start Activity Sessions And Text Cat5 Collection

**Files:**
- Modify: `backend/server.py`
- Modify: `backend/recipe_loader.py`
- Modify: `backend/schemas/session_state.py`
- Modify: `backend/turn_handling/core.py`
- Modify: `backend/turn_handling/collection.py`
- Modify: `backend/turn_handling/helpers.py`
- Test: `backend/tests/test_activity_text_game_api.py`
- Test: `backend/tests/test_activity_text_game_turns.py`

**Step 1: Add failing start and Cat5 text tests**

Extend `backend/tests/test_activity_text_game_api.py`:

```python
def test_start_activity_creates_text_session() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/start-activity",
        json={"activity_type": "activity_word_echo_practice", "tier": "T1", "interaction_mode": "text"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["activity_type"] == "activity_word_echo_practice"
    assert body["template_type"] == "cat1"
    assert body["session_state"]["interaction_mode"] == "text"
```

Create `backend/tests/test_activity_text_game_turns.py` with direct unit tests where possible:

```python
from schemas.session_state import SessionStateModel
from schemas.creative_slots import Cat5CreativeSlots
from turn_handling.collection import record_text_collection_pick


def test_text_collection_pick_records_typed_item() -> None:
    state = SessionStateModel(
        session_id="s1",
        tier="T1",
        template_type="cat5",
        activity_type="activity_phoneme_treasure_hunt",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        interaction_mode="text",
        creative_slots=Cat5CreativeSlots(
            observation_angle="form",
            collection_criterion="words that start with a target sound",
            collection_count=3,
            mission_metaphor="sound treasure hunt",
            role_title="Sound Treasure Hunter",
            synthesis_type="naming_story",
            stuck_hint="Try a word nearby.",
            naming_prompt="What word did you find?",
            detail_question_template="What sound does it start with?",
        ),
    )

    record_text_collection_pick(state, "ball")

    assert state.collection_phase == "detail"
    assert state.collected_text_items == ["ball"]
    assert state.collected_photos == ["text_find_1"]
```

**Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_turns.py -q
```

Expected: FAIL.

**Step 3: Add interaction mode state**

In `SessionStateModel`:

```python
interaction_mode: Literal["default", "text"] = "default"
collected_text_items: list[str] = Field(default_factory=list, description="Text-mode Cat5 collected item labels")
```

Set it in `recipe_to_session_state(..., interaction_mode="default")`.

**Step 4: Implement shared activity start**

In `backend/server.py`, create `_start_activity_session(entity_config, tier, interaction_mode)` by extracting the recipe setup used by `/api/start-deep-link`:

```python
async def _start_activity_session(
    entity_config: EntityConfig,
    tier: str,
    *,
    interaction_mode: str,
    source: str = "activity_text_game",
) -> JSONResponse:
    session_id = str(uuid.uuid4())
    recipe = load_instruction_recipe(entity_config.activity_type)
    state = recipe_to_session_state(recipe, session_id, tier, entity_config.demo_filename, interaction_mode=interaction_mode)
    ...
```

Do not fetch upstream context for `/api/start-activity`.

**Step 5: Implement text-mode Cat5 collection**

In `backend/turn_handling/collection.py`:

```python
def record_text_collection_pick(state: SessionStateModel, text: str) -> None:
    """Record a typed Cat5 collection item in text-only mode."""
    label = text.strip()
    if not label:
        return
    item_id = f"text_find_{len(state.collected_text_items) + 1}"
    state.collected_text_items.append(label)
    state.collected_photos.append(item_id)
    state.consecutive_wrong = 0
    state.collection_phase = "detail"
    state.detail_exchange_count = 0
```

In `core.resolve_turn`, before photo validation, call it when:

```python
if (
    state.interaction_mode == "text"
    and state.template_type == "cat5"
    and state.current_step.startswith("STEP_3_COLLECT_")
    and state.collection_phase == "photo"
    and turn_input.text
):
    record_text_collection_pick(state, turn_input.text)
```

Ensure it does not double-append child history beyond the existing actual child text.

Update `_state_context()` to include `collected_text_items`.

**Step 6: Run tests**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_turns.py -q
```

Expected: PASS.

**Step 7: Commit**

```bash
git add backend/server.py backend/recipe_loader.py backend/schemas/session_state.py backend/turn_handling/core.py backend/turn_handling/collection.py backend/turn_handling/helpers.py backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_turns.py
git commit -m "feat(activity): start text sessions"
```

---

### Task 5: Asset Manifest And Imagegen Prompt Workflow

**Files:**
- Create: `frontend/public/activity-assets/activity-assets.manifest.json`
- Create: `frontend/public/activity-assets/prompts/wonderlens-activity-style.md`
- Create: `frontend/src/activityGame/activityAssets.js`
- Create: `frontend/src/activityGame/activityAssets.test.js`
- Create: `docs/activity-authoring.md`

**Step 1: Write failing manifest tests**

Create `frontend/src/activityGame/activityAssets.test.js`:

```javascript
import { describe, expect, it } from 'vitest';
import manifest from '../../public/activity-assets/activity-assets.manifest.json';
import { assetForBeat, activitiesWithAssets } from './activityAssets';

describe('activity asset manifest', () => {
  it('maps every activity to an icon and beat assets', () => {
    expect(activitiesWithAssets(manifest)).toHaveLength(12);
    for (const entry of manifest.activities) {
      expect(entry.icon).toMatch(/^\/activity-assets\//);
      expect(entry.beats.length).toBeGreaterThanOrEqual(5);
      expect(entry.beats.map((beat) => beat.id)).toContain('intro');
      expect(entry.beats.map((beat) => beat.id)).toContain('recap');
    }
  });

  it('falls back to icon when a beat is missing', () => {
    const activity = manifest.activities[0];
    expect(assetForBeat(activity, 'unknown')).toBe(activity.icon);
  });
});
```

**Step 2: Run tests and confirm failure**

Run:

```bash
cd frontend
npm test -- src/activityGame/activityAssets.test.js --runInBand
```

Expected: FAIL because files do not exist. If `node_modules` is missing, run `npm install` first and commit only source/package-lock changes that are already expected; do not commit `node_modules`.

**Step 3: Add manifest shape and helpers**

Create manifest entries like:

```json
{
  "version": 1,
  "style": "wonderlens-soft-mint-device",
  "activities": [
    {
      "id": "activity_word_echo_practice",
      "source_export_id": "concept_word_echo_remember",
      "icon": "/activity-assets/activity_word_echo_practice/icon.png",
      "fallback_label": "Word Echo Practice",
      "beats": [
        {"id": "intro", "src": "/activity-assets/activity_word_echo_practice/intro.png", "usage": "hook"},
        {"id": "rules", "src": "/activity-assets/activity_word_echo_practice/rules.png", "usage": "setup"},
        {"id": "round_1", "src": "/activity-assets/activity_word_echo_practice/round_1.png", "usage": "round"},
        {"id": "round_2", "src": "/activity-assets/activity_word_echo_practice/round_2.png", "usage": "round"},
        {"id": "round_3", "src": "/activity-assets/activity_word_echo_practice/round_3.png", "usage": "round"},
        {"id": "recap", "src": "/activity-assets/activity_word_echo_practice/recap.png", "usage": "closing"}
      ]
    }
  ]
}
```

Create `frontend/src/activityGame/activityAssets.js`:

```javascript
export function activitiesWithAssets(manifest) {
  return Array.isArray(manifest?.activities) ? manifest.activities : [];
}

export function assetForBeat(activity, beatId) {
  const match = activity?.beats?.find((beat) => beat.id === beatId);
  return match?.src || activity?.icon || '';
}

export function beatIdFromSessionState(sessionState) {
  const step = sessionState?.current_step || '';
  if (step === 'STEP_1_HOOK') return 'intro';
  if (step === 'STEP_2_RULES' || step === 'STEP_2_MISSION' || step === 'STEP_2_SETUP') return 'rules';
  if (step.startsWith('STEP_3_ROUND_') || step.startsWith('STEP_3_COLLECT_') || step.startsWith('STEP_3_BUILD_')) {
    return `round_${sessionState?.current_round || 1}`;
  }
  if (step.includes('SYNTHESIS')) return 'synthesis';
  if (step.includes('CELEBRATE') || step.includes('CLOSING')) return 'recap';
  return 'intro';
}
```

**Step 4: Generate static assets with Codex imagegen**

Use the `imagegen` skill and built-in `image_gen` tool. Generate assets in activity batches. For each activity:

- One icon.
- Beat images for each runtime beat in the manifest.
- No in-image text.
- Shared style: soft white/mint WonderLens device language, rounded child-friendly toy illustration, clean dark circular lens compatibility.

After generation, copy selected outputs from `/Users/pharrelly/.codex/generated_images/...` into:

```text
frontend/public/activity-assets/<activity_id>/<beat_id>.png
```

Do not delete original generated outputs.

**Step 5: Add authoring docs**

Create `docs/activity-authoring.md` with:

- How to add a backend activity file.
- How to add/update manifest entries.
- How to run Codex internal imagegen for display assets.
- How to verify no runtime image generation happens.

**Step 6: Run tests**

Run:

```bash
cd frontend
npm test -- src/activityGame/activityAssets.test.js
```

Expected: PASS.

**Step 7: Commit**

```bash
git add frontend/public/activity-assets frontend/src/activityGame/activityAssets.js frontend/src/activityGame/activityAssets.test.js docs/activity-authoring.md
git commit -m "feat(activity): add display assets"
```

---

### Task 6: Frontend Text Session Hook

**Files:**
- Modify: `frontend/src/utils/api.js`
- Create: `frontend/src/activityGame/useActivityTextSession.js`
- Create: `frontend/src/activityGame/useActivityTextSession.test.jsx`

**Step 1: Write failing hook tests**

Create `frontend/src/activityGame/useActivityTextSession.test.jsx`:

```javascript
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import useActivityTextSession from './useActivityTextSession';

describe('useActivityTextSession', () => {
  it('starts an activity through the text endpoint', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 's1',
        activity_type: 'activity_word_echo_practice',
        template_type: 'cat1',
        session_state: { status: 'active', current_step: 'STEP_1_HOOK', turn_count: 1 },
        first_turn: { dialogue: 'Echo time!', screen_frame: { widget: 'activity_lens', widget_params: {} } },
      }), { status: 200 }));

    const { result } = renderHook(() => useActivityTextSession());

    await act(async () => {
      await result.current.startActivity('activity_word_echo_practice', 'T1');
    });

    expect(result.current.messages[0].text).toBe('Echo time!');
    expect(global.fetch).toHaveBeenCalledWith('/api/start-activity', expect.any(Object));
  });
});
```

**Step 2: Run tests and confirm failure**

Run:

```bash
cd frontend
npm test -- src/activityGame/useActivityTextSession.test.jsx
```

Expected: FAIL.

**Step 3: Add API helpers**

In `frontend/src/utils/api.js`:

```javascript
export async function fetchActivities() {
  const res = await fetch(`${BASE}/api/activities`);
  if (!res.ok) throw new Error(`Activities failed: ${res.status}`);
  return res.json();
}

export async function startActivitySession(activityType, tier = 'T1') {
  const res = await fetch(`${BASE}/api/start-activity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ activity_type: activityType, tier, interaction_mode: 'text' }),
  });
  if (!res.ok) throw new Error(`Activity start failed: ${res.status}`);
  return res.json();
}
```

**Step 4: Add text-only hook**

Create hook with local state shaped like `useConversation`, but only start activity and send `/api/turn`:

```javascript
export default function useActivityTextSession() {
  // state: messages, sessionId, sessionState, screenFrame, loading, turnPending, error, activityType, templateType
  // startActivity(activityType, tier)
  // sendMessage(text)
  // reset()
}
```

Do not call TTS, STT, silence timers, `/api/turn-speak`, or photo collection.

**Step 5: Run tests**

Run:

```bash
cd frontend
npm test -- src/activityGame/useActivityTextSession.test.jsx
```

Expected: PASS.

**Step 6: Commit**

```bash
git add frontend/src/utils/api.js frontend/src/activityGame/useActivityTextSession.js frontend/src/activityGame/useActivityTextSession.test.jsx
git commit -m "feat(activity): add text session hook"
```

---

### Task 7: Device Frame And Lens UI

**Files:**
- Create: `frontend/src/activityGame/WonderLensDevice.jsx`
- Create: `frontend/src/activityGame/WonderLensDevice.test.jsx`
- Create: `frontend/src/activityGame/ActivityLens.jsx`
- Modify: `frontend/src/index.css`

**Step 1: Write failing device tests**

Create `frontend/src/activityGame/WonderLensDevice.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import WonderLensDevice from './WonderLensDevice';

describe('WonderLensDevice', () => {
  it('renders preserved device controls and top-right scroll control', () => {
    render(
      <WonderLensDevice
        activity={{ name: 'Word Echo Practice', mechanic: 'remember' }}
        latestAiText="Repeat after me."
        progress={{ current: 1, total: 3 }}
        onScrollNext={vi.fn()}
        onPrimaryAction={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Scroll activity lens')).toBeInTheDocument();
    expect(screen.getByLabelText('Start or restart activity')).toBeInTheDocument();
    expect(screen.getByText('Word Echo Practice')).toBeInTheDocument();
  });
});
```

**Step 2: Run tests and confirm failure**

Run:

```bash
cd frontend
npm test -- src/activityGame/WonderLensDevice.test.jsx
```

Expected: FAIL.

**Step 3: Implement device shell**

Build a code-native device, not a bitmap:

- Outer body aspect ratio close to screenshot: `aspect-ratio: 0.78 / 1`.
- Large black circular lens near top.
- Left mint grip.
- Top-right mint scroll wheel/rocker, clickable and keyboard accessible.
- Small gray button.
- Large mint button.
- Use the `ActivityLens` component inside the circular screen.

Do not reuse `ToyCameraFrame` for this route because its proportions and green toy camera body differ from the screenshot.

**Step 4: Add lens UI**

`ActivityLens` props:

```javascript
{
  activity,
  latestAiText,
  sessionState,
  assetSrc,
  savedTokens,
}
```

It should render:

- Static beat asset if present.
- Latest AI text over/under asset inside the circular lens.
- Activity name.
- Mechanic badge.
- Progress dots.
- Saved child text tokens.

**Step 5: Run tests**

Run:

```bash
cd frontend
npm test -- src/activityGame/WonderLensDevice.test.jsx
```

Expected: PASS.

**Step 6: Commit**

```bash
git add frontend/src/activityGame/WonderLensDevice.jsx frontend/src/activityGame/WonderLensDevice.test.jsx frontend/src/activityGame/ActivityLens.jsx frontend/src/index.css
git commit -m "feat(activity): add device frame"
```

---

### Task 8: Activity Game Surface

**Files:**
- Create: `frontend/src/activityGame/ActivityGameApp.jsx`
- Create: `frontend/src/activityGame/ActivityLibrary.jsx`
- Create: `frontend/src/activityGame/ActivityTranscript.jsx`
- Create: `frontend/src/activityGame/ActivityTextInput.jsx`
- Create: `frontend/src/activityGame/ActivityGameApp.test.jsx`
- Modify: `frontend/src/App.jsx`

**Step 1: Write failing integration test**

Create `frontend/src/activityGame/ActivityGameApp.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ActivityGameApp from './ActivityGameApp';

vi.mock('../utils/api', () => ({
  fetchActivities: vi.fn(async () => ({
    count: 1,
    activities: [{
      id: 'activity_word_echo_practice',
      name: 'Word Echo Practice',
      kind: 'activity',
      category: 'category_1',
      mechanic: 'remember',
      tier: 'T1',
      premise: 'Repeat a word back.',
      core_ib_key_concepts: ['Form'],
    }],
  })),
  startActivitySession: vi.fn(),
  sendTurn: vi.fn(),
}));

describe('ActivityGameApp', () => {
  it('uses activity wording and no multimodal controls', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByText('Activity library')).toBeInTheDocument();
    expect(screen.getByText('Word Echo Practice')).toBeInTheDocument();
    expect(screen.queryByLabelText(/Voice input/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Choose a concept/i)).not.toBeInTheDocument();
  });
});
```

**Step 2: Run tests and confirm failure**

Run:

```bash
cd frontend
npm test -- src/activityGame/ActivityGameApp.test.jsx
```

Expected: FAIL.

**Step 3: Implement activity game surface**

Create an app shell with:

- Left activity library.
- Current activity status.
- Transcript.
- Text input and send button only.
- Right WonderLens device.

Use URL mode switch in `frontend/src/App.jsx`:

```javascript
const view = new URLSearchParams(window.location.search).get('view');
if (view === 'activities') {
  return <ActivityGameApp />;
}
```

This preserves existing demo behavior by default and makes the standalone surface available at:

```text
http://localhost:5173/?view=activities
```

**Step 4: Run tests**

Run:

```bash
cd frontend
npm test -- src/activityGame/ActivityGameApp.test.jsx src/activityGame/WonderLensDevice.test.jsx src/activityGame/useActivityTextSession.test.jsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/App.jsx frontend/src/activityGame
git commit -m "feat(activity): add activity game UI"
```

---

### Task 9: Backend And Frontend Contract Verification

**Files:**
- Modify if needed based on failures from previous tasks.

**Step 1: Run focused backend checks**

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_activity_text_game_turns.py -q
```

Expected: PASS.

**Step 2: Run focused frontend checks**

Run:

```bash
cd frontend
npm test -- src/activityGame/activityAssets.test.js src/activityGame/useActivityTextSession.test.jsx src/activityGame/WonderLensDevice.test.jsx src/activityGame/ActivityGameApp.test.jsx
npm run build
```

Expected: PASS.

**Step 3: Fix narrow failures**

If backend or frontend fails, fix only the failing contract. Do not broaden into unrelated refactors.

**Step 4: Commit fixes if any**

```bash
git add <changed-files>
git commit -m "fix(activity): align text game contract"
```

---

### Task 10: Live Backend Verification

**Files:**
- No file changes expected.

**Step 1: Start backend with credentials without printing secrets**

Run from repo root:

```bash
cd backend
set -a
source .env
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.elaborate-baton-480304-r8-a8a39bcb34f1.json"
uv run uvicorn server:app --reload --port 8000
```

Do not echo env values. Keep the server session running until frontend verification completes.

**Step 2: Smoke test backend endpoints**

In another shell:

```bash
curl -s http://localhost:8000/api/activities | python -m json.tool | sed -n '1,80p'
```

Expected: JSON contains `count: 12` and activity names.

Start a session:

```bash
curl -s -X POST http://localhost:8000/api/start-activity \
  -H 'Content-Type: application/json' \
  -d '{"activity_type":"activity_word_echo_practice","tier":"T1","interaction_mode":"text"}' \
  | python -m json.tool | sed -n '1,120p'
```

Expected: `status: ok`, `session_id`, `first_turn.dialogue`.

**Step 3: Stop backend only after frontend verification**

Do not leave long-running sessions open at final response.

---

### Task 11: Browser Verification

**Files:**
- No file changes expected unless visual defects are found.

**Step 1: Start frontend**

Run:

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

**Step 2: Use Browser plugin**

Open:

```text
http://127.0.0.1:5173/?view=activities
```

Verify:

- Activity library says "Activity library".
- There are 12 activities.
- No mic/TTS/photo upload controls are visible.
- Device body is compact and vertical, not stretched.
- Top-right scroll control is visible and clickable.
- Starting an activity calls backend and populates transcript/lens.
- Sending typed text advances a turn.
- At least one Cat1 activity starts.
- Guided Drawing starts and uses Cat3 setup/build wording.
- Phoneme Treasure Hunt accepts typed collection text.

Check desktop and mobile-ish widths. Fix any overlap or text clipping.

**Step 3: Commit visual fixes if any**

```bash
git add <changed-files>
git commit -m "fix(activity): polish device layout"
```

---

### Task 12: Documentation And Handoff

**Files:**
- Modify: `README.md`
- Modify or create: `HANDOFF.md`
- Modify: `docs/activity-authoring.md`
- Optional: `docs/plans/2026-05-27-activity-text-game.md` if execution notes need updates.

**Step 1: Update README**

Add a concise section:

```markdown
### Activity Text Game

Run backend and frontend, then open `http://localhost:5173/?view=activities`.
This surface starts backend-backed activity sessions with typed text only.
```

Include credential note without secret values.

**Step 2: Update HANDOFF**

Add top entry with:

- Problem
- Solution
- Edits
- NOT Changed
- Verification

Keep only last 10 entries and update `Last updated: 2026-05-27`.

**Step 3: Run doc diff check**

Run:

```bash
git diff --check
git diff -- README.md HANDOFF.md docs/activity-authoring.md
```

Expected: no whitespace errors.

**Step 4: Commit**

```bash
git add README.md HANDOFF.md docs/activity-authoring.md
git commit -m "docs(activity): document activity game"
```

---

## Final Verification

Run all focused checks:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_activity_text_game_turns.py -q
cd frontend
npm test -- src/activityGame/activityAssets.test.js src/activityGame/useActivityTextSession.test.jsx src/activityGame/WonderLensDevice.test.jsx src/activityGame/ActivityGameApp.test.jsx
npm run build
```

Run live smoke:

```bash
cd backend
set -a
source .env
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.elaborate-baton-480304-r8-a8a39bcb34f1.json"
uv run uvicorn server:app --reload --port 8000
```

Then:

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/?view=activities` with Browser plugin and verify the checklist in Task 11.

## Completion Criteria

- Worktree is clean after final commit.
- All 12 activities appear in the frontend activity library.
- All 12 activities can start backend sessions.
- Cat1 and Cat5 flows still use existing runtime semantics.
- Guided Drawing has a minimal Cat3 flow.
- Text-only UI has no mic, TTS, audio, photo upload, or camera controls.
- Device proportions are preserved and top-right scroll control is visible.
- Static activity assets are committed and manifest-driven.
- Future activity authoring is documented.
- Live API verification uses backend `.env` and credential JSON without exposing secrets.
