# Hover Effect, Distinct Celebration Image, In-Image Caption

**Date:** 2026-04-11
**Scope:**
- `frontend/src/widgets/StoryScene.jsx`
- `frontend/src/widgets/AchievementImage.jsx`
- `frontend/src/widgets/PhotoDisplay.jsx` (background photo)
- `backend/turn_handling/synthesis.py` (LLM prompt for image descriptions)
- `backend/image_gen.py` (style prefix)

## Problem

Three separate refinements to the synthesis visuals:

### 1. Images should have a hover effect
The child sits in front of the device and occasionally hovers over images
with a mouse / finger. Right now the rendered images (`StoryScene`,
`AchievementImage`, `PhotoDisplay`) are inert — no feedback when the user
interacts with them. The existing collection step (`PhotoGallery.jsx`)
already has a nice `hover:scale-[1.02] hover:shadow-md transition-all`
treatment that feels responsive without being distracting. Apply the same
language to the three image widgets above.

### 2. Celebration image looks identical to scene 3
Currently the achievement image prompt is a single line baked into the
LLM system message:

> "Achievement description: show ALL characters together in a warm scene."

Scene 3 of the story is *also* "Breakthrough + Warm Ending: They figure it
out together. End with comfort" — so the LLM happily produces an
achievement description that reads exactly like scene 3. The rendered
achievement image ends up visually indistinguishable from scene 3.

What we actually want from the achievement image is a *distinct
celebration moment*, not a continuation of the story's warm ending:
- Iconic / portrait composition (centered hero shot, not a narrative scene)
- Explicit celebration props — confetti, soft glow, tiny flags, paper
  crowns, medals, banners — chosen from a rotating palette so each story
  feels unique
- Brighter, higher-key lighting than the warm-ending scene 3
- Still in the same watercolor storybook style for visual continuity

### 3. Add one short descriptive sentence IN the image
The current style prefix explicitly forbids text:

> "...no text or words in the image."

The user wants each generated image to have a single short sentence
baked into it, like a real storybook page (illustration + one-line
caption at the bottom). Gemini 2.5 Flash Image is capable of rendering
short quoted text reliably when the caption is <= ~10 words and passed
explicitly in the prompt.

**Design reservations (acknowledged, proceeding anyway):**
- AI-rendered text can be garbled. Mitigation: keep captions short,
  quote them exactly, and accept occasional misreads — the backup is
  the TTS narration which is always correct.
- Young children (T0, ages 2–4) can't read yet. The caption is
  therefore a visual / compositional element for them, not a literacy
  aid. For T1/T2 it doubles as a read-along cue.
- The narration text is already displayed as the TTS transcript in the
  conversation panel — so the caption is compositional, not redundant
  information. Keep the caption short and punchy (think movie poster
  tagline) rather than copying the narration verbatim.

## Solution

### Part A — Hover effect on rendered images (frontend)

Use a shared Tailwind class fragment so the three widgets stay in sync:

```
transition-all duration-300 hover:scale-[1.03] hover:shadow-2xl cursor-zoom-in
```

Apply to:
1. `StoryScene.jsx` — the `<img>` for the scene image. Wrapper already has
   `rounded-2xl shadow-lg object-contain` — add the hover classes.
2. `AchievementImage.jsx` — the achievement `<img>`. Already has
   `rounded-3xl shadow-2xl object-contain` — add hover scale (keep the
   existing shadow-2xl and go to `hover:shadow-[0_25px_60px_rgba(0,0,0,0.25)]`
   for a slightly deeper lift on hover).
3. `PhotoDisplay.jsx` — the background photo `<img>`. Wrap with the hover
   classes. This is the "background image" covered by the user's request
   (the captured entity photo that shows during Cat1 early steps).

Respect `prefers-reduced-motion` — `index.css` already has a global
reduced-motion rule that neutralizes animations and transitions, so the
hover scale will auto-disable for users who need it.

Leave interactive photo grids (`PhotoGallery`, `PhotoSelector`) alone —
they already have their own hover treatment and this change should not
touch buttons.

### Part B — Distinct celebration image (backend)

**Schema change:** add an optional `caption: str | None` field to
`StoryScene` and a `caption` field on the structured story's achievement
slot (via a dedicated `achievement_caption`). This holds the exact text
we want baked into the image. Keep it <= 10 words.

**Prompt change (`synthesis.py`):** rewrite the `user_prompt` for
`_generate_structured_story` so the LLM produces:
- Per-scene: `narration`, `image_description`, `caption` (≤ 10 words)
- Global: `achievement_description`, `achievement_caption` (≤ 6 words)

Specifically for the achievement image, the instructions become:

> ACHIEVEMENT IMAGE — must be visually DISTINCT from scene 3. This is a
> CELEBRATION POSTER, not a story scene:
> - Centered hero composition (all characters centered, facing viewer)
> - Explicit celebration props: pick 2–3 from { soft paper confetti,
>   tiny paper flags, a glowing sunburst behind the characters, small
>   paper crowns, a ribbon banner arching overhead, soft golden
>   particles, a warm spotlight }
> - Brighter / higher-key lighting than scene 3
> - Same watercolor storybook style
> - achievement_caption: 3–6 celebratory words (e.g. "A brave new team!",
>   "Friends forever", "Our first adventure")

### Part C — Text caption in the generated image (backend)

**Style prefix (`image_gen.py`):** change the existing style prefix from
"no text or words in the image" to explicitly *allow* one short caption,
and include the caption text in the prompt when a caption is supplied.

Rewrite `generate_image` to accept an optional `caption: str | None`
argument. When present, append:

```
Include a short hand-lettered caption at the bottom of the illustration
that reads EXACTLY: "{caption}". The caption is painted in a cozy
hand-lettered style, clearly readable, no additional words.
```

Update `_scene_image_worker` to accept `scene_captions: list[str | None]`
and `achievement_caption: str | None` and thread them through each
`generate_image` call.

Update `start_scene_images` signature accordingly, and update
`_generate_structured_story` + `_generate_comparison_reveal` to pull
captions out of the LLM response and pass them in.

Update `StoryScene.image_description` / caption flow so the frontend
doesn't need to know about captions — the text lives baked into the
image itself. No frontend caption UI.

## Implementation Steps

1. **Schema:** add `caption: str | None = None` to `StoryScene`; add
   `achievement_caption: str | None = None` to `StructuredStory`.
2. **Backend prompt rewrite:** update the `user_prompt` in
   `_generate_structured_story` to request `caption` per scene and
   `achievement_caption` globally, with the CELEBRATION POSTER
   instructions for the achievement image. Also update
   `_generate_comparison_reveal` with an analogous caption field
   (`reveal_caption`).
3. **image_gen:** change `_STYLE_PREFIX` to drop "no text or words"; add
   an optional `caption` parameter to `generate_image` that appends
   caption instructions when set. Update `_scene_image_worker`,
   `start_scene_images`, and the blocking `generate_scene_images`
   wrapper to carry the new caption lists through.
4. **Synthesis wiring:** pull captions from the parsed LLM JSON and pass
   them into `start_scene_images` in both
   `_generate_structured_story` and `_generate_comparison_reveal`.
5. **Frontend hover:** apply the shared hover class fragment to
   `StoryScene.jsx`, `AchievementImage.jsx`, and `PhotoDisplay.jsx`.
6. **Verification:**
   - `uv run ruff check` + `uv run ruff format` on changed backend files
   - `uv run python` smoke test that `start_scene_images` still works
     when `scene_captions=None` and when captions are supplied
   - `npx vite build` passes
7. **Review loop:** run code-reviewer and code-simplifier subagents on
   the diff before reporting complete.

## Tradeoffs / honest concerns

- **AI text garbling:** I estimate Gemini 2.5 Flash Image gets short
  quoted captions right ~80–90% of the time. The ~10–20% failure mode
  is misspellings or extra letters. Since the narration is also
  displayed in the conversation bubble and spoken via TTS, a garbled
  in-image caption degrades gracefully into "nice decorative text" —
  not a blocker. If the user reports it's too often wrong, we can
  either (a) render the caption on the frontend as a CSS overlay
  instead of baking it into the image, or (b) drop captions entirely.
  I'll flag this risk in the commit message so the rollback path is
  obvious.
- **Caption length:** shorter is better for both legibility and LLM
  accuracy. Target ≤ 6 words for achievement, ≤ 10 words per scene.
- **"Background image" interpretation:** I'm reading this as the
  entity photo in `PhotoDisplay` (the Cat1 background image of the
  captured subject). If the user meant something else (e.g. the
  ExplorerMap canvas or the `.bg-nature` gradient), they can tell me
  and I'll adjust.
- **Hover effect interpretation:** "like the one shown in celebration
  step in ladybug game" — no hover currently exists on the ladybug
  celebration (`AchievementImage`). I'm applying the collection-grid
  hover treatment (`hover:scale-[1.02]` family) as the most reasonable
  match for the described feel: a gentle lift with shadow.

## Out of scope

- Not changing the scene count (still 3 for story, 1 for reveal).
- Not changing the Imagen model or the progressive delivery plumbing.
- Not adding a CSS text overlay for captions — captions go IN the image.
- Not touching the concept reveal / closing step visualization (the
  user confirmed earlier that those should stay as-is).
