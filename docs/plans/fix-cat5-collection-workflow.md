# Fix Cat 5 Out-of-Device Collection Workflow

## Context

The Cat 5 (out-of-device collection) activities — `polka_dot_patrol` and `fluffy_expedition_dandelion` — have four bugs:

1. **AI dialogue doesn't guide child to find/collect** — jumps straight to questions about the photo
2. **Round counter off-by-one** — status bar shows "Round: 4/4" while screen shows "3 of 4 found"
3. **Both activities show identical grid items** — same 6 hardcoded nature items
4. **Same grid every round** — no per-round variation; should be 3 items per round (1 correct + 2 distractors)

## Files Modified

| File | Changes |
|------|---------|
| `backend/schemas/session_state.py` | Add `round_items` field |
| `backend/server.py` | Add catalogs, `generate_round_items()`, update validation, update state dict |
| `frontend/src/components/PhotoGallery.jsx` | Accept `items` prop, remove hardcoded array |
| `frontend/src/App.jsx` | Pass round items to PhotoGallery, fix round counter |
| `backend/skills/step_instructions/cat5_step2_mission.md` | Add "go explore" call-to-action |
| `backend/skills/step_instructions/cat5_step3_collect.md` | Add "go find next item" preamble |

## Implementation Order

1. Backend schema — `round_items` field
2. Backend server — catalogs, generation, validation, state dict
3. Frontend PhotoGallery — dynamic items from props
4. Frontend App.jsx — pass items, fix round counter
5. Prompt templates — "go find" language
