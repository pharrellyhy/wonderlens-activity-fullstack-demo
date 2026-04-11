# Celebration/Closing Bug Fixes + Image Consistency

**Date:** 2026-04-10
**Status:** Draft — needs approval before implementation
**Branch:** `worktree-feat+edu-content-feedback`
**HEAD:** `5952254`

Five issues found during manual E2E testing of the just-landed celebration/closing redesign (plan: `docs/superpowers/plans/2026-04-10-celebration-closing-redesign.md`). Fixing them as a batch.

---

## Issues (from the user's test report)

1. **Stage mode is unusable.** Device panel grows without bound on tall viewports (`image-1.png`), the conversation collapses to a 48px footer that can't be expanded, the footer text is truncated with no way to see the full AI line, and the user cannot type to advance. No visible affordance for "how do I get back to the chat?" → critical UX failure.

2. **Debug panel doesn't show the celebrate turn for the ladybug (comparison_reveal) game.** It shows up for dandelion but not ladybug.

3. **Generated characters drift between scenes.** Parallel image generation produces independent images with no visual memory, so Peter-the-petal in scene 1 and Peter-the-petal in scene 2 look like different characters.

4. **Ladybug game still uses "story" language at synthesis start.** Speaker says "Ooh, let me think of a story about..." and the loading widget shows "Creating your story". Both are wrong for comparison_reveal games.

5. **Dandelion game hangs on "i don't know" at the detail phase.** The Turn Director's non-answer handler keeps returning `need_help` with identical scaffolding, forever. Counter `detail_exchange_count` is not incremented for non-answers, so the child is stuck.

---

## Goals

- Stage mode becomes user-friendly: device panel grows without trapping the user in an unresponsive footer.
- Loading screen + dialogue work for both `collaborative_story` and `comparison_reveal` formats.
- The "i don't know" loop terminates after 2 attempts with a playful default.
- Debug panel records the celebrate step for both Cat5 games.
- Image generation produces visually consistent characters across scenes and the achievement image.

## Non-goals

- No architectural refactor of the Turn Director.
- No new animation/transition work beyond what's needed to fix Issue 1.
- No per-game default lookup tables beyond a small fallback.
- Not speeding up image generation (sequential is OK; we'll improve the loading UX instead).
- No changes to Cat1 flows.

---

## Fix 1 — Stage mode: proportional resize instead of footer collapse (CRITICAL)

### Root cause

Stage mode currently does TWO things that together make the UI unusable:

- Grows device panel from `h-[55%] max-h-[34rem]` to `flex: 1 1 auto; max-height: none` (unbounded).
- Collapses the conversation panel to `flex: 0 0 3rem; overflow: hidden`, replacing `<ConversationPanel>` with `<StageModeFooter>` (a single-line truncated quote of the latest AI message).

The footer has:
- No expand button
- No visible indication it's tappable
- No text wrapping (uses Tailwind `truncate`)
- No way to get back to a full conversation

Meanwhile the device panel, with `max-height: none`, stretches to fill the viewport on tall screens (image-1.png). The combination feels trapped.

### Fix

**Abandon the footer approach entirely.** Stage mode will simply grow the device panel proportionally and let the conversation panel shrink but remain fully usable.

Changes:

**Delete:** `frontend/src/components/StageModeFooter.jsx` (no longer needed).

**Revert:** `frontend/src/App.jsx` — remove the `import StageModeFooter` line, remove the `stageMode ? <StageModeFooter.../> : ...` ternary branch in the conversation `<section>`. The conversation panel renders normally (RetryButton / PhotoSelector / ConversationPanel) in all modes.

**Change:** `frontend/src/App.jsx` — keep `stageMode` derivation and the `stage-mode` class on `<main>`. That's how the CSS below targets stage-mode overrides.

**Rewrite:** `frontend/src/index.css` stage-mode rules.

```css
/* Stage mode — celebrate/closing grow the device panel while keeping the
 * conversation panel usable (not collapsed). The conversation still shows
 * messages and the input bar so the user can always type or see what the
 * AI just said in full. */
.app-top-panel,
.app-main > section[aria-label="Conversation panel"] {
  transition: flex-basis 500ms ease-out, max-height 500ms ease-out;
}

.stage-mode .app-top-panel {
  flex: 1 1 72%;
  max-height: 48rem;
}

.stage-mode > section[aria-label="Conversation panel"] {
  flex: 1 1 auto;
  min-height: 9rem;
}
```

**Important CSS specificity note:** the device panel currently has `h-[55%] max-h-[34rem]` as Tailwind utilities in its `className`. Those need to be overridden by `.stage-mode .app-top-panel`. Tailwind utilities compile to `.h-\[55\%\]` etc. which have specificity `(0,1,0)`. Our selector `.stage-mode .app-top-panel` has specificity `(0,2,0)`. That's higher, so it wins. No `!important` needed.

However, Tailwind v4's arbitrary-value utilities sometimes emit `height: 55% !important` in the layer cascade. If our override doesn't win in practice, we'll switch to conditionally applying the Tailwind classes via JSX (Approach B below). **Verify during implementation by inspecting computed styles.**

Approach B fallback: in App.jsx, toggle the classes:
```jsx
<section className={`app-top-panel shrink min-h-0 transition-[flex-basis] duration-500 ease-out ${
  stageMode ? 'flex-[1_1_72%] max-h-[48rem]' : 'h-[55%] max-h-[34rem]'
}`} aria-label="Device screen">
```

And drop the custom `.stage-mode .app-top-panel` CSS rule. The conversation panel rule stays in CSS because `<section className="flex-1 min-h-0 flex flex-col surface-primary overflow-hidden">` uses utility-computed flex that the `.stage-mode` override can coexist with.

**Expected outcome:**
- Normal mode: 55% device, 45% conversation (unchanged)
- Stage mode: ~72% device (capped at 48rem on huge screens), ~28% conversation
- Conversation panel stays fully usable during stage mode — messages scrollable, input works, "new session" button reachable
- Smooth 500ms flex-basis transition both ways

### Tests

No frontend test framework, so verification is:
- `npm run lint && npm run build` clean
- Manual E2E: run dandelion, reach celebrate → verify conversation panel still has input, verify device panel grew but didn't dominate
- Manual E2E: same for ladybug

---

## Fix 2 — Format-neutral loading text

### Root cause

`backend/turn_handling/synthesis.py:110` hardcodes the loading dialogue:

```python
dialogue=f"[excited] Ooh, let me think of a story about {names}...",
```

`frontend/src/widgets/StoryLoading.jsx:27-31` hardcodes the headline:

```jsx
<p className="... story-loading-shimmer">Creating your story</p>
<p className="...">Painting scenes with words and colors...</p>
```

Both use "story" language that's wrong for `comparison_reveal` games (ladybug).

### Fix

**`backend/turn_handling/synthesis.py`:** change `_loading_result` to use format-neutral dialogue:

```python
def _loading_result(state: SessionStateModel) -> TurnResult:
    """Return a synthesis loading screen and queue generation via auto-advance."""
    turn_response = TurnResponse(
        dialogue="[excited] Ooh, let me put it all together for you...",
        tone_marker="excited",
        screen_widget="story_loading",
        screen_widget_params={},
        stay_on_step=True,
    )
    # ... rest unchanged
```

Removes the `names` dependency (no longer interpolated). Works for both story and comparison games.

**`frontend/src/widgets/StoryLoading.jsx`:** update the headline and subtitle:

```jsx
<p className="text-xl max-[380px]:text-lg font-display font-bold story-loading-shimmer">
  Creating your adventure
</p>
<p className="text-sm max-[380px]:text-xs text-gray-400 mt-2 animate-pulse">
  Bringing everything together...
</p>
```

Keeps the same visual style and animation. Just neutralizes the "story" language.

**Not renaming the file.** `StoryLoading.jsx` → it's still the "synthesis loading" widget; renaming requires updating `WIDGET_MAP` and imports. The widget name in the backend `ScreenFrame` is `story_loading` — keep it as the widget-registry key for backward compat, but the user-visible text is neutral.

### Tests

- `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py` — no backend tests should break (the dialogue string isn't asserted anywhere, verify via grep)
- `npm run build` — verify StoryLoading.jsx still compiles
- Manual E2E: dandelion + ladybug both show neutral loading text

---

## Fix 3 — "I don't know" infinite loop at detail phase

### Root cause

`backend/turn_handling/directive.py:638-685` — when the child's detail-phase input is in `_NON_ANSWER_PHRASES`, the Turn Director returns a `need_help` directive with scaffolding text ("The child said 'i dont know' — they need help with texture. Model an answer yourself first. Describe how the {item} feels in a playful way. Then offer a binary choice about the texture."). Critically:

1. **`state.detail_exchange_count` is NOT incremented** for non-answers. The counter bump at line 687 is AFTER the non-answer return.
2. No other counter tracks how many times the child has been stuck.
3. The LLM Speaker receives the same `response_direction` each time, so the output is nearly identical — the child sees the exact same scaffolded question repeated.

From the log:
```
Turn 1: "i dont know" → "Whoosh, it feels like a tiny cloud... Is it soft like a bunny or smooth like an egg?"
Turn 2: "i dont know" → "Whoosh, it feels like a tiny cloud... Is it soft like a bunny or smooth like an egg?"
(loop forever)
```

### Fix

Add a `detail_stuck_count` field to `SessionStateModel` and force-advance after 2 consecutive non-answers with a playful default.

**`backend/schemas/session_state.py`:** add the field (find the SessionStateModel class):

```python
detail_stuck_count: int = Field(
    default=0,
    description="Count of consecutive non-answers in the detail phase; resets on successful harvest or on advance",
)
```

**`backend/turn_handling/directive.py`:** update the non-answer branch (around line 638). Rewrite as:

```python
# Detect non-answers: child is stuck, confused, or asking AI to decide.
if normalized_detail in _NON_ANSWER_PHRASES:
    state.detail_stuck_count += 1
    current_item = state.collected_photos[-1] if state.collected_photos else "this item"
    current_item_label = current_item.replace("_", " ")

    # After 2 consecutive non-answers, pick a playful default and advance.
    if state.detail_stuck_count >= 2:
        default_name, default_detail = _pick_stuck_default(state, current_item_label)
        _record_collection_detail(state, default_detail)
        if is_naming_game:
            state.collected_names.append(default_name)
        state.detail_stuck_count = 0
        state.detail_exchange_count = 0
        state.round_advance_pending = True

        friendly = (
            f"No worries! Let's call this one {default_name} — it feels {default_detail}. "
            f"Now, where should we look for the next find?"
            if is_naming_game
            else f"No worries! I'd say it looks {default_detail}. Let's see what else you can find!"
        )
        fast = TurnDirective(
            action="advance",
            reasoning=f"Child stuck (2 non-answers). Applying default '{default_name}/{default_detail}'.",
            response_direction=friendly,
            emotion_tag="gentle",
            max_sentences=3,
        )
        logger.info(
            "turn_director: step=%s action=advance (stuck default applied) name=%s detail=%s",
            state.current_step, default_name, default_detail,
        )
        state.last_directive_action = fast.action
        return fast

    # First non-answer: scaffold (existing behavior, unchanged below this point)
    obs_angle = ""
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        obs_angle = state.creative_slots.observation_angle

    if is_naming_game:
        # ... existing naming-game scaffold code ...
    else:
        # ... existing observation-game scaffold code ...
    # ... build and return fast directive (existing code) ...
```

And **add** a helper `_pick_stuck_default` near the top of directive.py:

```python
_STUCK_DEFAULTS: dict[str, list[tuple[str, str]]] = {
    "texture": [("Softie", "soft and cozy"), ("Fuzzy", "fluffy and warm")],
    "color": [("Sunny", "bright and cheerful"), ("Rainbow", "colorful and fun")],
    "shape": [("Curvy", "smooth and curvy"), ("Pointy", "tall and pointy")],
    "size": [("Tiny", "small and cute"), ("Mighty", "big and strong")],
    "pattern": [("Spotty", "covered in pretty spots"), ("Dotty", "full of tiny dots")],
    "form": [("Bumpy", "bumpy and interesting"), ("Wiggly", "wiggly and playful")],
    "movement": [("Dancy", "always moving"), ("Bouncy", "bouncing around")],
    "smell": [("Sweetie", "sweet and fresh"), ("Minty", "cool and fresh")],
    "function": [("Helpful", "useful and clever"), ("Special", "special and unique")],
    "habitat": [("Cozy", "snug and safe"), ("Hidden", "tucked away")],
}

def _pick_stuck_default(state: "SessionStateModel", item_label: str) -> tuple[str, str]:
    """Pick a playful (name, detail) fallback when the child is stuck at detail phase."""
    angle = "texture"
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        angle = state.creative_slots.observation_angle
    options = _STUCK_DEFAULTS.get(angle, _STUCK_DEFAULTS["texture"])
    # Rotate through options based on how many stuck-defaults we've already used
    # (avoid repeating the same default if two items in a row got stuck)
    used = sum(
        1 for n in state.collected_names
        if any(n == opt[0] for opt in _STUCK_DEFAULTS[angle])
    ) if angle in _STUCK_DEFAULTS else 0
    return options[used % len(options)]
```

**Reset the counter on successful harvest.** Find the detail-phase success path in directive.py (right after line 687's `state.detail_exchange_count += 1`) and add:

```python
state.detail_exchange_count += 1
state.detail_stuck_count = 0  # reset on successful harvest
```

Also reset when advancing collection (core.py or wherever `round_advance_pending` is processed) — verify during implementation that the reset covers all transitions.

**Tests:** add a regression test in `tests/test_turn_handler.py`:

```python
async def test_detail_phase_force_advances_after_two_non_answers():
    """Two consecutive 'i dont know' responses should force-advance with a default."""
    state = _make_state(
        current_step="STEP_3_COLLECT_3",
        status="active",
        template_type="cat5",
        collection_phase="detail",
        collected_photos=["fuzzy_moss", "woolly_caterpillar", "fluffy_seed"],
        collected_names=["Softie", "Cloudy"],
        collected_details=["soft", "fluffy"],
        detail_exchange_count=0,
        detail_stuck_count=0,
    )

    # First "i dont know" → still scaffolds
    # (verify: action == "need_help", detail_stuck_count == 1)
    # Second "i dont know" → force-advances with default
    # (verify: action == "advance", name appended, detail added, counters reset)
```

### Expected flow after fix

Turn 1: "i dont know" → `need_help` with scaffold. `detail_stuck_count = 1`.
Turn 2: "i dont know" → **force advance** with "No worries! Let's call this one Softie — it feels soft and cozy. Now, where should we look for the next find?" `detail_stuck_count = 0`, counters reset, `round_advance_pending = True`.

---

## Fix 4 — Debug panel missing celebrate for ladybug

### Investigation needed

Likely root cause candidates:
1. **`_deliver_scene` in synthesis.py doesn't include a debug payload** in its TurnResult. Both dandelion and ladybug go through this, so this alone doesn't explain why ladybug specifically is missing celebrate.
2. **Celebrate is reached through a different code path for ladybug** (1 scene → advance to STEP_5_CELEBRATE in a single call) that may race with the turn recording. For dandelion, 3 scene deliveries are separate turns, creating natural breaks.
3. **The frontend DebugPanel filters or groups celebrate turns differently** when they arrive in quick succession after the last scene.

### Fix approach

1. Add a minimal debug payload to `_deliver_scene`:
   ```python
   return TurnResult(
       ...
       debug={
           "generation": {"source": "structured_scene_delivery", "scene_number": scene_number, "total_scenes": len(story.scenes)},
       },
   )
   ```
2. Run the ladybug game E2E and inspect the `/api/turn` response payload for the celebrate turn. Confirm whether `debug` is populated server-side.
3. If server-side is fine, check the frontend `DebugPanel` + `debugHistory` accumulation in `useSessionOrchestration` to see if something is swallowing the celebrate entry.
4. If the issue is frontend accumulation (e.g. dedupe logic), fix at that layer.

**This is the smallest-risk fix and may be just "add debug= to _deliver_scene". If it's more involved, I'll time-box to 30 minutes and defer the rest to a follow-up issue.**

### Tests

Manual E2E only — ladybug game reaches celebrate, verify a celebrate entry appears in the Debug Panel History tab.

---

## Fix 5 — Sequential image generation for character consistency

### Root cause

`backend/image_gen.py::generate_scene_images` currently runs scene images in 2+2 batches via `asyncio.gather`. Each `generate_image` call is independent — no shared character appearance. Gemini receives only a text prompt per scene, so Peter-the-petal in scene 1 and Peter-the-petal in scene 2 are unrelated generations.

The user's suggestion: **use a previously generated image as a visual reference when generating the next one.** Gemini 2.5 Flash Image supports multimodal input — you can pass an image as part of `contents` alongside the text prompt, and the model will preserve character/style.

### Fix

Rewrite `generate_scene_images` to run **sequentially**, passing each generated PNG as a reference when generating the next:

```python
async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
    session_id: str = "",
) -> tuple[list[str | None], str | None]:
    """Generate scenes sequentially, threading each previous image as a visual
    reference into the next prompt for character/style consistency.

    Scene 1: no reference (anchors the character design)
    Scene 2: scene 1 as reference
    Scene 3: scene 2 as reference  (or scene 1, if we prefer anchoring)
    Achievement: last scene as reference
    """
    sid = session_id or "unknown"
    scene_images: list[str | None] = []
    anchor_bytes: bytes | None = None  # first successful scene image (the "canon" look)
    previous_bytes: bytes | None = None

    for i, desc in enumerate(scene_descriptions):
        img_bytes = await generate_image(
            desc,
            aspect_ratio="16:9",
            reference=previous_bytes,
            anchor=anchor_bytes,  # keep character canon stable even as scenes progress
        )
        if img_bytes:
            _save_image(img_bytes, sid, f"scene_{i + 1}.png")
            scene_images.append(image_to_base64(img_bytes))
            previous_bytes = img_bytes
            if anchor_bytes is None:
                anchor_bytes = img_bytes
        else:
            scene_images.append(None)

    achievement_bytes = await generate_image(
        achievement_description,
        aspect_ratio="1:1",
        reference=previous_bytes or anchor_bytes,
        anchor=anchor_bytes,
    )
    achievement_url = None
    if achievement_bytes:
        _save_image(achievement_bytes, sid, "achievement.png")
        achievement_url = image_to_base64(achievement_bytes)

    return scene_images, achievement_url
```

And update `generate_image` to accept optional reference image bytes:

```python
async def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    reference: bytes | None = None,
    anchor: bytes | None = None,
) -> bytes | None:
    """Generate an image, optionally using reference/anchor images for consistency.

    `reference`: the immediately previous scene's image (style/mood continuity).
    `anchor`: the first successful scene's image (character design canon).
    """
    settings = get_settings()
    if not settings.imagen_enabled:
        return None

    full_prompt = f"{_STYLE_PREFIX} {prompt}"
    if reference or anchor:
        full_prompt += (
            " Keep the character designs, proportions, colors, and art style "
            "visually consistent with the reference images."
        )

    contents: list = [full_prompt]
    if anchor:
        contents.append(types.Part.from_bytes(data=anchor, mime_type="image/png"))
    if reference and reference is not anchor:
        contents.append(types.Part.from_bytes(data=reference, mime_type="image/png"))

    client = _get_client()
    for attempt in range(_MAX_RETRIES):
        try:
            start = time.perf_counter()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.imagen_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            # ... existing extraction + retry + error handling ...
```

**Verify the Gemini SDK API:** before implementing, confirm that `types.Part.from_bytes(data=..., mime_type=...)` is the correct way to pass an image in `contents` for `gemini-2.5-flash-image`. If the API differs, adapt. Quick test: make a one-off call with a test prompt and a reference image, check the response.

### Performance trade-off

**Parallel (current):** ~8-12s total for 4 images (3 scenes + 1 achievement). Two batches of 2 with a 1s sleep between.

**Sequential (new):** ~4 × 5s = 20s total. ~2.5x slower.

**Mitigation:** the loading screen is already visible during generation; users watch the animated mascot. The doubled wait is acceptable for the consistency win. If it becomes a real problem, we can revisit with a hybrid (scene 1 standalone, then scenes 2+3 parallel using scene 1 as anchor; achievement can also use scene 1 as anchor and run concurrently with scene 2+3).

**Hybrid approach (optional alternative):**
- Scene 1 standalone (anchors everything) — ~5s
- Scenes 2, 3, achievement in parallel, all using scene 1 as anchor — ~5s
- Total: ~10s with consistency

If the straight sequential approach is too slow in practice, I'll switch to the hybrid during implementation.

### Tests

- Unit: hard to test without mocking Gemini. Skip unit tests; rely on the existing `generate_scene_images` being called by synthesis code paths that do have tests.
- Manual: run dandelion, inspect saved images in `backend/data/images/{session_id}/`. Characters should look visibly similar across scenes.

---

## Implementation order

Do the fixes in this order (smallest → largest):

1. **Fix 2** (loading text) — 5 min. Pure text changes. No behavioral risk.
2. **Fix 1** (stage mode UX) — 20 min. Delete one component, revert App.jsx, rewrite CSS. Test lint + build.
3. **Fix 4** (debug panel celebrate) — 15 min. Add `debug=` to `_deliver_scene`. Manually test; if not enough, investigate frontend.
4. **Fix 3** (i dont know loop) — 45 min. Schema field + directive logic + tests.
5. **Fix 5** (image consistency) — 45 min. Gemini SDK verification + rewrite `generate_scene_images`.

Total estimated: ~2 hours with testing. Each fix commits independently so any one can be reverted if problematic.

## Files touched (summary)

| Fix | File | Change |
|---|---|---|
| 1 | `frontend/src/App.jsx` | Remove `StageModeFooter` import + usage, keep `stageMode` + class |
| 1 | `frontend/src/index.css` | Rewrite stage-mode rules (proportional, no collapse) |
| 1 | `frontend/src/components/StageModeFooter.jsx` | **Delete** |
| 2 | `backend/turn_handling/synthesis.py` | `_loading_result` dialogue text |
| 2 | `frontend/src/widgets/StoryLoading.jsx` | Headline + subtitle text |
| 3 | `backend/schemas/session_state.py` | Add `detail_stuck_count` field |
| 3 | `backend/turn_handling/directive.py` | Non-answer force-advance + `_pick_stuck_default` |
| 3 | `tests/test_turn_handler.py` | Add stuck-default regression test |
| 4 | `backend/turn_handling/synthesis.py` | Add `debug=` to `_deliver_scene` TurnResult |
| 5 | `backend/image_gen.py` | Sequential generation with reference images |

## Success criteria

1. Manual E2E: ladybug game runs through synthesis → celebrate → closing with:
   - Format-neutral loading text ✓
   - No "story" mentions in dialogue ✓
   - Celebrate step appears in debug history ✓
   - Device panel grows but conversation stays usable ✓
   - Can see full AI dialogue during celebrate/closing (no truncation) ✓
2. Manual E2E: dandelion "i dont know" spam → force-advances after 2 non-answers with a friendly default ✓
3. Manual E2E: dandelion generated scenes show visibly consistent characters (not guaranteed but noticeably better) ✓
4. `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py` → all pass (no regressions) ✓
5. `cd backend && uv run ruff check . && uv run mypy state_machine.py turn_handling/ schemas/` → clean ✓
6. `cd frontend && npm run lint && npm run build` → no new errors, build succeeds ✓

## Rollback

Each fix is an independent commit. If any one causes regression:
- `git revert <sha>` — the per-fix commit
- Re-test

If Fix 5 (sequential generation) breaks image generation entirely, revert it and investigate whether the Gemini SDK call shape changed.

---

## Open questions (resolve during implementation)

1. **Stage mode CSS specificity:** will `.stage-mode .app-top-panel` override Tailwind's `h-[55%]` utility reliably? Test by inspecting computed styles in the browser. If not, use Approach B (toggle classes in JSX).
2. **Gemini image-in-content API shape:** verify `types.Part.from_bytes(data=..., mime_type="image/png")` is valid for multimodal input. Check with a test call.
3. **`round_advance_pending` vs `_advance_state`:** for Fix 3, should the force-advance set `round_advance_pending = True` (lets the next turn advance naturally) or call `_advance_state` directly? The former is safer — follow the pattern used elsewhere in the file.
4. **Debug panel: is it `debugHistory` that's dropping the celebrate entry, or something else?** Investigate quickly during Fix 4.
