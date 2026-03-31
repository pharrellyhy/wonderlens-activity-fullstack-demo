# Phase Timeline Debug Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add phase-level sub-step timelines to the debug panel so developers and stakeholders can see internal state machine phases for Cat5 collection, Cat5 synthesis, and Cat1 invitation flows.

**Architecture:** New `_build_phase_timeline(state)` function in `turn_handler.py` returns a list of phase dicts or `None`. Called from `_build_debug_payload`. Frontend renders as a compact horizontal badge row nested under the step flow in the State tab.

**Tech Stack:** Python (backend), React/JSX + Tailwind (frontend), pytest (tests)

**Spec:** `docs/superpowers/specs/2026-03-31-phase-timeline-debug-design.md`

---

### Task 1: Backend — `_build_phase_timeline` for Cat5 Collection

**Files:**
- Modify: `backend/turn_handler.py:633` (near `_MAX_DETAIL_EXCHANGES`)
- Test: `tests/test_debug_payload.py`

- [ ] **Step 1: Write failing tests for Cat5 collection phase timeline**

Add to `tests/test_debug_payload.py`:

```python
from turn_handler import _build_phase_timeline


class TestBuildPhaseTimelineCat5Collection:
    def test_photo_phase_all_details_pending(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T1",
            collection_phase="photo",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3  # photo + 2 detail slots (T1 max=2)
        assert timeline[0] == {"phase": "photo", "status": "current", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "pending", "label": "Detail 1/2", "meta": None}
        assert timeline[2] == {"phase": "detail", "status": "pending", "label": "Detail 2/2", "meta": {"round_advance_pending": False}}

    def test_detail_phase_first_exchange(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_2",
            tier="T2",
            collection_phase="detail",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 4  # photo + 3 detail slots (T2 max=3)
        assert timeline[0] == {"phase": "photo", "status": "done", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "current", "label": "Detail 1/3", "meta": None}
        assert timeline[2] == {"phase": "detail", "status": "pending", "label": "Detail 2/3", "meta": None}
        assert timeline[3] == {"phase": "detail", "status": "pending", "label": "Detail 3/3", "meta": {"round_advance_pending": False}}

    def test_detail_phase_mid_exchange(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T2",
            collection_phase="detail",
            detail_exchange_count=1,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0] == {"phase": "photo", "status": "done", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "done", "label": "Detail 1/3", "meta": None}
        assert timeline[2] == {"phase": "detail", "status": "current", "label": "Detail 2/3", "meta": None}
        assert timeline[3] == {"phase": "detail", "status": "pending", "label": "Detail 3/3", "meta": {"round_advance_pending": False}}

    def test_round_advance_pending(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="detail",
            detail_exchange_count=1,
            round_advance_pending=True,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        # T0 max=1, so: photo(done) + detail 1/1(done)
        assert len(timeline) == 2
        assert timeline[1] == {"phase": "detail", "status": "done", "label": "Detail 1/1", "meta": {"round_advance_pending": True}}

    def test_t0_single_detail_slot(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="photo",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 2  # photo + 1 detail (T0 max=1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat5Collection -v`
Expected: FAIL — `_build_phase_timeline` not found in imports

- [ ] **Step 3: Implement `_build_phase_timeline` for Cat5 collection**

Add to `backend/turn_handler.py` after `_build_step_flow` (around line 862), before `_build_debug_payload`:

```python
def _build_phase_timeline(state: SessionStateModel) -> list[dict] | None:
    """Build a sub-step phase timeline for steps with internal state machines."""
    step = state.current_step

    if state.template_type == "cat5" and step.startswith("STEP_3_COLLECT"):
        return _phase_timeline_cat5_collection(state)

    return None


def _phase_timeline_cat5_collection(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 collection loop: photo → detail(1..max)."""
    max_detail = _MAX_DETAIL_EXCHANGES.get(state.tier, 3)
    in_detail = state.collection_phase == "detail"
    exchange = state.detail_exchange_count

    timeline: list[dict] = [
        {
            "phase": "photo",
            "status": "done" if in_detail else "current",
            "label": "Photo",
            "meta": None,
        }
    ]

    for i in range(1, max_detail + 1):
        is_last = i == max_detail
        if in_detail:
            if i <= exchange:
                status = "done"
            elif i == exchange + 1:
                status = "done" if state.round_advance_pending else "current"
            else:
                status = "pending"
        else:
            status = "pending"

        meta = None
        if is_last:
            meta = {"round_advance_pending": state.round_advance_pending}

        timeline.append({
            "phase": "detail",
            "status": status,
            "label": f"Detail {i}/{max_detail}",
            "meta": meta,
        })

    return timeline
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat5Collection -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/turn_handler.py tests/test_debug_payload.py
git commit -m "feat(debug): add phase timeline for cat5 collection"
```

---

### Task 2: Backend — `_build_phase_timeline` for Cat5 Synthesis

**Files:**
- Modify: `backend/turn_handler.py` (extend `_build_phase_timeline`)
- Test: `tests/test_debug_payload.py`

- [ ] **Step 1: Write failing tests for Cat5 synthesis phase timeline**

Add to `tests/test_debug_payload.py`:

```python
class TestBuildPhaseTimelineCat5Synthesis:
    def test_invite_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T1",
            synthesis_phase="invite",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 4  # invite, evaluate, improve, generate (T1 has improve)
        assert timeline[0] == {"phase": "invite", "status": "current", "label": "Invite", "meta": None}
        assert timeline[1] == {"phase": "evaluate", "status": "pending", "label": "Evaluate", "meta": None}
        assert timeline[2] == {"phase": "improve", "status": "pending", "label": "Improve", "meta": None}
        assert timeline[3] == {"phase": "generate", "status": "pending", "label": "Generate", "meta": None}

    def test_evaluate_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T2",
            synthesis_phase="evaluate",
            synthesis_prompt_count=1,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"
        assert timeline[1] == {"phase": "evaluate", "status": "current", "label": "Evaluate", "meta": {"prompt_count": 1}}
        assert timeline[2]["status"] == "pending"

    def test_t0_skips_improve(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T0",
            synthesis_phase="invite",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3  # invite, evaluate, generate (no improve for T0)
        phases = [e["phase"] for e in timeline]
        assert "improve" not in phases

    def test_generate_phase_all_done(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T1",
            synthesis_phase="generate",
            synthesis_prompt_count=2,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"  # invite
        assert timeline[1]["status"] == "done"  # evaluate
        assert timeline[2]["status"] == "done"  # improve
        assert timeline[3] == {"phase": "generate", "status": "current", "label": "Generate", "meta": {"prompt_count": 2}}

    def test_improve_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T2",
            synthesis_phase="improve",
            synthesis_prompt_count=1,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"   # invite
        assert timeline[1]["status"] == "done"   # evaluate
        assert timeline[2] == {"phase": "improve", "status": "current", "label": "Improve", "meta": {"prompt_count": 1}}
        assert timeline[3]["status"] == "pending"  # generate
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat5Synthesis -v`
Expected: FAIL — synthesis step not handled yet

- [ ] **Step 3: Implement synthesis timeline**

Add to `backend/turn_handler.py`, after `_phase_timeline_cat5_collection`:

```python
def _phase_timeline_cat5_synthesis(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 synthesis loop: invite → evaluate → improve? → generate."""
    has_improve = state.tier in ("T1", "T2")
    ordered = ["invite", "evaluate"]
    if has_improve:
        ordered.append("improve")
    ordered.append("generate")

    labels = {"invite": "Invite", "evaluate": "Evaluate", "improve": "Improve", "generate": "Generate"}
    current_idx = ordered.index(state.synthesis_phase) if state.synthesis_phase in ordered else 0

    timeline: list[dict] = []
    for i, phase in enumerate(ordered):
        if i < current_idx:
            status = "done"
        elif i == current_idx:
            status = "current"
        else:
            status = "pending"

        meta = None
        if i == current_idx and phase in ("evaluate", "improve", "generate"):
            meta = {"prompt_count": state.synthesis_prompt_count}

        timeline.append({"phase": phase, "status": status, "label": labels[phase], "meta": meta})

    return timeline
```

Update `_build_phase_timeline` to add the synthesis branch:

```python
    if state.template_type == "cat5" and step.startswith("STEP_3_COLLECT"):
        return _phase_timeline_cat5_collection(state)

    if state.template_type == "cat5" and step == "STEP_4_SYNTHESIS":
        return _phase_timeline_cat5_synthesis(state)

    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat5Synthesis -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/turn_handler.py tests/test_debug_payload.py
git commit -m "feat(debug): add phase timeline for cat5 synthesis"
```

---

### Task 3: Backend — `_build_phase_timeline` for Cat1 Invitation

**Files:**
- Modify: `backend/turn_handler.py` (extend `_build_phase_timeline`)
- Test: `tests/test_debug_payload.py`

- [ ] **Step 1: Write failing tests for Cat1 invitation phase timeline**

Add to `tests/test_debug_payload.py`:

```python
class TestBuildPhaseTimelineCat1Invitation:
    def test_initial_invite(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=0,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 1
        assert timeline[0] == {"phase": "invite", "status": "current", "label": "Invite", "meta": None}

    def test_one_decline(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=1,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 2
        assert timeline[0] == {"phase": "invite", "status": "done", "label": "Invite", "meta": None}
        assert timeline[1] == {"phase": "decline", "status": "current", "label": "Decline 1", "meta": None}

    def test_two_declines(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=2,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3
        assert timeline[0]["status"] == "done"
        assert timeline[1] == {"phase": "decline", "status": "done", "label": "Decline 1", "meta": None}
        assert timeline[2] == {"phase": "decline", "status": "current", "label": "Decline 2", "meta": None}

    def test_accepted(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_accepted=True,
            invitation_decline_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 1
        assert timeline[0] == {"phase": "invite", "status": "done", "label": "Invite", "meta": {"accepted": True}}

    def test_non_rules_step_returns_none(self) -> None:
        state = _make_cat1_state(current_step="STEP_3_ROUND_1")
        timeline = _build_phase_timeline(state)

        assert timeline is None

    def test_cat5_non_collection_returns_none(self) -> None:
        state = _make_cat5_state(current_step="STEP_1_HOOK")
        timeline = _build_phase_timeline(state)

        assert timeline is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat1Invitation -v`
Expected: FAIL — cat1 rules not handled yet

- [ ] **Step 3: Implement Cat1 invitation timeline**

Add to `backend/turn_handler.py`, after `_phase_timeline_cat5_synthesis`:

```python
def _phase_timeline_cat1_invitation(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat1 invitation: invite → decline 1 → decline 2."""
    timeline: list[dict] = []

    if state.invitation_accepted:
        timeline.append({"phase": "invite", "status": "done", "label": "Invite", "meta": {"accepted": True}})
        return timeline

    invite_status = "current" if state.invitation_decline_count == 0 else "done"
    timeline.append({"phase": "invite", "status": invite_status, "label": "Invite", "meta": None})

    for i in range(1, state.invitation_decline_count + 1):
        is_latest = i == state.invitation_decline_count
        timeline.append({
            "phase": "decline",
            "status": "current" if is_latest else "done",
            "label": f"Decline {i}",
            "meta": None,
        })

    return timeline
```

Update `_build_phase_timeline` to add the Cat1 branch:

```python
    if state.template_type == "cat1" and step == "STEP_2_RULES":
        return _phase_timeline_cat1_invitation(state)

    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestBuildPhaseTimelineCat1Invitation -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/turn_handler.py tests/test_debug_payload.py
git commit -m "feat(debug): add phase timeline for cat1 invitation"
```

---

### Task 4: Backend — Wire into `_build_debug_payload`

**Files:**
- Modify: `backend/turn_handler.py:911` (inside `_build_debug_payload`)
- Test: `tests/test_debug_payload.py`

- [ ] **Step 1: Write failing test for phase_timeline in debug payload**

Add to `tests/test_debug_payload.py`:

```python
class TestDebugPayloadPhaseTimeline:
    def test_cat5_collection_includes_timeline(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T1",
            collection_phase="detail",
            detail_exchange_count=1,
        )
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" in payload
        assert len(payload["phase_timeline"]) == 3  # photo + 2 details (T1)

    def test_cat1_round_excludes_timeline(self) -> None:
        state = _make_cat1_state(current_step="STEP_3_ROUND_1")
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" not in payload

    def test_cat1_rules_includes_timeline(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=1,
        )
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" in payload
        assert len(payload["phase_timeline"]) == 2  # invite + decline 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py::TestDebugPayloadPhaseTimeline -v`
Expected: FAIL — `phase_timeline` not in payload

- [ ] **Step 3: Wire `_build_phase_timeline` into `_build_debug_payload`**

In `backend/turn_handler.py`, inside `_build_debug_payload`, add after `debug["step_flow"] = _build_step_flow(state)` (line 912):

```python
    timeline = _build_phase_timeline(state)
    if timeline:
        debug["phase_timeline"] = timeline
```

- [ ] **Step 4: Run all debug payload tests**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run ruff check and format**

Run: `cd backend && uv run ruff check ../tests/test_debug_payload.py turn_handler.py && uv run ruff format ../tests/test_debug_payload.py turn_handler.py`

- [ ] **Step 6: Commit**

```bash
git add backend/turn_handler.py tests/test_debug_payload.py
git commit -m "feat(debug): wire phase timeline into debug payload"
```

---

### Task 5: Frontend — PhaseBadge Component and Phase Detail Section

**Files:**
- Modify: `frontend/src/components/DebugPanel.jsx`

- [ ] **Step 1: Add `PhaseBadge` component**

Add after `StepBadge` (around line 100) in `frontend/src/components/DebugPanel.jsx`:

```jsx
const PHASE_STYLES = {
  done:    { color: C.green,    borderColor: C.green },
  current: { color: C.blue,     borderColor: C.blue, backgroundColor: `${C.blue}15` },
  pending: { color: C.surface2, borderColor: C.surface2 },
};

function PhaseBadge({ entry }) {
  const s = PHASE_STYLES[entry.status] || PHASE_STYLES.pending;
  return (
    <span
      className="px-1.5 py-0.5 rounded text-[8px] font-semibold whitespace-nowrap border"
      style={{ color: s.color, borderColor: s.borderColor, backgroundColor: s.backgroundColor }}
    >
      {entry.status === 'done' && <>&zwj;&#10003; </>}{entry.label}
    </span>
  );
}

function PhaseTimeline({ timeline }) {
  if (!timeline || timeline.length === 0) return null;

  return (
    <div className="mt-2 pl-2" style={{ borderLeft: `2px solid ${C.surface0}` }}>
      <SectionTitle>Phase Detail</SectionTitle>
      <div className="flex items-center gap-1 flex-wrap">
        {timeline.map((entry, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <span className="text-[8px]" style={{ color: C.surface2 }}>&rarr;</span>}
            <span className="inline-flex flex-col items-center">
              <PhaseBadge entry={entry} />
              {entry.meta && (
                <span className="text-[7px] mt-0.5" style={{ color: C.overlay0 }}>
                  {Object.entries(entry.meta).map(([k, v]) => `${k}: ${String(v)}`).join(', ')}
                </span>
              )}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add `PhaseTimeline` to `StateMachineTab`**

In `StateMachineTab`, after the step flow `div` and the existing `collectionPhase` badge block (around line 123), add:

Replace this block in column 1:
```jsx
        {isCat5 && collectionPhase && (
          <div className="mt-2">
            <Badge color={C.blue}>{collectionPhase}</Badge>
          </div>
        )}
```

With:
```jsx
        <PhaseTimeline timeline={debugData?.phase_timeline} />
```

This replaces the old standalone `collectionPhase` badge with the richer phase timeline (which subsumes that information).

- [ ] **Step 3: Verify in browser**

Run the dev server and test:
1. Start a Cat5 session — verify phase timeline appears under step flow during collection steps
2. Advance to synthesis — verify synthesis phases render
3. Start a Cat1 session — verify invitation phase shows on STEP_2_RULES
4. Advance past STEP_2_RULES — verify phase timeline disappears

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DebugPanel.jsx
git commit -m "feat(debug): add phase timeline to state tab"
```

---

### Task 6: Frontend — History Tab Phase Indicator

**Files:**
- Modify: `frontend/src/components/DebugPanel.jsx` (HistoryTab)

- [ ] **Step 1: Add inline phase badge to history entries**

In `HistoryTab`, inside the turn entry (around line 400-414), after the existing badges row, add a phase indicator. Find this block:

```jsx
              {entry.llm_output?.tone_marker && (
                <span style={{ color: C.overlay0 }}>[{entry.llm_output.tone_marker}]</span>
              )}
```

Add after it:
```jsx
              {entry.phase_timeline?.find(p => p.status === 'current') && (
                <Badge color={C.yellow}>
                  {entry.phase_timeline.find(p => p.status === 'current').label}
                </Badge>
              )}
```

- [ ] **Step 2: Verify in browser**

Play through several turns and check the History tab:
- Each turn entry should show the active phase as a yellow badge (e.g., "Detail 1/2", "Evaluate")
- Turns on steps without phase timelines should show no phase badge

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DebugPanel.jsx
git commit -m "feat(debug): add phase indicator to history tab"
```

---

### Task 7: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py -v`
Expected: All tests PASS

- [ ] **Step 2: Run ruff check and format**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

- [ ] **Step 3: Run full test suite**

Run: `cd backend && uv run pytest ../tests/ -v --timeout=30`
Expected: All tests PASS (no regressions)

- [ ] **Step 4: Launch code-reviewer and code-simplifier agents**

Run code-reviewer and code-simplifier sub-agents in parallel on all changed files:
- `backend/turn_handler.py`
- `frontend/src/components/DebugPanel.jsx`
- `tests/test_debug_payload.py`
