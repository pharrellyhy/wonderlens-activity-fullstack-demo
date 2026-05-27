# Activity Authoring

## Add A Backend Activity

Add one `backend/games/activity_<slug>.md` file with YAML frontmatter. Use `activity_set: activity_text_game`, preserve the source export id in `source_export_id`, and use user-facing wording that says "activity" instead of "concept" except for "Core IB Key Concepts".

Cat1 activities need `creative_slots.game_mechanic`, `round_scenarios`, step instructions, screen frames, and a badge frame. Cat3 activities use `build_steps`. Cat5 activities need collection slots, `story_scaffold`, `collection_catalog`, and a synthesis instruction.

The catalog endpoint reads loadable games with `activity_set: activity_text_game`; there is no separate frontend registry for text activities. If an activity needs a new category flow, add parser/schema support first, then add the state-machine and turn-handling tests before wiring it into the UI.

Run:

```bash
uv run pytest backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py -q
```

## Add Display Assets

Static assets live under `frontend/public/activity-assets/<activity_id>/` and are listed in `frontend/public/activity-assets/activity-assets.manifest.json`.

Each activity has an `icon.png` and one file per runtime beat. Cat1 and Cat3 usually use `intro`, `rules`, `round_1`, `round_2`, `round_3`, and `recap`. Cat5 activities can add `synthesis`.

Generate source art with Codex built-in imagegen using `frontend/public/activity-assets/prompts/wonderlens-activity-style.md`. Copy selected outputs from `/Users/pharrelly/.codex/generated_images/...` into the project, keeping the originals in place.

Runtime code must not call an image generation API for these display assets. It only reads the committed manifest and static PNGs.

Run:

```bash
cd frontend
npm test -- tests/activityAssets.test.js
```

## Verify The Text Game

Run the focused checks before handing off a new activity:

```bash
uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_activity_text_game_turns.py -q

cd frontend
npm test -- tests/activityAssets.test.js tests/useActivityTextSession.test.jsx tests/WonderLensDevice.test.jsx tests/ActivityGameApp.test.jsx
npm run build
```

For a live backend smoke test, source the backend `.env` and set `GOOGLE_APPLICATION_CREDENTIALS` before starting `uvicorn`. Do not print or commit secret values.

```bash
cd backend
set -a
source .env
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.elaborate-baton-480304-r8-a8a39bcb34f1.json"
uv run uvicorn server:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:5173/?view=activities` with the Vite dev server running from `frontend/`.
