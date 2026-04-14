# Tester Feedback Collection

**Status:** Design • **Date:** 2026-04-13

## Context

The existing `DebugPanel` (`frontend/src/components/DebugPanel.jsx`, 683 lines) is
a rich developer telemetry surface — agent pipeline attempts, verdicts,
latencies, LLM output fields, session state machine, round/phase tracking,
and a per-turn history ring buffer. It's indispensable when debugging the
multi-agent pipeline, but it's the wrong surface for the WonderLens edu
team when they test activities.

Edu team testers care about things like "this line felt preachy", "the dog
wouldn't really say that", "this transition is confusing for a 4-year-old",
"the photo looks cropped weird" — qualitative content feedback tied to a
specific moment in a specific session. Today that feedback arrives through
a mix of Slack messages, screenshots, and verbal notes, and developers have
to reconstruct which turn/step/recipe produced the issue. Context is lost,
follow-up is slow, and testers skip reporting small cuts that never feel
worth the ceremony.

This spec introduces a **tester-facing feedback capture surface** that runs
parallel to the existing debug panel. It is gated behind a visible mode
toggle so developers keep their existing workflow untouched and testers
get a focused UI that matches how they actually work — flag a moment
instantly, expand on it retrospectively, hand devs a self-contained package
of comments + screenshots + turn snapshots.

## Goals

1. **In-the-moment flagging** — one click during play attaches a quick tag
   and auto-screenshot to the current turn without breaking the flow.
2. **Post-session review** — a review screen at the end of the session lets
   testers expand each flagged turn with a longer comment.
3. **Self-contained output** — a single JSON file plus an image folder
   (or a .zip containing both) that a developer can open without any
   additional context.
4. **Zero impact on developer mode** — the existing `DebugPanel` and its
   data flow are untouched when the app is in developer mode.

## Non-goals

- Replacing the `DebugPanel` or folding any of its data into the tester UI.
- Any backend agent/pipeline changes (no new LLM calls, no schema churn
  in `Recipe`, `Turn`, or other existing models).
- Multi-user concurrency or authentication — feedback is collected from
  trusted internal testers running the demo locally or on a staging URL.
- Analytics/aggregation across sessions — this spec only handles *capture*
  and *delivery*. Analysis is out of scope.

## Architecture

### Mode toggle

A single `app_mode` state with two values: `dev` (default) and `tester`.
Source of truth is `localStorage["wl-app-mode"]`; a URL query param
`?mode=tester` sets the localStorage value on page load so devs can send
testers preset links.

A small **Mode pill** component in the top-right corner of the app shell
(outside any existing panel so it's always visible) displays the current
mode and flips it on click. Switching mid-session works instantly — no
reload — because both surfaces are simple conditional mounts on a shared
React state.

| Mode | What's mounted | What's hidden |
|---|---|---|
| `dev` | `DebugPanel` (unchanged), its `Ctrl+D` toggle, its bottom-right button | Tester feedback button + review screen |
| `tester` | `FeedbackFlagButton`, `TesterIdentityModal`, `FeedbackReviewScreen` | `DebugPanel` and its toggle |

The mode pill is always visible regardless of mode.

### Frontend components (new)

All new components live in `frontend/src/components/feedback/` to keep the
feature self-contained.

| File | Purpose |
|---|---|
| `FeedbackFlagButton.jsx` | Floating bottom-right button, always visible in tester mode. Replaces the debug toggle position. Click → opens the quick-flag popover |
| `FeedbackQuickFlag.jsx` | Popover with auto-captured screenshot thumbnail, four tag chips, a short note field (~10 words), Save/Cancel. Triggers `html2canvas` on mount |
| `FeedbackReviewScreen.jsx` | Full-screen overlay shown at session end. Lists every flagged turn with snippet, screenshot, tags, an expandable comment textarea, and a delete button. Bottom actions: Submit, Download .zip |
| `TesterIdentityModal.jsx` | Shown the first time a tester flags something in a session. Asks for an alias, persists to `localStorage["wl-tester-alias"]` |
| `ModePill.jsx` | Top-right corner pill showing current mode, flips on click |

Hook:

| File | Purpose |
|---|---|
| `hooks/useFeedbackStore.js` | In-memory store for the current session's flags, screenshot blobs, and tester identity. Exposes `addFlag`, `updateFlag`, `deleteFlag`, `buildPayload`, `clearSession`. Subscribes to session lifecycle via `useSessionOrchestration` |

### Dependencies

- `html2canvas` (~50KB gzipped) for auto-screenshot of the split-view
  container at flag time. Added to `frontend/package.json`.
- `jszip` (~90KB gzipped) for client-side .zip generation in the Download
  flow. Added to `frontend/package.json`.
- No new backend dependencies — FastAPI already handles multipart uploads.

### Backend endpoint

New endpoint `POST /api/feedback` in `backend/server.py`:

- Accepts `multipart/form-data` with:
  - `feedback` — JSON string matching the schema below
  - `screenshots[]` — one or more PNG blobs; filenames must match the
    paths referenced in the JSON
- Validated via a new `FeedbackPayload` Pydantic model in
  `backend/schemas/feedback.py`
- On success: creates
  `backend/feedback/<YYYY-MM-DD-HHmm>-<alias>-<session-short>/`,
  writes `feedback.json`, writes each blob into `screenshots/`
- Returns `{ "status": "saved", "path": "<relative-path>" }`
- Errors (validation / IO) return structured JSON errors with HTTP 4xx/5xx
- Adds `backend/feedback/` to the repo's `.gitignore` (tester data should
  not be committed)

### File + folder naming

Consistent format across the backend folder and the downloaded zip, so a
downloaded zip dropped into `backend/feedback/` Just Works.

- **Backend folder:** `backend/feedback/2026-04-13-1432-alice-abc123/`
- **Downloaded zip:** `wonderlens-feedback-2026-04-13-1432-alice-abc123.zip`
- **Zip internal structure:** mirrors the backend folder exactly

Name parts:
- `2026-04-13-1432` — local date + 24h time, zero-padded. Generated at
  session end so the timestamp reflects when the tester finished, not when
  they started
- `alice` — tester alias, slugified: lowercased, spaces → `-`,
  non-alphanumeric stripped; falls back to `anon` if the tester skipped the
  identity modal
- `abc123` — 6-char suffix of the existing backend `session_id`, used to
  disambiguate two testers sharing an alias in the same minute

## Data schema

One `feedback.json` per session:

```json
{
  "session_id": "abc123def456",
  "tester_alias": "alice",
  "app_mode": "tester",
  "activity": {
    "template_type": "mood_changer_dog",
    "category": "cat1",
    "photo_filename": "dog-on-couch.jpg"
  },
  "session_started_at": "2026-04-13T14:28:11+08:00",
  "session_ended_at": "2026-04-13T14:32:47+08:00",
  "flags": [
    {
      "flag_id": "f-01",
      "turn_number": 3,
      "flagged_at": "2026-04-13T14:30:02+08:00",
      "tags": ["tone"],
      "quick_note": "too preachy",
      "review_comment": "The dog shouldn't moralize — just react to the photo.",
      "screenshots": [
        "screenshots/turn-03-auto.png",
        "screenshots/turn-03-manual-1.png"
      ],
      "turn_snapshot": {
        "step": "detail_exchange",
        "speaker_text": "Wow, look at that dog! Remember, always treat pets with kindness...",
        "child_transcript": "he looks happy",
        "widget_type": "photo_full",
        "recipe_round": 2
      }
    }
  ]
}
```

Field notes:

- `turn_snapshot` is intentionally small — only the fields a dev needs to
  replay the moment, not the full debug payload. Pulled from the existing
  `debugData` + `debugHistory` ring buffer in
  `frontend/src/hooks/useConversation.js:21` at flag time.
- `review_comment` is `null` until the tester expands the flag in the
  review screen.
- Screenshot paths are relative so the zip is self-contained.
- Timestamps are ISO-8601 with local timezone offset.
- `tags` is an ordered array of strings (not an enum in JSON — the
  taxonomy is enforced in the `FeedbackPayload` Pydantic model).

## Tag taxonomy

Starter set of four chips on the quick-flag popover — tappable in under a
second, not mutually exclusive (a flag can carry multiple tags):

| ID (machine) | Label (display) | When to use | Color |
|---|---|---|---|
| `tone` | Tone | Voice/wording feels off — too adult, flat, preachy, wrong vibe | amber |
| `confusing` | Confusing | Child would be lost here — unclear instruction, broken flow, dead-end | rose |
| `bug` | Bug | Something's visibly broken — crop, overlap, wrong photo, stuck state | red |
| `loved_it` | Loved it | A great moment worth keeping or replicating | green |

The machine ID is what lands in `flags[].tags[]` in JSON and is what the
Pydantic model validates against; the label is only used for the chip UI.
Defined once in `frontend/src/components/feedback/tags.js` and referenced
by the popover, review screen, and Pydantic model. Adding a new tag later
is a one-line change.

## User flow

1. Edu team tester opens the demo URL (localhost or staging).
2. First time ever: they click the **Mode pill** in the top-right corner
   to switch from Dev → Tester. The pill persists the choice. Devs may
   send a `?mode=tester` link to do this automatically.
3. They pick a photo and the activity starts normally.
4. On turn 3 the dog says something that feels off. They click the
   **floating flag button** (bottom-right).
5. First flag of the session → **identity modal** appears asking for an
   alias. They type "Alice" and continue. Alias is stored in
   localStorage, so subsequent sessions skip this modal.
6. **Quick-flag popover** opens with the auto-captured screenshot visible,
   four tag chips, and a short note field. Alice taps `tone`, types
   "too preachy", hits Save. Popover closes in ~1s. Activity keeps flowing.
7. Session ends naturally (or Alice clicks an End Session button on the
   ending screen). **Review screen** opens full-screen, listing the three
   turns Alice flagged during play.
8. Alice expands two flags with longer comments; the third was a mis-tap,
   she deletes it.
9. She clicks **Submit** → frontend POSTs multipart form-data to
   `/api/feedback` → backend writes files → success toast. Alternative:
   **Download .zip** button produces a self-contained zip file for
   staging builds where she can't reach the backend filesystem.
10. The review screen closes and the app returns to the photo picker,
    ready for another session. `useFeedbackStore.clearSession()` resets.

## Critical files to modify / create

### New

- `frontend/src/components/feedback/FeedbackFlagButton.jsx`
- `frontend/src/components/feedback/FeedbackQuickFlag.jsx`
- `frontend/src/components/feedback/FeedbackReviewScreen.jsx`
- `frontend/src/components/feedback/TesterIdentityModal.jsx`
- `frontend/src/components/feedback/ModePill.jsx`
- `frontend/src/components/feedback/tags.js`
- `frontend/src/hooks/useFeedbackStore.js`
- `frontend/src/utils/buildFeedbackZip.js` (wraps `jszip`)
- `frontend/src/utils/captureScreenshot.js` (wraps `html2canvas`)
- `backend/schemas/feedback.py` — `FeedbackPayload`, `FeedbackFlag`,
  `TurnSnapshot` models
- `backend/feedback_storage.py` — pure helpers: folder naming, path
  resolution, file writing. Pulled out so `server.py` stays thin
- `frontend/tests/useFeedbackStore.test.js` (Vitest)
- `backend/tests/test_feedback_endpoint.py` (pytest + `TestClient`)

### Modified

- `frontend/src/App.jsx` — read `app_mode` from localStorage, conditionally
  mount `<DebugPanel>` vs the feedback components, always render
  `<ModePill>`
- `frontend/src/hooks/useConversation.js` — expose the most recent
  `debugData` entry to `useFeedbackStore` so it can snapshot on flag
  (the existing ring buffer at line 21 is reused; no new state added)
- `frontend/package.json` — add `html2canvas`, `jszip`
- `backend/server.py` — import new schemas + storage helpers, add
  `POST /api/feedback`
- `.gitignore` — add `backend/feedback/`

### Explicitly NOT modified

- `frontend/src/components/DebugPanel.jsx` — zero changes
- Any agent file under `backend/agents/` — zero changes
- Any existing recipe/turn/STT/TTS endpoint
- `backend/tier_rules.yaml`, scenarios, fallbacks
- The existing `/api/start`, `/api/turn`, `/api/stt`, `/api/tts` endpoints

## Reused utilities

- **Existing `debugData` / `debugHistory`** in
  `frontend/src/hooks/useConversation.js:20-43` — the turn snapshot for
  each flag is sliced from these, no new event bus needed.
- **Existing `session_id`** from `/api/start` response — truncate for the
  folder suffix; don't generate a new ID client-side.
- **Existing session orchestration** in
  `frontend/src/hooks/useSessionOrchestration.js` — `useFeedbackStore`
  subscribes to session-start and session-end events here rather than
  inventing a new lifecycle mechanism.
- **Existing Tailwind + Catppuccin palette** already used by the demo —
  tester UI uses the same tokens for visual consistency.

## Verification

1. **Frontend unit test (`useFeedbackStore.test.js`)**
   - Adding a flag stores it with a generated `flag_id`
   - Deleting a flag removes it
   - `tester_alias` persists to localStorage and is read back on reload
   - `buildPayload()` produces JSON matching the schema above
2. **Dev mode regression (manual)**
   - Launch app with no localStorage → `DebugPanel` behaves exactly as
     before, `Ctrl+D` still toggles it, no feedback UI visible
3. **Tester mode end-to-end (manual)**
   - Click Mode pill → debug panel vanishes, flag button appears
   - Play a full Cat1 session, flag 2 turns with different tag combos,
     type a quick note each time
   - Verify the identity modal shows exactly once
   - End the session → review screen lists both flags with screenshots
   - Add a longer `review_comment` to one flag, delete the other
   - Click **Download** → open the resulting zip, confirm
     `feedback.json` schema is correct and `screenshots/` contains the
     auto-captured PNG
   - Click **Submit** → confirm `backend/feedback/<folder>/` contains the
     same files
4. **Backend test (`test_feedback_endpoint.py`)**
   - Happy path: post a multipart body with valid JSON + one PNG, assert
     files land at the expected path and response shape is correct
   - Validation: post with an unknown tag and assert 422 + error payload
   - Validation: post with `screenshots[]` paths that don't match uploaded
     filenames and assert 422
5. **Lint + type-check**
   - `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest`
   - `cd frontend && npm run lint && npm test`

## Out of scope / future work

- Aggregation dashboard across sessions
- Automatic PR/issue creation from feedback
- Feedback diffing across recipe iterations
- Voice-recorded comments (nice for busy testers but adds ASR complexity)
