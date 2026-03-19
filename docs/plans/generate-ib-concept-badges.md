# Plan: Generate IB Concept Badge Images

## Context

The BadgeAward widget currently renders a CSS-only gradient circle with a generic SVG icon for all concepts. We want distinct, generated PNG badge images for each of the 8 IB concepts, displayed during both the celebrating and closing steps. This gives each concept a unique visual identity that children can recognize and associate with what they learned.

## Scope

- **New script**: `scripts/generate_concept_badges_gemini.py`
- **Modified widget**: `frontend/src/widgets/BadgeAward.jsx`
- **New assets**: `frontend/public/badges/` (8 PNGs)
- **Zero backend changes** — existing pipeline already passes `concepts: string[]` via widget_params

## Step 1: Create `scripts/generate_concept_badges_gemini.py`

Follow the exact patterns from `scripts/generate_cat5_icons_gemini.py`:
- Import shared utilities from `generate_cat5_icons_openai.py`: `load_env_file`, `TARGET_SIZE`
- Reuse `generate_image()`, `extract_image()`, `save_icon()`, `get_vertex_client()`, `get_api_key_client()` patterns
- Own `OUT_DIR = ROOT / "frontend" / "public" / "badges"`
- Same CLI: `--only`, `--overwrite`, `--mode` (auto/vertex/api-key)
- Same rate limiting: `BASE_DELAY=15`, `RETRY_DELAY=30`, `MAX_RETRIES=5`

### Concept definitions (8 badges)

| Concept | Filename | Visual Metaphor |
|---------|----------|----------------|
| Perspective | `perspective.png` | Binoculars on a hilltop looking at a landscape |
| Reflection | `reflection.png` | Calm pond reflecting trees and sky |
| Change | `change.png` | Caterpillar and butterfly together on a branch |
| Causation | `causation.png` | Row of falling dominoes |
| Form | `form.png` | Magnifying glass revealing leaf patterns |
| Connection | `connection.png` | Two hands holding a woven friendship bracelet |
| Function | `function.png` | Key fitting into a colorful lock |
| Responsibility | `responsibility.png` | Child's hands cupping a plant seedling |

### Prompt template

```
Create a square illustrated badge icon for a children's learning concept called "{concept}".
Main subject: {description}
Use a warm children's-book illustration style with gentle outlines, soft painterly shading, and natural earth-toned colors.
The image should feel like a badge or emblem — the subject should be centered, large, and framed within a soft circular or shield-shaped border with a warm golden-tan edge.
Show exactly one clear visual metaphor, no text, no letters, no words.
The background must extend to ALL edges of the image — no black borders, no white borders, no empty margins.
Keep the silhouette very clear and easy to recognize at small size for ages 2-8.
Do not add extra objects, characters, labels, text, borders, frames, or watermarks.
```

Data structure: `@dataclass(frozen=True)` with `concept`, `filename`, `description` fields.

## Step 2: Generate badge PNGs

Run the script to produce 8 images in `frontend/public/badges/`. ~2 minutes total (8 images × 15s spacing).

## Step 3: Update `frontend/src/widgets/BadgeAward.jsx`

Replace the single CSS badge circle with concept-specific badge images:

- Map concept name to image: `concept.toLowerCase() + ".png"` → `/badges/perspective.png`
- Each concept renders as: `<img>` (badge PNG) + concept label text below
- Multiple concepts display in a horizontal flex row with staggered animation delays
- **Fallback**: `onError` handler hides broken `<img>` and shows the current CSS gradient circle with SVG BadgeIcon
- When no concepts provided (generic badge): keep existing CSS rendering unchanged

No changes to props or widget_params contract.

## Step 4: Verify

1. Run `scripts/generate_concept_badges_gemini.py --overwrite` — confirm 8 PNGs in `frontend/public/badges/`
2. Start frontend dev server (`cd frontend && npm run dev`)
3. Start a Cat1 session (e.g., mood_changer_dog) — verify badge images appear at:
   - STEP_4_CELEBRATE (role title + concept badges)
   - STEP_5_CLOSING (IB concepts with badge images)
4. Start a Cat5 session (e.g., polka_dot_patrol with 2 concepts) — verify multiple badges display correctly at:
   - STEP_5_CELEBRATE
   - STEP_6_CLOSING
5. Test fallback: temporarily rename a badge file, confirm CSS fallback renders

## Critical files

| File | Action |
|------|--------|
| `scripts/generate_cat5_icons_gemini.py` | Reference pattern (read-only) |
| `scripts/generate_cat5_icons_openai.py` | Import `load_env_file`, `TARGET_SIZE` |
| `frontend/src/widgets/BadgeAward.jsx` | Modify to render badge images |
| `frontend/src/icons/index.js` | Read-only — BadgeIcon import stays for fallback |
| `backend/games/polka_dot_patrol.md` | Read-only — reference for multi-concept testing |
