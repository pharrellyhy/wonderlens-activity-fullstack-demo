# Feedback Gallery Panel

## Context

Testers currently flag issues during a session via `FeedbackQuickFlag` and submit
them through `FeedbackReviewScreen`, which POSTs to `/api/feedback`. Submitted
feedback is persisted as per-session JSON bundles on disk
(`backend/feedback/YYYY-MM-DD-HHMM-{alias}-{sessionshort}/feedback.json` +
`screenshots/*.png`), but there is no way for anyone to browse what has been
collected — the bundles are write-only from the frontend's perspective.

This plan adds a **read-only feedback gallery**: a dedicated view, reached from
the landing page via the `?view=feedback` query param, that fetches every flag
from disk and renders a flat, filterable list with inline screenshot thumbnails
and a lightbox. The goal is to let reviewers (other testers, designers,
stakeholders) scan collected feedback without needing shell access to the
feedback directory.

## Design Decisions

Confirmed with the user during brainstorming:

- **Entry** — separate view via `?view=feedback` query param, linked from a
  small "View feedback gallery →" button on `PhotoSelector`. No React Router;
  follows the existing state-gated conditional-render pattern in `App.jsx`.
- **Shape** — flat list of flags (one card per flag, not per session). Each
  card shows tester alias + session timestamp so session context is preserved.
- **Filters** — tag chip row (`TONE` / `CONFUSING` / `BUG` / `LOVED_IT` / `ALL`)
  + tester alias dropdown + newest/oldest sort toggle. All filtering/sorting is
  client-side since feedback volume is small.
- **Screenshots** — thumbnails inline, click to open a full-screen lightbox.
- **Moderation** — read-only. No delete, no resolve, no edit. Keeps the backend
  to a pair of GET endpoints and avoids auth concerns.

## Architecture

```
PhotoSelector → "View feedback gallery →" → ?view=feedback
                                                   ↓
App.jsx reads query param → renders FeedbackGalleryPanel
                                                   ↓
                             GET /api/feedback/list
                                                   ↓
                 feedback_storage.list_all_feedback()
                                                   ↓
                  walks backend/feedback/*/feedback.json
                                                   ↓
                  flattens flags + attaches session metadata
                                                   ↓
              Panel renders filter bar + flat card list
                                                   ↓
                click thumbnail → ScreenshotLightbox
                                                   ↓
              GET /api/feedback/image/{folder}/{relative_path}
```

## Backend Changes

### `backend/feedback_storage.py` — list/read helpers

Add two functions alongside the existing `write_feedback_bundle`:

- `list_all_feedback(base_dir: Path | None = None) -> list[dict]` — walks
  `base_dir` (defaults to `FEEDBACK_DIR`), loads each `feedback.json`, and
  flattens every flag into an enriched entry:

  ```python
  {
      "flag": {...},                    # full FeedbackFlag dict
      "session": {
          "session_id": str,
          "tester_alias": str,
          "app_mode": str,
          "activity": {...},            # template_type / category / photo_filename
          "session_started_at": str,    # ISO
          "session_ended_at": str,      # ISO
          "folder_name": str,           # on-disk bundle folder
      },
  }
  ```

  Skip folders whose `feedback.json` is missing or malformed (log a warning,
  do not raise). Callers sort — this helper does not.

- `read_feedback_image(folder_name: str, relative_path: str,
  base_dir: Path | None = None) -> bytes | None` — reads a screenshot with
  strict path validation using the existing `_resolve_safe` helper:
  - Reject `folder_name` that contains path separators or `..`
  - Resolve `relative_path` against the bundle root via `_resolve_safe`
  - Return `None` if the file does not exist
  - Any path escape raises `ValueError`

### `backend/server.py` — two GET endpoints

Near the existing `POST /api/feedback` handler:

- `GET /api/feedback/list` — calls `list_all_feedback()`, sorts by
  `flag.flagged_at` descending, returns `{"entries": [...]}` JSON. No pagination.
- `GET /api/feedback/image/{folder_name}/{relative_path:path}` — calls
  `read_feedback_image()`, returns the bytes as a `Response` with the
  MIME type inferred via `mimetypes`. Returns 404 if missing, 400 on unsafe
  path.

### `backend/tests/test_feedback_endpoint.py` — extend existing suite

Add `TestFeedbackListAndImage` class covering:

- `list_all_feedback` happy path with two session folders
- `list_all_feedback` skips a folder whose `feedback.json` is malformed
- `read_feedback_image` happy path returns bytes
- `read_feedback_image` path-traversal rejection: `..`, absolute, nested escape
- `GET /api/feedback/list` returns sorted entries
- `GET /api/feedback/image/...` serves an image and 404s on missing

## Frontend Changes

### `frontend/src/utils/api.js` — two helpers

```js
export async function fetchFeedbackList() {
  const res = await fetch(`${API_BASE}/api/feedback/list`);
  if (!res.ok) throw new Error(`Feedback list failed: ${res.status}`);
  return res.json();
}

export function feedbackImageUrl(folderName, relativePath) {
  return `${API_BASE}/api/feedback/image/${encodeURIComponent(folderName)}/${relativePath
    .split('/')
    .map(encodeURIComponent)
    .join('/')}`;
}
```

### New components under `frontend/src/components/feedback/`

- **`FeedbackGalleryPanel.jsx`** — top-level panel.
  - On mount, `fetchFeedbackList()`; holds `entries`, `loading`, `error`.
  - Filter state: `activeTag`, `activeTester`, `sortOrder` (useState).
  - Computes filtered+sorted list with `useMemo`.
  - Renders header (title, count, back button), filter bar (tag chips, tester
    select, sort toggle), card list, empty state.
  - Manages `lightbox` state for the fullscreen preview.

- **`FeedbackGalleryCard.jsx`** — single flag card.
  - Top row: tag chips (reuse `TAG_STYLES` / `FEEDBACK_TAGS`), relative time,
    tester alias, activity label.
  - Middle: `quick_note` (bold) + optional `review_comment`.
  - Turn context block with `speaker_text` and `child_transcript`.
  - Thumbnail row — one `<img>` per screenshot path, clickable.
  - Styling: `surface-card rounded-2xl p-4`.

- **`ScreenshotLightbox.jsx`** — full-screen overlay.
  - Click backdrop or press Escape to close.
  - Portal-rendered into `document.body`.
  - Image: `max-w-[90vw] max-h-[90vh] rounded-xl`.

### `frontend/src/App.jsx` — gallery route wiring

- Read `window.location.search` for `view=feedback` on mount → `galleryView` state.
- `setGalleryView(on)` uses `history.pushState` to add/remove `?view=feedback`.
- Listen for `popstate` to sync browser navigation.
- In the landing branch (`!sessionId && !loading && !showRetry`), render
  `<FeedbackGalleryPanel onBack={() => setGalleryView(false)} />` when
  `galleryView === true`, otherwise the existing `<PhotoSelector />`.

### `frontend/src/components/PhotoSelector.jsx` — entry link

Add a small text button in the top-right of the header labeled
"View feedback gallery →". Calls an `onOpenGallery` prop wired by `App.jsx`.

## Critical Files

**Backend:**
- `backend/feedback_storage.py` — add `list_all_feedback`, `read_feedback_image`
- `backend/server.py` — add `GET /api/feedback/list` and `GET /api/feedback/image/...`
- `backend/tests/test_feedback_endpoint.py` — extend with `TestFeedbackListAndImage`

**Frontend:**
- `frontend/src/components/feedback/FeedbackGalleryPanel.jsx` (new)
- `frontend/src/components/feedback/FeedbackGalleryCard.jsx` (new)
- `frontend/src/components/feedback/ScreenshotLightbox.jsx` (new)
- `frontend/src/utils/api.js` — add `fetchFeedbackList`, `feedbackImageUrl`
- `frontend/src/App.jsx` — `galleryView` state + URL sync + render branch
- `frontend/src/components/PhotoSelector.jsx` — add "View feedback gallery →" link

**Reused (do not duplicate):**
- `frontend/src/components/feedback/tags.js`, `tagStyles.js` — chip enum + colors
- `.surface-card` / `.surface-primary` tokens from `frontend/src/index.css`
- `backend/feedback_storage._resolve_safe` for path-traversal guarding

## Out of Scope

- Pagination (dataset is tens of entries)
- Delete / resolve / edit (read-only per brainstorm)
- Auth or permission gating on the backend endpoint
- Server-side filtering (all filtering is client-side)
- Mobile-only layout tuning beyond existing responsive utilities
- Any change to feedback submission, `FeedbackQuickFlag`, or `FeedbackReviewScreen`

## Verification

**Backend:**
```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run mypy .
uv run pytest tests/test_feedback_endpoint.py -v
uv run uvicorn server:app --reload --port 8000
# Manual: curl http://localhost:8000/api/feedback/list | jq
```

**Frontend end-to-end:**
1. Start backend and frontend (`npm run dev`).
2. Open `http://localhost:5173`, enable tester mode, run a session, flag 2+
   turns with different tags + a screenshot, submit via the review screen.
3. Return to landing, click "View feedback gallery →" — verify the URL updates
   to `?view=feedback` and the panel renders.
4. Verify new flags appear at the top with correct tags, note, turn context,
   and tester alias.
5. Click a tag chip — verify only matching flags remain.
6. Change the tester dropdown — verify filter works.
7. Toggle sort — verify order reverses.
8. Click a thumbnail — verify the lightbox opens; press Escape to close.
9. Click "← Back to photos" — verify the query param is cleared and
   `PhotoSelector` returns.
10. Use browser back/forward — verify the view state tracks history correctly.

**Post-implementation:**
- Launch `code-reviewer` and `code-simplifier` sub-agents in parallel.
- Update `HANDOFF.md` with a new entry at the top (keep only the last 10).
