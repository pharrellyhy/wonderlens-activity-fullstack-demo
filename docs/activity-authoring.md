# Activity Authoring

## Add A Backend Activity

Add one `backend/games/activity_<slug>.md` file with YAML frontmatter. Use `activity_set: activity_text_game`, preserve the source export id in `source_export_id`, and use user-facing wording that says "activity" instead of "concept" except for "Core IB Key Concepts".

Cat1 activities need `creative_slots.game_mechanic`, `round_scenarios`, step instructions, screen frames, and a badge frame. Cat3 activities use `build_steps`. Cat5 activities need collection slots, `story_scaffold`, `collection_catalog`, and a synthesis instruction.

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
