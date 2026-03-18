# Category 5 Image Asset Plan

## Goal
Add visual images for Cat 5 collection/distractor items. Currently items show a generic LeafIcon; this plan adds per-item images.

## Changes

| File | Change |
|------|--------|
| `backend/server.py` | Add `image` field to `COLLECTION_CATALOGS` items |
| `backend/server.py` | Include `image` in `_session_state_dict()` response |
| `frontend/src/components/PhotoGallery.jsx` | Render `<img>` when `photo.image` exists, fallback to LeafIcon |
| `frontend/public/icons/` | 16 new PNG images (generated externally via DALL-E) |

## Implementation Order

1. Backend: add `image` paths to catalog items
2. Backend: include `image` in frontend API response
3. Frontend: update PhotoGallery to render images
4. Generate actual PNG images externally (ChatGPT/DALL-E)

## Image List (16 new)

### Polka-Dot Patrol (8)
- `spotted_mushroom.png`, `dotted_pebble.png`, `speckled_leaf.png`, `circle_flower.png` (correct)
- `straight_stick.png`, `plain_bark.png`, `long_grass.png`, `smooth_stone.png` (distractors)

### Fluffy Expedition (8)
- `fuzzy_moss.png`, `fluffy_seed.png`, `soft_petal.png`, `woolly_caterpillar.png` (correct)
- `hard_rock.png`, `spiky_pinecone.png`, `rough_bark.png`, `sharp_thorn.png` (distractors)

Note: Backend has 4 additional distractors per game (pine_needle, plain_leaf, forked_twig, acorn_cap for polka_dot; dry_leaf, smooth_pebble, stiff_branch, brittle_shell for fluffy) that need images too for a total of 24.
