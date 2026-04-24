# Activity Signature — Demo Implementation Plan (fullstack-demo)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mirror the `activity_signature` runtime engine that ships in `wonderlens-ai` into this prototype — dataclass-based models, simpler `aiosqlite` persistence, same shared test vector for behavioral parity.

**Architecture:** Direct port of wonderlens-ai's `activity_signature` package, adapted to this repo's existing style (dataclasses instead of Pydantic; direct `aiosqlite` instead of a `DatabaseManager`). Logic parity verified by running the same `activity_signature_scenarios.json` fixture that the backend plan produces.

**Prerequisite plans:**
- **Authoring** (autodesign): `docs/plans/2026-04-23-activity-signature-authoring.md` — produces the canonical `activity_vocabulary.md`, the 5 per-game dirs, and the `activity_signature_scenarios.json` fixture. Must ship first.
- **Backend** (wonderlens-ai): `docs/plans/2026-04-23-activity-signature-backend.md` — reference implementation. Can ship before or in parallel with this plan; this plan doesn't depend on the backend's code, only on the authoring plan's artifacts.

This plan is otherwise **self-contained** — you copy artifacts into place in Task 2, then all subsequent work is local to this repo.

**Companion docs:**
- Cross-repo overview: `wonderlens-activity-autodesign/docs/plans/2026-04-23-activity-signature-integration.md`

**Tech Stack:**
- Python 3.12, FastAPI, `aiosqlite`, dataclasses
- React 18 + Vite (no changes in this plan — payload extensions feed an existing debug panel)
- Testing: pytest + pytest-asyncio (already configured)

---

## ◆ Recent updates (2026-04-24)

Spec additions landed after the plan was first written. Search this plan for `◆ 2026-04-24` to find every affected spot.

| Change | Affected tasks | What changes |
|---|---|---|
| **New `activity_signature.intro` field** — one-sentence observer-facing description, Layer 2 templated (design spec §3.5) | Task 2 (dataclass), Task 3 (loader), Task 4 (writer + session-end wiring) | `ActivitySignature` dataclass gains `intro: str` field; loader reads it with fallback to `plain_description`; writer includes rendered `intro` in `recap.latest.yaml` + `dashboard.latest.yaml`; server `/session/end` handler renders template before writing |
| **Two-layer activity_signature distinction** — Layer 1 (identity) vs Layer 2 (templated) | Task 2 (dataclass docstring) | Dataclass docstring marks each field layer |
| **observation_angle orthogonal to topic_axis** (not sub-dimension) | Task 2 (vocabulary docstring) | Module docstring in `vocabulary.py` aligned with `activity_vocabulary.md` |

---

## 0 · Context (read this first)

### 0.1 Design spec

**Required reading before starting:** `docs/plans/2026-04-23-activity-signature-design.md`

That doc is authoritative for:
- The 6-field `activity_signature` block (§3)
- 3 closed vocabularies: `observation_angle` (10), `mechanic` (8), `entity_role` (4) (§3.2-3.4)
- Per-game directory layout (§4)
- Matcher scoring (§5.3)
- Payload extensions (§6)
- DB schema changes (§7)
- V1 scope: migrate 5 games, leave 19 on legacy layout via dual-loader (§8)

This plan implements the spec. If the spec is ambiguous, fix the spec first — don't improvise.

### 0.2 Repos and paths

| Repo | Root | Role |
|---|---|---|
| autodesign | `/Users/pharrelly/codebase/github/wonderlens-activity-autodesign` | Source of truth — vocabulary, spec, games |
| wonderlens-ai | `/Users/pharrelly/codebase/gitlab/wonderlens-ai` | Production backend; Pydantic + DatabaseManager |
| fullstack-demo | `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo` | Prototype; dataclasses + aiosqlite |

### 0.3 Git worktree convention

Per `memory/feedback_worktree_convention.md`: branches under `.worktrees/feat/activity-signature/` in each of the three repos. Task 1 creates these.

### 0.4 Complementary systems (read-only context)

- **Progression runtime plans** (`2026-04-21-progression-runtime-*.md`) — already-written. Selector bonus here stacks on top of progression's existing rung bonus.
- **Matchability tags** (`2026-04-20-matchability-tags-*.md`) — already shipped. `entity_binding`/`entity_class`/`tier_range` are already in game tag blocks; this plan's `activity_signature` sits alongside them in the same tag_block.yaml.

---

## 1 · File structure (this repo only)

### 1.1 New files

```
backend/activity_signature/
├── __init__.py
├── models.py                  # dataclass port of wonderlens-ai's Pydantic models
├── vocabulary.py              # StrEnums mirroring autodesign's activity_vocabulary.md
├── conversation_signature.py  # V1 heuristic, same keywords as wonderlens-ai
├── writer.py                  # .latest.yaml writer
└── per_game_loader.py         # loader for activities/<game_id>/ layout

backend/activities/             # ◆ read-only mirror copied from autodesign
└── <game_id>/                  # 5 dirs

backend/tests/activity_signature/
├── test_models.py
├── test_vocabulary.py
├── test_writer.py
├── test_per_game_loader.py
├── test_scenarios.py           # runs the shared JSON fixture
└── fixtures/
    └── activity_signature_scenarios.json  # byte-identical copy from autodesign
```

### 1.2 Modified files

| File | What changes |
|---|---|
| `backend/game_loader.py` | Route through new per-game loader; fall back to legacy `games/*.md` |
| `backend/entity_registry.py` | Index by `observation_angle` for scoring lookups |
| `backend/server.py` | Accept `conversation_signature` on session-start request; write `.latest.yaml` on session-end handler |
| `backend/db.py` | Add 4 columns to `session_outcomes`: `observation_angle`, `mechanic`, `entity_role`, `focal_attribute` |

---

## 2 · Task plan (bite-sized)

5 tasks: worktree → port vocabulary + models → port conversation_signature + per-game loader → port selector + writer + DB → shared fixture + verify + PR.

---

### Task 1: Worktree setup

**Files:**
- Create: `.worktrees/feat/activity-signature/` in this repo

- [ ] **Step 1: Create the worktree**

```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo
git fetch origin
git worktree add .worktrees/feat/activity-signature -b feat/activity-signature origin/main
```

- [ ] **Step 2: Verify tests pass before any changes**

```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-signature
python -m pytest backend/tests -x -q
```
Expected: all pass (baseline).

- [ ] **Step 3: No commit yet — setup only.**

All paths in subsequent tasks are relative to `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-signature`.

---

### Task 2: Port vocabulary + models (dataclass variant)

**Files:**
- Create: `backend/activity_signature/__init__.py`
- Create: `backend/activity_signature/vocabulary.py`
- Create: `backend/activity_signature/models.py`
- Test: `backend/tests/activity_signature/test_vocabulary.py`, `test_models.py`

- [ ] **Step 1: Port `vocabulary.py`**

Identical to `wonderlens-ai/app/modules/activity/activity_signature/vocabulary.py` except for import paths. Use the same `StrEnum` classes — they work in both codebases. Copy the file verbatim and adjust imports if any.

- [ ] **Step 2: Port `models.py` as dataclasses**

`backend/activity_signature/models.py`:
```python
"""Dataclass port of wonderlens-ai/app/modules/activity/activity_signature/models.py.

Field names + semantics 1:1 with the Pydantic version so the shared scenario
fixture (activity_signature_scenarios.json) applies identically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.activity_signature.vocabulary import (
    EntityRole,
    Mechanic,
    ObservationAngle,
)


@dataclass
class BridgePrerequisites:
    primary: list[ObservationAngle] = field(default_factory=list)
    secondary: list = field(default_factory=list)  # ObservationAngle | str


@dataclass
class ActivitySignature:
    """The activity_signature block.

    Two layers:
      · Layer 1 (identity, matcher-facing): observation_angle, mechanic,
        entity_role, bridge_prerequisites
      · Layer 2 (presentation, templated): focal_attribute, intro,
        preview_label, preview_prompt, role_pivot_note
    """
    # Layer 1 — editorial identity
    observation_angle: ObservationAngle
    mechanic: Mechanic
    entity_role: EntityRole
    bridge_prerequisites: BridgePrerequisites
    # Layer 2 — presentation (templated)
    focal_attribute: str
    intro: str                                   # ◆ 2026-04-24 NEW — one sentence, observer-facing; see design spec §3.5
    preview_label: str
    preview_prompt: str
    role_pivot_note: str | None = None


@dataclass
class ConversationSignature:
    dominant_angle: ObservationAngle | None = None
    secondary_angles: list[ObservationAngle] = field(default_factory=list)
    turn_count: int = 0
    entity_role_implied: EntityRole = EntityRole.SUBJECT
```

- [ ] **Step 3: Write tests mirroring the wonderlens-ai test file**

Adjust assertions for dataclass behavior (no ValidationError; Python will raise TypeError if required fields missing). Drop the `preview_label` max-length test (dataclasses don't enforce length; add a `__post_init__` validator if strict enforcement is required).

- [ ] **Step 4: Run, verify pass + commit**

```bash
python -m pytest backend/tests/activity_signature/test_vocabulary.py backend/tests/activity_signature/test_models.py -x -q
```

```bash
git add backend/activity_signature/ backend/tests/activity_signature/
git commit -m "feat(activity-signature): port vocabulary + models to fullstack-demo"
```

---

### Task 3: Port conversation_signature + per_game_loader

**Files:**
- Create: `backend/activity_signature/conversation_signature.py`
- Create: `backend/activity_signature/per_game_loader.py`
- Test: `backend/tests/activity_signature/test_conversation_signature.py`, `test_per_game_loader.py`

- [ ] **Step 1: Copy activities/ from autodesign**

```bash
mkdir -p backend/activities
cp -r /Users/pharrelly/codebase/github/wonderlens-activity-autodesign/.worktrees/feat/activity-signature/activities/* \
      backend/activities/
```

- [ ] **Step 2: Port conversation_signature.py verbatim**

Same heuristic, same keyword table. Adjust imports only.

- [ ] **Step 3: Port per_game_loader.py**

Demo's `GameDefinition` lives in `backend/game_parser.py` (or `game_loader.py`). Check which:

```bash
grep -l "class GameDefinition\|class Game " backend/*.py
```

◆ 2026-04-24 — When constructing `ActivitySignature` from parsed YAML, resolve `intro` with fallback:

```python
sig_data = data.get("activity_signature") or {}
# 1. explicit intro → use it  2. plain_description fallback  3. raise
intro = sig_data.get("intro") or data.get("plain_description")
if not intro:
    raise ValueError(
        f"{game_dir.name}: activity_signature requires `intro` "
        "(no plain_description fallback available). See design spec §3.5."
    )
signature = ActivitySignature(
    # ... other fields ...
    intro=intro,
    # ...
)
```

Add one parity test mirroring wonderlens-ai:

```python
def test_intro_fallback_to_plain_description(tmp_path):
    # same shape as backend plan Task 5 — verify fallback works
    ...
```

Then implement a loader that returns demo's GameDefinition shape, with activity_signature attached. Exact structure depends on demo's existing model — adapt accordingly while preserving the contract from autodesign's tag_block.yaml.

- [ ] **Step 4: Write + run tests, commit**

```bash
git add backend/activity_signature/ backend/activities/ backend/tests/activity_signature/
git commit -m "feat(activity-signature): port conversation_signature + per-game loader to demo"
```

---

### Task 4: Port selector scoring + writer

**Files:**
- Modify: `backend/state_machine.py` or wherever selection happens
- Create: `backend/activity_signature/writer.py`
- Modify: `backend/db.py` (ALTER session_outcomes columns)

- [ ] **Step 1: Locate selection code in fullstack-demo**

```bash
grep -rn "select_game\|pick.*game\|Tier A\|Tier B" backend/ --include="*.py" | head -10
```

Demo's selection flow may be simpler than wonderlens-ai's. Add the scoring bonus at whichever function picks the game; preserve existing tier-based ranking.

- [ ] **Step 2: Port writer.py**

Same shape as wonderlens-ai's `app/modules/activity/activity_signature/writer.py`. Identical logic, adjust imports.

◆ 2026-04-24 — `LatestPayload` dataclass includes `rendered_intro: str = ""` field. `_build_recap` emits `intro: <rendered>`; `_build_dashboard` emits `session.intro: <rendered>`. Mirror of backend plan Task 9.

- [ ] **Step 3: DB migration for demo**

In `backend/db.py`, append to the schema DDL block (from the progression-runtime demo plan, columns already exist for `session_outcomes`):

```python
# Signature fields
CREATE TABLE IF NOT EXISTS session_outcomes (
    # ... existing columns from progression plan ...
    observation_angle TEXT,
    mechanic TEXT,
    entity_role TEXT,
    focal_attribute TEXT
);
```

If session_outcomes already exists without these columns, add ALTER TABLE statements (idempotent pattern via PRAGMA table_info check, mirroring the progression demo plan).

- [ ] **Step 4: Wire writer + DB writes into server.py's session-end handler**

Pattern: load the active game's `GameDefinition`, build a `LatestPayload` from session state + activity_signature fields, call `write_latest_yaml(game_dir, payload)`, then INSERT into `session_outcomes` with the four new columns. The backend reference plan (`wonderlens-ai/docs/plans/2026-04-23-activity-signature-backend.md`) shows the equivalent wiring — the demo version has fewer moving parts since there's no `ActivityService` orchestrator. Integration test at `backend/tests/activity_signature/test_end_session.py` is optional; manual verification (smoke test in Task 5) is acceptable.

◆ 2026-04-24 — Before calling `write_latest_yaml`, render the activity_signature intro template with concrete session data:

```python
# In server.py's session-end handler, before building LatestPayload:
game_def = registry.get_by_activity_type(session["activity_type"])
sig = game_def.activity_signature
rendered_intro = sig.intro.format(
    entity=session["entity_name"],
    focal_attribute=session.get("matched_property") or sig.focal_attribute.strip("{}"),
    **({sig.observation_angle: session["matched_property"]} if session.get("matched_property") else {}),
) if sig and sig.intro else ""

payload = LatestPayload(
    # ... other fields ...
    rendered_intro=rendered_intro,
)
```

Mirror of backend plan Task 10's `_render_template` helper. Demo version is simpler — no pet_type derivation needed unless you're exercising that scenario.

- [ ] **Step 5: Commit**

```bash
git add backend/activity_signature/writer.py backend/db.py backend/server.py backend/state_machine.py
git commit -m "feat(activity-signature): port selector scoring + .latest.yaml writer to demo"
```

---

### Task 5: Shared scenario fixture + demo verification + PR

- [ ] **Step 1: Copy fixture from autodesign**

```bash
mkdir -p backend/tests/activity_signature/fixtures
cp /Users/pharrelly/codebase/github/wonderlens-activity-autodesign/.worktrees/feat/activity-signature/docs/plans/fixtures/activity_signature_scenarios.json \
   backend/tests/activity_signature/fixtures/
```

- [ ] **Step 2: Port scenario runner**

```python
# backend/tests/activity_signature/test_scenarios.py
import json
from pathlib import Path

import pytest

from backend.activity_signature.models import ConversationSignature
# Demo-specific selector import
from backend.state_machine import select_game  # adjust per where selection lives

FIXTURE = Path(__file__).parent / "fixtures" / "activity_signature_scenarios.json"


@pytest.mark.parametrize(
    "scenario", json.loads(FIXTURE.read_text())["scenarios"], ids=lambda s: s["name"],
)
def test_scenario_pick(scenario):
    conv = None
    if scenario["conversation_signature"] is not None:
        conv = ConversationSignature(**scenario["conversation_signature"])
    result = select_game(
        entity_name=scenario["photo_entity"],
        detected_properties=scenario["detected_properties"],
        age_tier=scenario["age_tier"],
        conversation_signature=conv,
    )
    assert result.activity_type == scenario["expected_pick"]
```

- [ ] **Step 3: Run full demo test suite**

```bash
python -m pytest backend/tests -x -q
```
Expected: all pass including the 4 scenarios.

- [ ] **Step 4: Byte-parity check**

```bash
diff backend/tests/activity_signature/fixtures/activity_signature_scenarios.json \
     /Users/pharrelly/codebase/github/wonderlens-activity-autodesign/.worktrees/feat/activity-signature/docs/plans/fixtures/activity_signature_scenarios.json
```
Expected: no output (byte-identical).

- [ ] **Step 5: Code review + simplify, commit, push + open PR**

```bash
git push -u origin feat/activity-signature
gh pr create --title "feat(activity-signature): runtime engine (demo port)" \
             --body "Mirrors wonderlens-ai's implementation. Shares activity_signature_scenarios.json test vector."
```

---

## 3 · Known V1 limitations

Document in each PR/MR description:

1. **LLM-based dominant_angle is deferred.** V1 uses keyword-matching heuristic. Expect false negatives on synonyms not in the table (e.g., "crimson" → color).
2. **5 games migrated; 19 remain on legacy layout.** Loader supports both; follow-up PRs migrate the rest. Until then, unmigrated games have `activity_signature = None` and are scored without signature bonus.
3. **Angle-to-axis map is static.** `_ANGLE_TO_AXIS` hardcodes that all visual/physical angles map to Form. If an activity is genuinely at Causation angle=color ("why is it red?"), the dashboard rollup will misattribute. Acceptable for V1; revisit when a real case arises.
4. **`.latest.yaml` files committed to git.** Initial cautious default; switch to `.gitignore`d if authors find the noise unhelpful (1-line change).
5. **`bridge_prerequisites.secondary` can contain non-enum strings.** V1 stores them but doesn't score them; full matching is future work.

---

## 4 · Commit/PR discipline

Per `memory/feedback_review_simplify.md`:
- After each task → code-reviewer + code-simplifier, fix Important findings, commit follow-ups
- After each Phase → cross-branch code-reviewer before opening PR/MR

Per `memory/feedback_worktree_convention.md`: branches under `.worktrees/feat/activity-signature/` in each repo.

Per `memory/feedback_plan_datetime.md`: this plan is `2026-04-23-activity-signature-demo.md`.

---

## 5 · Verification summary

- [ ] `python -m pytest backend/tests -x -q` — all pass
- [ ] `backend/tests/activity_signature/test_scenarios.py` — 4 scenarios green (same outcomes as the backend repo's equivalent test)
- [ ] `backend/activity_signature/vocabulary.py` enum members match `wonderlens-activity-autodesign/docs/activity_vocabulary.md`
- [ ] `activity_signature_scenarios.json` byte-identical to the autodesign copy:
  ```bash
  diff backend/tests/activity_signature/fixtures/activity_signature_scenarios.json \
       /Users/pharrelly/codebase/github/wonderlens-activity-autodesign/.worktrees/feat/activity-signature/docs/plans/fixtures/activity_signature_scenarios.json
  ```
  Expected: no output.
- [ ] End-to-end demo session produces `recap.latest.yaml` + `dashboard.latest.yaml` in the local game dir
- [ ] ◆ 2026-04-24 — `recap.latest.yaml.intro` is non-empty, contains no unrendered `{placeholders}`, and reflects the photographed entity
- [ ] ◆ 2026-04-24 — `dashboard.latest.yaml.session.intro` matches the recap's intro
- [ ] PR opened with link to `wonderlens-activity-autodesign/docs/plans/2026-04-23-activity-signature-integration.md`

---

## Revnote

- **v0.2** (2026-04-24) — Added `activity_signature.intro` field: extends `ActivitySignature` dataclass (Task 2), loader reads intro with `plain_description` fallback (Task 3), writer emits rendered `intro` in both YAML outputs (Task 4), server session-end handler renders the template before writing. Mirrors backend plan v0.2. See design spec §3.5.
- **v0.1** (2026-04-23) — Inaugural demo-mirror plan. 5 tasks: worktree setup · port vocabulary + models · port conversation_signature + per-game loader · port selector + writer + DB · shared fixture + verify + PR. V1 scope matches the backend plan: 6-field `activity_signature`, heuristic dominant_angle, selector bonus, `.latest.yaml` writes. Deferred items (§3) match the backend plan. Backend reference implementation ships via `wonderlens-ai/docs/plans/2026-04-23-activity-signature-backend.md`.
