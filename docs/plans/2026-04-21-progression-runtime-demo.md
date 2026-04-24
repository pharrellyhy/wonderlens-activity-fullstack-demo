# Progression Runtime — Demo Implementation Plan (fullstack-demo)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mirror the progression runtime that ships in `wonderlens-ai` (Template 0 §07 rules + walkthrough scenarios + interaction-spec Soft-Reframe trigger) into this prototype repo so the demo's behavior matches prod on the 4 canonical journeys.

**Design authorities (read in order):**
1. `wonderlens-activity-autodesign/docs/template_0_preview.html` §07 — the rule source of truth (5 triggers).
2. `wonderlens-activity-autodesign/docs/plans/2026-04-23-progression-interaction-spec.md` — adds the 6th trigger (Soft-Reframe) and canonical wait-time constants (§6.1).
3. `wonderlens-activity-autodesign/progression-pedagogy-spec.md` — three-framework ECE synthesis (Colorado ELDG · UK EYFS Development Matters · China MoE 3–6 Guidelines).

**Out of scope (demo):** banned-phrase constraints and dignity-reframe prompt injections. Those live in `wonderlens-ai` only via `docs/plans/2026-04-24-agent-dialogue-constraints-backend.md` — the demo uses its own independent agent stack and does not mirror production's speaker prompt.

**Architecture:** A pure-function rules engine (`backend/progression/rules.py`) owns the quantified triggers. A stateful service (`progression/service.py`) loads per-device axis state, feeds it to the game selector, records turn-by-turn outcomes during gameplay, and persists new rung assignments at session end. Demo uses `aiosqlite` directly (not a `DatabaseManager`) and dataclasses (not Pydantic) to match this repo's existing style. There is no multi-device concept — a stable `device_id = "demo-local"` constant stands in.

**Prerequisite plan:** The reference implementation + canonical JSON scenario vector ship first in `wonderlens-ai` via `docs/plans/2026-04-21-progression-runtime-backend.md`. You'll copy the fixture from there in Task 2. This plan is otherwise **self-contained** — you don't need to read the backend plan's task bodies to finish the demo work.

**Tech Stack:**
- Backend: Python 3.12, FastAPI, `aiosqlite`, dataclasses
- Frontend: React 18 + Vite (adds a small debug panel, no new runtime logic)
- Testing: pytest + pytest-asyncio (already configured)

---

## 0 · Context (read this first)

### 0.1 What's being shipped

The design lives in two places:

1. **Template 0 §07 "Promotion & demotion — when to move the child between rungs"** in `docs/template_0_preview.html` (autodesign repo).
   - Source of truth for the 5 §07 quantified triggers + three footer rules. The 6th trigger (Soft-Reframe) lives in the Progression Interaction Spec (see authorities above).
2. **`docs/template_0_progression_walkthrough.html`** — 4 hand-authored scenarios illustrating the rules in action (steady progression, hit-a-wall recovery, across-axis independence, reluctance vs inability).

Both files are shipped and reviewed; no content changes are in scope here. This plan takes those rules and makes them run.

### 0.2 The six quantified triggers

Five triggers come verbatim from §07. The sixth (Soft-Reframe) is promoted from a Scenario-4 footnote to a first-class runtime trigger per `wonderlens-activity-autodesign/docs/plans/2026-04-23-progression-interaction-spec.md` §3. All six ride the same classifier and share the wait-time policy block.

| # | Trigger | Scope | Condition | Effect |
|---|---|---|---|---|
| 1 | **Within-activity promote** | single activity | child answered current rung correctly in **2+ rounds** without prompt-repetition, OR spontaneously produced an L+1 response | bump target rung for next activity on this axis (not mid-activity) |
| 2 | **Within-activity hold** | single activity | mixed or slow but on-topic | stay at current rung, vary exemplar |
| 3 | **Within-activity demote** | single activity | child did not complete current rung after **2 attempts** (silence > 6s, off-topic, or repeats prompt) | drop one rung, **same axis** (never abandon mid-activity); floor L1 |
| 4 | **Across-activity promote** | session sequence | child finished at current rung in **3 consecutive activities** on the same axis | next activity on that axis defaults to rung + 1 |
| 5 | **Across-activity demote** | session sequence | child needed an in-activity demote in **2 consecutive sessions** on the same axis | next activity on that axis defaults to rung − 1 (floor L1) |
| 6 | **Soft-Reframe** | within-turn | silence ≥ **10s** **after a correct response** (and no subsequent failed attempt that turn), OR mixed/slow on-topic with hesitation | **no rung change**, **no attempt-counter increment**; script agent receives `soft_reframe=True` flag → hint / multiple-choice / extended-wait beat (demo uses its own agent stack; the flag is emitted identically but wired differently) |

### 0.3 The three footer rules

| Rule | Rule | Implementation hook |
|---|---|---|
| **Dignity rule** | Demote is never surfaced as failure. Script agent language switches from "let's try again" to "let me show you what I notice first" when a `within_activity_demote` fires mid-session. | Passed into script agent as a `dignity_reframe=True` flag on the turn. |
| **Sibling-axis jump** | If the child has hit L3 on one axis, the next activity can jump to L1 on a related axis (Form→Connection, Causation→Change) instead of forcing L3 elsewhere. | Applied by game selector when it can't find a viable L3 activity on the current axis. |
| **Personalization hook** | Thresholds are a `progression_policy` object — not hardcoded. V1 uses defaults; ≥ ~200 sessions triggers swap to per-child pace model. | `progression_policy` lives in DB per device; default is loaded from YAML; swap is an admin-API toggle (out of scope for V1 impl, interface only). |

### 0.4 Soft-reframe is NOT a demote (the key distinction)

A single silence (≥ 10s per interaction spec §6.1) or attention lapse **after a correct response** is **not** a demote trigger. The runtime has a **soft-reframe** beat: same rung, softer prompt (hint, multiple-choice scaffold, or extended-wait acknowledgement). Demote requires the 2-attempts-with-failure pattern.

This distinction must hold in three places, identically to the backend implementation:

1. **Classifier (`backend/progression/rules.py::classify_round_trail`)** — emits `Outcome.SOFT_REFRAME` on silence-after-correct; emits `Outcome.DEMOTE` only on 2 consecutive failed attempts. Mutually exclusive; attempt counter never increments on a soft-reframe round.
2. **Session-outcome aggregation** — soft-reframe does **not** count toward across-activity demote; also does **not** count toward across-activity promote (rung-neutral).
3. **Demo agent stack** — the `soft_reframe=True` flag is emitted but consumed by demo-specific dialogue code, not the production speaker prompt. Out of scope for this plan: dialogue-layer banned-phrase constraints (those live in `wonderlens-ai` only).

**Pedagogical basis:** the 10s wait-time floor comes from EYFS Development Matters p. 29 ("at least 10 seconds processing time"); the ban on treating silence-after-correct as failure comes from Colorado ELDG p. 124 ("vary wait time") and China MoE 3-6 Guidelines p. 14 ("提醒他不要着急，慢慢说").

### 0.5 Repos and paths

| Repo | Root | Language | Purpose |
|---|---|---|---|
| `wonderlens-ai` | `/Users/pharrelly/codebase/gitlab/wonderlens-ai` | Python FastAPI | Production backend (Android-app client). DB-persisted multi-device. |
| `wonderlens-activity-fullstack-demo` | `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo` | Python FastAPI + React | Self-contained prototype. Local SQLite, single-user implied. |

**Rule from `memory/project_three_repos.md`:** don't copy code between them. Each repo re-implements the module in its own style. Logic parity is verified by a shared test vector (§7 of this plan).

### 0.6 Git worktree convention

Per `memory/feedback_worktree_convention.md`: branch under `.worktrees/feat/progression-runtime/`. Commands in Task 1 create this.

### 0.7 Existing code to hook into

**Existing code to hook into** (read before starting):
- `backend/db.py` — `sessions` / `turns` / `agent_logs` schema (this plan adds two new tables here)
- `backend/state_machine.py` — activity state machine
- `backend/server.py` — FastAPI endpoint routes (this plan adds `GET /progression/snapshot`)
- `backend/turn_handling/rounds.py` — Cat1 round-level handler (where within-activity outcome signals attach)
- `backend/turn_handling/collection.py` — Cat5 detail-phase equivalent
- `frontend/src/App.jsx` — root React component (this plan adds a toggle for the debug panel)

---

## 1 · File structure

### 1.1 New files

```
backend/progression/
├── __init__.py
├── models.py                      # Mirror of wonderlens-ai progression models
├── rules.py                       # Mirror of wonderlens-ai rules
├── policy.py
├── sibling_pairs.py
├── service.py                     # Demo variant — uses backend/db.py not DatabaseManager
└── dignity.py

backend/tests/progression/
├── test_rules.py                  # Same test vector as wonderlens-ai (§7)
├── test_service.py
└── fixtures/
    └── progression_scenarios.json # IDENTICAL file as wonderlens-ai

frontend/src/components/
└── ProgressionSnapshot.jsx        # Debug panel — radial/bar view of rung-per-axis
```

### 1.2 Modified files

| File | Lines to touch | Why |
|---|---|---|
| `backend/db.py` | add `device_progression` table DDL + `log_progression()` / `get_progression()` helpers | Persist rung state per "device" (demo: a stable anon ID) |
| `backend/server.py` | add `GET /progression/snapshot`; wire `ProgressionService` into `/session/start` (load target rung) and `/session/end` (apply result) | HTTP surface for debug panel + live runtime hooks |
| `backend/turn_handling/rounds.py` | emit `within_activity_outcome` into turn result | Outcome classification in Cat1 |
| `backend/turn_handling/collection.py` | same for Cat5 detail phase | Outcome classification in Cat5 |
| `frontend/src/App.jsx` | add toggle to open `<ProgressionSnapshot />` panel; fetch on session end | Show the 7-axis view after each session |

### 1.3 Related plans

- **Backend reference implementation:** `wonderlens-ai/docs/plans/2026-04-21-progression-runtime-backend.md` — ships first; produces the canonical scenario vector JSON that Task 2 of this plan copies in.
- **Top-level coordination doc:** `wonderlens-activity-autodesign/docs/plans/2026-04-21-progression-runtime-integration.md` — short overview with links to both sibling plans.

---

## 2 · Core data shapes (reference)

Both repos converge on these shapes. `wonderlens-ai` uses Pydantic; `fullstack-demo` uses dataclasses (to match its existing style). Field names and semantics are identical.

### 2.1 Axes and rungs

```python
# app/modules/activity/progression/models.py  (wonderlens-ai)
# backend/progression/models.py               (fullstack-demo; dataclass variant)

from enum import StrEnum

class Axis(StrEnum):
    FORM = "form"
    FUNCTION = "function"
    CAUSATION = "causation"
    CHANGE = "change"
    CONNECTION = "connection"
    PERSPECTIVE = "perspective"
    RESPONSIBILITY = "responsibility"


class Rung(StrEnum):
    L1 = "L1"   # notice
    L2 = "L2"   # extend
    L3 = "L3"   # reason


class Outcome(StrEnum):
    PROMOTE = "promote"
    HOLD = "hold"
    DEMOTE = "demote"
    SOFT_REFRAME = "soft_reframe"   # distinct from demote per Scenario 4
```

### 2.2 Per-axis rung state (persisted per device)

```python
class AxisState(BaseModel):
    axis: Axis
    current_rung: Rung | None = None              # None = axis never touched
    consecutive_axis_successes: int = 0            # counter for across-activity promote (threshold 3)
    consecutive_axis_demotes: int = 0              # counter for across-activity demote (threshold 2)
    last_outcome: Outcome | None = None
    total_sessions_on_axis: int = 0                # for personalization hook trigger (~200)

class ProgressionState(BaseModel):
    device_id: str
    axes: dict[Axis, AxisState]
    policy_version: str = "v1_default"
    updated_at: datetime
```

### 2.3 Progression policy (thresholds)

```python
class ProgressionPolicy(BaseModel):
    # Within-activity triggers
    within_promote_clean_rounds: int = 2           # "2+ rounds without prompt-repetition"
    within_demote_failed_attempts: int = 2         # "2 attempts"
    silence_threshold_trigger_demote_attempt_seconds: float = 6.0
    soft_reframe_fire_after_seconds: float = 10.0     # Interaction spec §6.1 — EYFS p. 29 ("≥10s processing time")

    # Across-activity triggers
    across_promote_consecutive: int = 3
    across_demote_consecutive: int = 2

    # Floors / ceilings
    rung_floor: Rung = Rung.L1
    rung_ceiling: Rung = Rung.L3

    # Sibling jump
    enable_sibling_jump: bool = True

    # Personalization hook (V1: interface only — no pace-model implementation)
    personalization_trigger_sessions: int = 200

    # Dignity reframe phrase — passed verbatim to script agent
    dignity_reframe_instruction: str = 'Open with a reframe: "let me show you what I notice first". Do not say "let\'s try again" or "easier".'
```

### 2.4 Sibling pairs (static)

```python
# progression/sibling_pairs.py
# Ordered by design preference — first match wins for L3→L1 jump
SIBLING_PAIRS: dict[Axis, list[Axis]] = {
    Axis.FORM:           [Axis.CONNECTION, Axis.FUNCTION],
    Axis.FUNCTION:       [Axis.FORM, Axis.CAUSATION],
    Axis.CAUSATION:      [Axis.CHANGE, Axis.CONNECTION],
    Axis.CHANGE:         [Axis.CAUSATION, Axis.CONNECTION],
    Axis.CONNECTION:     [Axis.FORM, Axis.PERSPECTIVE],
    Axis.PERSPECTIVE:    [Axis.CONNECTION, Axis.RESPONSIBILITY],
    Axis.RESPONSIBILITY: [Axis.PERSPECTIVE, Axis.CAUSATION],
}
```

*Rationale:* Form and Connection share "notice-vs-link" symmetry (Scenario 2 uses this). Causation and Change are mechanism/time companions. Responsibility depends on Perspective as prerequisite.

### 2.5 Session outcome record

Written at session end.

```python
class SessionOutcome(BaseModel):
    session_id: str
    device_id: str
    axis: Axis                                     # the `progression.topic_axis` of the activity
    entry_rung: Rung
    exit_rung: Rung                                # may differ if within-activity demote fired
    within_activity_outcomes: list[Outcome]        # per-round trail
    final_result: Outcome                          # summarized: promote | hold | demote
    dignity_reframe_fired: bool
    soft_reframe_count: int
    sibling_jump_applied: bool                     # true when game_selector pivoted to sibling axis
```

---

## 3 · DB schemas

### 3.1 New tables

```sql
-- backend/db.py (append to PRAGMA/schema block)
CREATE TABLE IF NOT EXISTS device_progression (
    device_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    policy_version TEXT NOT NULL DEFAULT 'v1_default',
    created_at DATETIME DEFAULT (datetime('now','localtime')),
    updated_at DATETIME DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS session_outcomes (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
    device_id TEXT NOT NULL,
    axis TEXT NOT NULL,
    entry_rung TEXT NOT NULL,
    exit_rung TEXT NOT NULL,
    final_result TEXT NOT NULL,
    within_activity_outcomes_json TEXT,
    dignity_reframe_fired INTEGER DEFAULT 0,
    soft_reframe_count INTEGER DEFAULT 0,
    sibling_jump_applied INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_session_outcomes_device_axis
    ON session_outcomes(device_id, axis, created_at);
```

Demo has no multi-device; it uses a stable `device_id = "demo-local"` constant.

---

## 4 · API surface additions

### 4.1 Endpoints

Demo adds exactly one new endpoint and augments existing responses minimally:

**New endpoint — GET `/progression/snapshot`**

Returns the full rung-per-axis state for the debug panel. Keyed off a query param, defaulting to `demo-local`:

```
GET /progression/snapshot?device_id=demo-local
```

**Modified — session end response**

Returns the same `progression: {...}` block wonderlens-ai does.

No changes to `/session/start` API shape — progression loading happens server-side only.

---

## 5 · Task plan (bite-sized)

5 tasks: worktree setup → port the progression package → wire into server + turn handling → frontend debug panel → verify + PR. Logic parity with the backend is verified by running the **same test vector** (fixture is copied from the backend repo in Task 2).

---

### Task 1: Worktree setup

**Files:**
- Create: `.worktrees/feat/progression-runtime/` in this repo

- [ ] **Step 1: Create the worktree**

Run:
```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo
git fetch origin
git worktree add .worktrees/feat/progression-runtime -b feat/progression-runtime origin/main
```

Expected: worktree created, new branch `feat/progression-runtime` tracking origin/main.

- [ ] **Step 2: Verify tests pass before any changes**

```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/progression-runtime
python -m pytest backend/tests -x -q
```
Expected: all tests pass (baseline).

- [ ] **Step 3: No commit yet — setup only.**

All file paths in subsequent tasks are relative to `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/progression-runtime`.

---

### Task 2: Port progression package + copy shared test vector

**Files (fullstack-demo only):**
- Create: `backend/progression/__init__.py`
- Create: `backend/progression/models.py`
- Create: `backend/progression/sibling_pairs.py`
- Create: `backend/progression/rules.py`
- Create: `backend/progression/policy.py`
- Create: `backend/progression/dignity.py`
- Create: `backend/progression/service.py`
- Create: `backend/progression/policy_profiles.yaml`

Demo uses dataclasses instead of Pydantic (its existing style).

- [ ] **Step 1: Port models.py**

`backend/progression/models.py`:
```python
"""Progression models — dataclass port of wonderlens-ai's Pydantic variant.

Field names and semantics MUST match 1:1 with
wonderlens-ai/app/modules/activity/progression/models.py
so the shared test vector applies identically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import total_ordering


class Axis(str, Enum):
    FORM = "form"
    FUNCTION = "function"
    CAUSATION = "causation"
    CHANGE = "change"
    CONNECTION = "connection"
    PERSPECTIVE = "perspective"
    RESPONSIBILITY = "responsibility"


@total_ordering
class Rung(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"

    def __lt__(self, other: "Rung") -> bool:
        order = {"L1": 1, "L2": 2, "L3": 3}
        return order[self.value] < order[other.value]

    def up(self) -> "Rung":
        return {Rung.L1: Rung.L2, Rung.L2: Rung.L3, Rung.L3: Rung.L3}[self]

    def down(self) -> "Rung":
        return {Rung.L1: Rung.L1, Rung.L2: Rung.L1, Rung.L3: Rung.L2}[self]


class Outcome(str, Enum):
    PROMOTE = "promote"
    HOLD = "hold"
    DEMOTE = "demote"
    SOFT_REFRAME = "soft_reframe"


@dataclass
class AxisState:
    axis: Axis
    current_rung: Rung | None = None
    consecutive_axis_successes: int = 0
    consecutive_axis_demotes: int = 0
    last_outcome: Outcome | None = None
    total_sessions_on_axis: int = 0


@dataclass
class ProgressionState:
    device_id: str
    axes: dict[Axis, AxisState] = field(default_factory=dict)
    policy_version: str = "v1_default"
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def axis_state(self, axis: Axis) -> AxisState:
        if axis not in self.axes:
            self.axes[axis] = AxisState(axis=axis)
        return self.axes[axis]


@dataclass
class ProgressionPolicy:
    within_promote_clean_rounds: int = 2
    within_demote_failed_attempts: int = 2
    silence_threshold_trigger_demote_attempt_seconds: float = 6.0
    soft_reframe_fire_after_seconds: float = 10.0
    across_promote_consecutive: int = 3
    across_demote_consecutive: int = 2
    rung_floor: Rung = Rung.L1
    rung_ceiling: Rung = Rung.L3
    enable_sibling_jump: bool = True
    personalization_trigger_sessions: int = 200
    dignity_reframe_instruction: str = (
        'Open with a reframe: "let me show you what I notice first". '
        "Do not say 'let's try again' or 'easier'."
    )
```

- [ ] **Step 2: Port sibling_pairs.py**

`backend/progression/sibling_pairs.py`:
```python
"""Axis kinship — identical table as wonderlens-ai/progression/sibling_pairs.py."""

from __future__ import annotations

from backend.progression.models import Axis


SIBLING_PAIRS: dict[Axis, list[Axis]] = {
    Axis.FORM:           [Axis.CONNECTION, Axis.FUNCTION],
    Axis.FUNCTION:       [Axis.FORM, Axis.CAUSATION],
    Axis.CAUSATION:      [Axis.CHANGE, Axis.CONNECTION],
    Axis.CHANGE:         [Axis.CAUSATION, Axis.CONNECTION],
    Axis.CONNECTION:     [Axis.FORM, Axis.PERSPECTIVE],
    Axis.PERSPECTIVE:    [Axis.CONNECTION, Axis.RESPONSIBILITY],
    Axis.RESPONSIBILITY: [Axis.PERSPECTIVE, Axis.CAUSATION],
}


def sibling_candidates(axis: Axis, exclude: set[Axis] | None = None) -> list[Axis]:
    exclude = exclude or set()
    return [a for a in SIBLING_PAIRS.get(axis, []) if a not in exclude]
```

- [ ] **Step 3: Port rules.py**

Copy the rules logic verbatim from `wonderlens-ai/app/modules/activity/progression/rules.py`, adjusting imports:
- Replace `from app.modules.activity.progression.models import ...` with `from backend.progression.models import ...`
- Replace `from app.modules.activity.progression.sibling_pairs import ...` with `from backend.progression.sibling_pairs import ...`

(The actual rule bodies are identical — this is why we can share the JSON vector.)

- [ ] **Step 4: Port policy.py + YAML**

`backend/progression/policy_profiles.yaml` — copy `app/config/progression_policy_default.yaml` verbatim.

`backend/progression/policy.py`:
```python
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from backend.progression.models import ProgressionPolicy


KNOWN_POLICIES: list[str] = ["v1_default", "v1_strict", "v1_loose"]


@lru_cache(maxsize=1)
def _load_yaml() -> dict[str, dict]:
    path = Path(__file__).with_name("policy_profiles.yaml")
    with path.open() as fh:
        data = yaml.safe_load(fh)
    return data.get("policies", {})


def load_policy(version: str) -> ProgressionPolicy:
    policies = _load_yaml()
    raw = policies.get(version) or policies.get("v1_default", {})
    return ProgressionPolicy(**raw)
```

- [ ] **Step 5: Port dignity.py**

Verbatim copy of the `dignity.py` file from wonderlens-ai.

- [ ] **Step 6: Port service.py (SQLite / aiosqlite variant)**

Demo uses `aiosqlite` directly (not a `DatabaseManager`). Shape:
```python
"""ProgressionService for fullstack-demo — aiosqlite backend."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import aiosqlite

from backend.progression.models import (
    Axis, AxisState, Outcome, ProgressionPolicy, ProgressionState, Rung,
)
from backend.progression.policy import load_policy
from backend.progression.rules import (
    apply_session_outcome, resolve_next_rung, sibling_jump_target,
)


@dataclass
class NextActivityPlan:
    target_axis: Axis
    target_rung: Rung
    sibling_jump_applied: bool
    source_axis: Axis


class ProgressionService:
    def __init__(self, *, db_path: str, policy_version: str = "v1_default") -> None:
        self._db_path = db_path
        self._policy: ProgressionPolicy = load_policy(policy_version)

    def _encode_state(self, state: ProgressionState) -> str:
        # Manual serialization: dataclass asdict + enum normalization
        axes = {
            axis.value: {
                "axis": a.axis.value,
                "current_rung": a.current_rung.value if a.current_rung else None,
                "consecutive_axis_successes": a.consecutive_axis_successes,
                "consecutive_axis_demotes": a.consecutive_axis_demotes,
                "last_outcome": a.last_outcome.value if a.last_outcome else None,
                "total_sessions_on_axis": a.total_sessions_on_axis,
            } for axis, a in state.axes.items()
        }
        return json.dumps({
            "device_id": state.device_id,
            "axes": axes,
            "policy_version": state.policy_version,
        })

    def _decode_state(self, device_id: str, raw: str) -> ProgressionState:
        data = json.loads(raw)
        axes = {}
        for axis_str, raw_axis in data.get("axes", {}).items():
            axis = Axis(axis_str)
            axes[axis] = AxisState(
                axis=axis,
                current_rung=Rung(raw_axis["current_rung"]) if raw_axis.get("current_rung") else None,
                consecutive_axis_successes=raw_axis.get("consecutive_axis_successes", 0),
                consecutive_axis_demotes=raw_axis.get("consecutive_axis_demotes", 0),
                last_outcome=Outcome(raw_axis["last_outcome"]) if raw_axis.get("last_outcome") else None,
                total_sessions_on_axis=raw_axis.get("total_sessions_on_axis", 0),
            )
        return ProgressionState(device_id=device_id, axes=axes,
                                policy_version=data.get("policy_version", "v1_default"))

    async def load_state(self, device_id: str) -> ProgressionState:
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT state_json FROM device_progression WHERE device_id = ?",
                (device_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return ProgressionState(device_id=device_id)
        return self._decode_state(device_id, row[0])

    async def save(self, state: ProgressionState) -> None:
        payload = self._encode_state(state)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO device_progression (device_id, state_json, policy_version)
                VALUES (?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    state_json = excluded.state_json,
                    policy_version = excluded.policy_version,
                    updated_at = datetime('now','localtime')
                """,
                (state.device_id, payload, state.policy_version),
            )
            await db.commit()

    async def plan_next_activity(self, device_id: str, axis: Axis) -> NextActivityPlan:
        state = await self.load_state(device_id)
        jump = sibling_jump_target(state, axis, self._policy)
        if jump is not None:
            return NextActivityPlan(
                target_axis=jump.axis, target_rung=jump.rung,
                sibling_jump_applied=True, source_axis=axis,
            )
        rung = resolve_next_rung(state, axis, self._policy)
        return NextActivityPlan(
            target_axis=axis, target_rung=rung,
            sibling_jump_applied=False, source_axis=axis,
        )

    async def apply_session_result(
        self, *, session_id: str, device_id: str, axis: Axis,
        entry_rung: Rung, exit_rung: Rung,
        within_activity_outcomes: list[Outcome],
        soft_reframe_count: int, dignity_reframe_fired: bool,
        sibling_jump_applied: bool,
    ) -> Outcome:
        if any(o == Outcome.DEMOTE for o in within_activity_outcomes):
            final = Outcome.DEMOTE
        elif any(o == Outcome.PROMOTE for o in within_activity_outcomes):
            final = Outcome.PROMOTE
        elif any(o == Outcome.SOFT_REFRAME for o in within_activity_outcomes):
            final = Outcome.SOFT_REFRAME
        else:
            final = Outcome.HOLD

        state = await self.load_state(device_id)
        apply_session_outcome(state, axis, entry_rung, final, self._policy)
        await self.save(state)

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO session_outcomes
                    (session_id, device_id, axis, entry_rung, exit_rung, final_result,
                     within_activity_outcomes_json, dignity_reframe_fired,
                     soft_reframe_count, sibling_jump_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, device_id, axis.value, entry_rung.value, exit_rung.value,
                    final.value,
                    json.dumps([o.value for o in within_activity_outcomes]),
                    1 if dignity_reframe_fired else 0,
                    soft_reframe_count,
                    1 if sibling_jump_applied else 0,
                ),
            )
            await db.commit()
        return final
```

- [ ] **Step 7: Write failing `__init__.py`**

`backend/progression/__init__.py`:
```python
from backend.progression.models import (
    Axis, Rung, Outcome, AxisState, ProgressionState, ProgressionPolicy,
)
from backend.progression.service import ProgressionService, NextActivityPlan

__all__ = [
    "Axis", "Rung", "Outcome", "AxisState",
    "ProgressionState", "ProgressionPolicy",
    "ProgressionService", "NextActivityPlan",
]
```

- [ ] **Step 8: Copy the shared test vector JSON from the backend repo**

The canonical fixture was created in the backend plan's Task 14. Copy it verbatim — any divergence is a parity failure.

```bash
mkdir -p backend/tests/progression/fixtures
cp /Users/pharrelly/codebase/gitlab/wonderlens-ai/.worktrees/feat/progression-runtime/tests/modules/activity/progression/fixtures/progression_scenarios.json \
   backend/tests/progression/fixtures/progression_scenarios.json
```

If the backend worktree isn't present, either check out the backend branch first or fetch the JSON from the backend repo's `feat/progression-runtime` branch on GitLab. Do NOT hand-recreate — byte-level parity matters.

- [ ] **Step 9: Port the scenario-vector test runner**

Copy `tests/modules/activity/progression/test_scenarios_vector.py` from the backend worktree to `backend/tests/progression/test_scenarios_vector.py`, adjusting imports:
- `from app.modules.activity.progression.*` → `from backend.progression.*`
- Replace `DatabaseManager` + `create_progression_tables` with direct `aiosqlite` table creation in `tmp_path / "t.db"`:

```python
import aiosqlite
import json
from pathlib import Path

import pytest

from backend.progression.models import Axis, Outcome, Rung
from backend.progression.policy import load_policy
from backend.progression.rules import RoundSignal, classify_round_trail
from backend.progression.service import ProgressionService


FIXTURE = Path(__file__).parent / "fixtures" / "progression_scenarios.json"

_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS device_progression (
        device_id TEXT PRIMARY KEY, state_json TEXT NOT NULL,
        policy_version TEXT NOT NULL DEFAULT 'v1_default',
        created_at DATETIME, updated_at DATETIME)""",
    """CREATE TABLE IF NOT EXISTS session_outcomes (
        session_id TEXT PRIMARY KEY, device_id TEXT NOT NULL,
        axis TEXT NOT NULL, entry_rung TEXT NOT NULL, exit_rung TEXT NOT NULL,
        final_result TEXT NOT NULL, within_activity_outcomes_json TEXT,
        dignity_reframe_fired INTEGER DEFAULT 0,
        soft_reframe_count INTEGER DEFAULT 0,
        sibling_jump_applied INTEGER DEFAULT 0,
        created_at DATETIME)""",
]


@pytest.fixture
async def svc(tmp_path):
    db_path = str(tmp_path / "t.db")
    async with aiosqlite.connect(db_path) as db:
        for ddl in _SCHEMA:
            await db.execute(ddl)
        await db.commit()
    return ProgressionService(db_path=db_path, policy_version="v1_default")


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", json.loads(FIXTURE.read_text())["scenarios"], ids=lambda s: s["name"])
async def test_scenario_playthrough(scenario, svc):
    service = await svc
    policy = load_policy("v1_default")

    for idx, session in enumerate(scenario["sessions"]):
        signals = [RoundSignal(round_index=i, **raw) for i, raw in enumerate(session["round_signals"])]
        final = classify_round_trail(signals, policy)
        assert final.value == session["expected_outcome"], (
            f"{scenario['name']} session {idx}: expected {session['expected_outcome']}, got {final.value}"
        )
        await service.apply_session_result(
            session_id=f"{scenario['name']}-{idx}",
            device_id=scenario["device_id"],
            axis=Axis(session["axis"]),
            entry_rung=Rung(session["entry_rung"]),
            exit_rung=Rung(session["entry_rung"]) if final != Outcome.DEMOTE else Rung(session["entry_rung"]).down(),
            within_activity_outcomes=[final],
            soft_reframe_count=1 if final == Outcome.SOFT_REFRAME else 0,
            dignity_reframe_fired=(final == Outcome.DEMOTE),
            sibling_jump_applied=False,
        )

    state = await service.load_state(scenario["device_id"])
    for axis_name, expected in scenario["expected_final_state"].items():
        axis = Axis(axis_name)
        actual = state.axes[axis]
        for field, expected_value in expected.items():
            if field == "current_rung":
                assert actual.current_rung is not None and actual.current_rung.value == expected_value
            else:
                assert getattr(actual, field) == expected_value

    if "expected_next_plan" in scenario:
        last_axis = Axis(scenario["sessions"][-1]["axis"])
        plan = await service.plan_next_activity(scenario["device_id"], last_axis)
        exp = scenario["expected_next_plan"]
        if "sibling_jump_applied" in exp:
            assert plan.sibling_jump_applied == exp["sibling_jump_applied"]
        if "target_rung" in exp:
            assert plan.target_rung.value == exp["target_rung"]
        if "target_axis" in exp:
            assert plan.target_axis.value == exp["target_axis"]
```

- [ ] **Step 10: Run the shared vector**

```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/progression-runtime
python -m pytest backend/tests/progression/test_scenarios_vector.py -x -v
```
Expected: 4 scenario tests pass, same outcomes as the backend repo.

- [ ] **Step 11: Commit**

```bash
git add backend/progression/ backend/tests/progression/
git commit -m "feat(progression): port runtime engine to fullstack-demo + shared scenario vector"
```

---

### Task 3: Wire ProgressionService into server

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/server.py`
- Modify: `backend/turn_handling/rounds.py`
- Modify: `backend/turn_handling/collection.py`

- [ ] **Step 1: Add progression tables to `backend/db.py`**

Append to the schema block (near the existing `CREATE TABLE` statements):
```python
CREATE TABLE IF NOT EXISTS device_progression (
    device_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    policy_version TEXT NOT NULL DEFAULT 'v1_default',
    created_at DATETIME DEFAULT (datetime('now','localtime')),
    updated_at DATETIME DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS session_outcomes (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),
    device_id TEXT NOT NULL,
    axis TEXT NOT NULL,
    entry_rung TEXT NOT NULL,
    exit_rung TEXT NOT NULL,
    final_result TEXT NOT NULL,
    within_activity_outcomes_json TEXT,
    dignity_reframe_fired INTEGER DEFAULT 0,
    soft_reframe_count INTEGER DEFAULT 0,
    sibling_jump_applied INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_session_outcomes_device_axis
    ON session_outcomes(device_id, axis, created_at);
```

- [ ] **Step 2: Add `GET /progression/snapshot` endpoint**

In `backend/server.py`, after existing routes, add:
```python
from backend.progression.service import ProgressionService
from backend.progression.models import Axis

_DEMO_DEVICE = "demo-local"


@app.get("/progression/snapshot")
async def progression_snapshot(device_id: str = _DEMO_DEVICE):
    svc = ProgressionService(db_path=DB_PATH)
    state = await svc.load_state(device_id)
    # Convert to JSON-ready dict
    return {
        "device_id": state.device_id,
        "axes": {
            a.value: {
                "current_rung": s.current_rung.value if s.current_rung else None,
                "consecutive_axis_successes": s.consecutive_axis_successes,
                "consecutive_axis_demotes": s.consecutive_axis_demotes,
                "last_outcome": s.last_outcome.value if s.last_outcome else None,
                "total_sessions_on_axis": s.total_sessions_on_axis,
            }
            for a, s in state.axes.items()
        },
        "policy_version": state.policy_version,
    }
```

- [ ] **Step 3: Hook round-outcome collection into turn handling**

In `backend/turn_handling/rounds.py`, at the point where a round resolves (the function that advances to the next round), record a `RoundSignal`-shaped dict into the session's in-memory progression trail. Store this on the session state object and flush at session end.

Specific location: find the function that returns after a completed round (search for `"response_type": "round"` or the equivalent). Add:
```python
from backend.progression.rules import RoundSignal

# Inside the round-finishing path, build a signal:
signal = RoundSignal(
    round_index=session.current_round,
    was_correct=not silence_detected,
    silence_seconds=6.5 if silence_detected else 0.0,
)
session.setdefault("progression_trail", []).append(asdict(signal))
```

Same pattern in `backend/turn_handling/collection.py` for Cat5 detail-phase rounds.

- [ ] **Step 4: Apply session outcome on session end**

In `server.py`'s session-end handler (search for `update_session_status(..., "ended"`), before returning:
```python
signals_raw = session_state.get("progression_trail") or []
if signals_raw:
    from backend.progression.rules import RoundSignal, classify_round_trail
    from backend.progression.models import Axis, Rung, Outcome
    from backend.progression.policy import load_policy

    policy = load_policy("v1_default")
    signals = [RoundSignal(round_index=i, **{k: v for k, v in s.items() if k != "round_index"})
               for i, s in enumerate(signals_raw)]
    per_round = [classify_round_trail(signals[:i+1], policy) for i in range(len(signals))]

    axis = Axis(session_state.get("topic_axis", "form"))
    entry_rung = Rung(session_state.get("target_rung", "L1"))
    exit_rung = entry_rung if per_round[-1] != Outcome.DEMOTE else entry_rung.down()
    soft_count = sum(1 for o in per_round if o == Outcome.SOFT_REFRAME)
    dignity = any(o == Outcome.DEMOTE for o in per_round)

    svc = ProgressionService(db_path=DB_PATH)
    await svc.apply_session_result(
        session_id=session_id,
        device_id=_DEMO_DEVICE,
        axis=axis,
        entry_rung=entry_rung,
        exit_rung=exit_rung,
        within_activity_outcomes=per_round,
        soft_reframe_count=soft_count,
        dignity_reframe_fired=dignity,
        sibling_jump_applied=bool(session_state.get("sibling_jump_applied")),
    )
```

- [ ] **Step 5: Run backend smoke test**

```bash
python -m backend.server &
sleep 2
curl http://localhost:8000/progression/snapshot | python -m json.tool
kill %1
```
Expected: empty axes dict for fresh device, 200 OK.

- [ ] **Step 6: Commit**

```bash
git add backend/db.py backend/server.py backend/turn_handling/rounds.py backend/turn_handling/collection.py
git commit -m "feat(progression): wire runtime service into demo server + turn handling"
```

---

### Task 4: Frontend ProgressionSnapshot debug panel

**Files:**
- Create: `frontend/src/components/ProgressionSnapshot.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Create the component**

`frontend/src/components/ProgressionSnapshot.jsx`:
```jsx
import { useEffect, useState } from 'react';

const ALL_AXES = ['form','function','causation','change','connection','perspective','responsibility'];
const RUNG_HEIGHT = { null: 0, 'L1': 33, 'L2': 66, 'L3': 100 };
const RUNG_COLOR = { null: '#ddd', 'L1': '#a8d5a8', 'L2': '#6aa86a', 'L3': '#3e7a3e' };

export default function ProgressionSnapshot({ visible, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!visible) return;
    fetch('/progression/snapshot')
      .then(r => r.json())
      .then(setData)
      .catch(err => setError(err.message));
  }, [visible]);

  if (!visible) return null;
  return (
    <div style={{ position: 'fixed', top: 20, right: 20, width: 320,
                  background: '#fffdf6', border: '1px solid #ccc',
                  padding: 16, borderRadius: 6, zIndex: 9999,
                  fontFamily: 'system-ui, sans-serif', fontSize: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <strong>Progression snapshot</strong>
        <button onClick={onClose} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>×</button>
      </div>
      {error && <div style={{ color: '#a00' }}>Error: {error}</div>}
      {data && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${ALL_AXES.length}, 1fr)`, gap: 4, height: 80 }}>
            {ALL_AXES.map(axis => {
              const rung = data.axes?.[axis]?.current_rung ?? null;
              return (
                <div key={axis} style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', flexDirection: 'column-reverse',
                                height: 60, border: '1px solid #eee', background: '#fafafa' }}>
                    <div style={{ height: `${RUNG_HEIGHT[rung]}%`, background: RUNG_COLOR[rung], transition: 'height 0.3s' }} />
                  </div>
                  <div style={{ fontSize: 9, marginTop: 3 }}>{axis.slice(0,4)}</div>
                  <div style={{ fontSize: 9, color: '#666' }}>{rung ?? '—'}</div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 10, fontSize: 10, color: '#666' }}>
            Policy: <code>{data.policy_version}</code>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add toggle in App.jsx**

In `frontend/src/App.jsx`, add state + mount:
```jsx
import ProgressionSnapshot from './components/ProgressionSnapshot.jsx';

// Inside App component:
const [showProgression, setShowProgression] = useState(false);

// Somewhere in the header/controls area:
<button onClick={() => setShowProgression(v => !v)}>Progression</button>
<ProgressionSnapshot visible={showProgression} onClose={() => setShowProgression(false)} />
```

- [ ] **Step 3: Smoke test the frontend**

```bash
cd frontend
npm run dev &
# open http://localhost:5173, click "Progression" button
# verify panel shows with 7 axes, all empty for fresh demo
```

- [ ] **Step 4: Run vitest**

```bash
cd frontend
npm test -- --run
```
Expected: existing tests pass; no new tests for this component in V1 (debug UI only).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProgressionSnapshot.jsx frontend/src/App.jsx
git commit -m "feat(progression): add debug snapshot panel to demo frontend"
```

---

### Task 5: Verification + PR

- [ ] **Step 1: Run backend + shared vector**

```bash
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/progression-runtime
python -m pytest backend/tests -x -q
```
Expected: all pass including the 4 scenario vector tests.

- [ ] **Step 2: End-to-end smoke test**

Start backend, open frontend, click through a full session, verify `/progression/snapshot` after session end shows a non-empty axes object.

- [ ] **Step 3: Push + open PR**

```bash
git push -u origin feat/progression-runtime
gh pr create --title "feat(progression): runtime engine (demo port)" \
             --body "Mirrors wonderlens-ai's backend implementation. Shares the progression_scenarios.json test vector (byte-identical copy from the backend repo). See docs/plans/2026-04-21-progression-runtime-demo.md."
```

- [ ] **Step 4: Run `pr-review-toolkit:code-reviewer` + `pr-review-toolkit:code-simplifier`**

Per `memory/feedback_review_simplify.md`. Fold any `Important` findings as follow-up commits on the branch before requesting review.

---

## 6 · Known V1 limitations (documented, not fixed)

These are intentional scope cuts. Fixing them is follow-up work.

1. **Outcome classification from raw dialogue is shallow.** V1 uses placeholder heuristics (silent → silence, non-empty → correct). A proper classifier calls the LLM on each (prompt, child response) pair and returns `was_correct`, `was_spontaneous_l_plus_1`, `prompt_was_repeated_by_child` labels. That's a separate design (`2026-04-XX-outcome-classifier-llm-design.md`, future).

2. **`topic_axis` needs to live in every gold-standard game definition.** Tier A/B games currently don't all have explicit axis metadata. A follow-up task inventories the 12 gold standards and adds missing `progression.topic_axis` fields.

3. **Tier P property-bridge templates default to `Form` axis.** This is a placeholder — some property bridges are actually Function or Change axis (e.g., Living Rescue → Responsibility). Classification pending.

4. **Personalization pace model is interface-only.** V1 exposes `policy_version` but only ships `v1_default/strict/loose`. The per-child pace model requires ≥200 sessions of data and a separate ML spec.

5. **Parent dashboard rendering of the snapshot** (the 7-axis radial from Scenario 3) — the API feeds it, but the dashboard UI wiring is in a separate plan (`parent_growth_path_preview.html` §03 curiosity radial integration).

6. **Cross-session continuity beyond last state** — history is stored but not used for smoother promotion curves. V1 is strictly counter-based.

These limitations should be called out in the PR description.

---

## 7 · Cross-repo test vector contract

The file `progression_scenarios.json` is the **single source of truth** for behavioral parity. It's authored in the backend repo (`wonderlens-ai`) and copied verbatim into this demo repo during Task 2. Any change to the rules must:
1. Land in both repos simultaneously.
2. Produce identical outcomes on all 4 scenarios.
3. If a new scenario is required (e.g., to cover personalization-hook behavior), add it to the JSON in the backend repo first, then re-copy into the demo repo.

Divergence between the two implementations = an automatic block on merging either PR.

---

## 8 · Verification checklist (run before shipping)

- [ ] `python -m pytest backend/tests -x -q` — all pass
- [ ] `backend/tests/progression/test_scenarios_vector.py` — 4 scenarios green (same outcomes as the backend repo's equivalent test)
- [ ] `GET /progression/snapshot` reachable; returns empty `axes` dict for a fresh device
- [ ] Frontend debug panel renders 7-axis view after session end
- [ ] `backend/progression/rules.py` is behaviorally identical to `wonderlens-ai/app/modules/activity/progression/rules.py` — same algorithms, adjusted imports only
- [ ] `progression_scenarios.json` byte-identical to the backend repo's copy:
  ```bash
  diff backend/tests/progression/fixtures/progression_scenarios.json \
       /Users/pharrelly/codebase/gitlab/wonderlens-ai/.worktrees/feat/progression-runtime/tests/modules/activity/progression/fixtures/progression_scenarios.json
  ```
  Expected: no output (files identical).
- [ ] Template 0 §07 (autodesign repo) unchanged — runtime follows design, not the other way

---

## 9 · Commit/PR discipline (from user memory)

From `memory/feedback_review_simplify.md`: after each significant feature delivery, run `pr-review-toolkit:code-reviewer` and `pr-review-toolkit:code-simplifier`.

Per-task cadence:
- After each task → run code-reviewer, fix `Important` findings, commit as a follow-up
- After each task → run code-simplifier, keep good suggestions, commit as follow-up
- After Task 5 complete → run final cross-branch code-reviewer before opening the PR

From `memory/feedback_plan_datetime.md`: this plan file is `2026-04-21-progression-runtime-demo.md` — date-prefixed.

From `memory/feedback_worktree_convention.md`: branch under `.worktrees/feat/progression-runtime/` (Task 1 sets this up).

---

## Revnote

- **v0.1** (2026-04-21) — Inaugural demo-mirror plan. 5 tasks: worktree setup · port progression package + scenario vector · wire service into server + turn handling · frontend debug panel · verify + PR. V1 scope: threshold-based rules + sibling-axis jump + dignity reframe + 3 policy profiles (mirrored from backend). Deferred items (§6) match the backend plan. The backend reference implementation ships via `wonderlens-ai/docs/plans/2026-04-21-progression-runtime-backend.md`.
