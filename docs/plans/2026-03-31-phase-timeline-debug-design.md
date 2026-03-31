# Phase Timeline Debug Panel Enhancement

**Date:** 2026-03-31
**Status:** Draft

## Summary

Add granular phase-level state tracking to the debug panel's State tab. A new `phase_timeline` payload in the debug data shows sub-step phases (done/current/pending) for steps that have internal state machines — Cat5 collection loop, Cat5 synthesis loop, and Cat1 invitation flow.

## Motivation

The debug panel currently shows which *step* is active but not which *phase within a step*. Cat5 step 3 (collection) has a photo/detail two-phase loop with tier-dependent exchange counts. Cat5 step 4 (synthesis) has a four-phase state machine (invite → evaluate → improve → generate). Cat1 step 2 (rules) tracks invitation decline count. These internal states are invisible in the current debug panel, making it harder to diagnose prompt/generation issues and to demo the state machine to stakeholders.

## Approach

**Phase timeline model** — a list of phase entries with `done/current/pending` status, matching the existing step flow visual pattern. The backend builds this contextually per step type; the frontend renders it as a compact sub-timeline nested below the step flow.

## Data Model

Each entry in `phase_timeline`:

```python
{
    "phase": str,         # Phase identifier (e.g., "photo", "detail", "invite")
    "status": str,        # "done" | "current" | "pending"
    "label": str,         # Display label (e.g., "Detail 1/2", "Invite")
    "meta": dict | None,  # Optional annotations (round_advance_pending, story_quality, etc.)
}
```

## Per-Step Timeline Definitions

### Cat5 STEP_3_COLLECT_N (current round only)

Phases for one collection round:

| Phase | Label | Notes |
|-------|-------|-------|
| photo | Photo | Selecting a photo from the gallery |
| detail | Detail 1/{max} ... Detail {max}/{max} | Detail-harvesting exchanges; max depends on tier (T0=1, T1=2, T2=3) |

Status assignment:
- If `collection_phase == "photo"`: photo is `current`, all details are `pending`
- If `collection_phase == "detail"`: photo is `done`, details up to `detail_exchange_count` are `done`, next is `current`, rest are `pending`

Metadata on last detail entry: `round_advance_pending: bool`

### Cat5 STEP_4_SYNTHESIS

Fixed phases (tier-dependent):

| Phase | Label | Tiers | Notes |
|-------|-------|-------|-------|
| invite | Invite | All | Ask child to make a story |
| evaluate | Evaluate | All | Classify child's response |
| improve | Improve | T1, T2 only | Ask child to elaborate on weak story |
| generate | Generate | All | AI generates complete story |

Status assigned by comparing `state.synthesis_phase` against the ordered list.

Metadata on current phase:
- `prompt_count`: `state.synthesis_prompt_count`
- `story_quality`: from classification result (when in evaluate/improve phase)

### Cat1 STEP_2_RULES

| Phase | Label | Notes |
|-------|-------|-------|
| invite | Invite | Initial invitation |
| decline_1 | Decline 1 | First decline (only if it happened) |
| decline_2 | Decline 2 | Second decline (only if it happened) |

Status:
- If `invitation_accepted`: invite is `done` with `meta.accepted: true`, no decline entries
- If not accepted: invite is `current` if `invitation_decline_count == 0`; otherwise invite is `done`, and decline entries appear as `done`/`current` based on count

### All Other Steps

`phase_timeline` is `null` — not rendered.

## Backend Changes

### `turn_handler.py`

New function:

```python
def _build_phase_timeline(state: SessionStateModel) -> list[dict] | None:
```

- Inspects `state.current_step`, `state.template_type`, `state.tier`
- Returns the appropriate timeline list or `None`
- Only reads existing state fields — no new model changes

Called from `_build_debug_payload`:

```python
timeline = _build_phase_timeline(state)
if timeline:
    debug["phase_timeline"] = timeline
```

No new schema or model fields required. All data comes from existing `SessionStateModel` fields:
- `collection_phase`, `detail_exchange_count`, `round_advance_pending`
- `synthesis_phase`, `synthesis_prompt_count`
- `invitation_decline_count`, `invitation_accepted`
- `tier` (for detail max lookup)

## Frontend Changes

### `DebugPanel.jsx` — StateMachineTab

Add a **Phase Detail** section below the step flow in column 1:

- Renders only when `debugData?.phase_timeline` is present
- Uses a `PhaseBadge` component — smaller variant of `StepBadge` (8px font)
- Horizontal flow with `→` separators between phases
- Same color scheme: green (done), blue (current), grey (pending)
- Annotations from `meta` appear as small muted labels beneath the relevant badge
- Slight indent or left border to visually nest under step flow
- Hidden entirely when `phase_timeline` is `null`

### `DebugPanel.jsx` — HistoryTab

- Include `phase_timeline` snapshot in `debugHistory` entries
- Render only the *current* phase as a compact inline badge (e.g., `detail 2/3`) — not the full timeline
- Keeps history entries scannable

## Files Modified

| File | Change |
|------|--------|
| `backend/turn_handler.py` | Add `_build_phase_timeline()`, call from `_build_debug_payload()` |
| `frontend/src/components/DebugPanel.jsx` | Add `PhaseBadge`, Phase Detail section in `StateMachineTab`, inline phase in `HistoryTab` |

## Out of Scope

- No new session state fields
- No changes to API response shape (debug is an opaque dict already)
- No per-step retry stats breakdown (separate enhancement)
- No `is_first_on_step` tracking (separate enhancement)
- No state machine diagram visualization
