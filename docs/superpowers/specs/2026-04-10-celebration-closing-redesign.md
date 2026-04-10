# Celebration & Closing Redesign — Stage Mode + Concept Reveal

**Date:** 2026-04-10
**Status:** Approved (brainstorming session)
**Worktree:** `.worktrees/feat/edu-content-feedback`
**Branch:** `feat/edu-content-feedback`

---

## TL;DR

Rework how Cat5 celebrate (STEP_5_CELEBRATE) and closing (STEP_6_CLOSING) render on the device panel:

1. **Stage mode** — when the child reaches celebrate/closing, the device panel expands to fill the viewport (the "toy camera zooms in"). The conversation panel collapses to a 48px footer strip showing the latest AI line. Fixes the perennial "the generated image gets cut off" bug by giving the image the entire viewport.
2. **Celebration** — `AchievementImage` widget is simplified to just the role title and the generated image. Character name pills and IB concept pills are removed from this step.
3. **Closing** — new `ConceptReveal` widget replaces `AchievementImage` at STEP_6_CLOSING. Role title + large circular IB concept medallions using the existing PNGs in `frontend/public/badges/`. No image, no character names.
4. **Concept medallions** — new `ConceptMedallion` component mirrors `ExplorerMap` `ZoneSlot` visual language (circle + gradient + inner white disc + name pill label + star accent) but sized larger for the stage (`clamp(6rem, 22vw, 8rem)` vs collection's `clamp(4.5rem, 18vw, 6rem)`).

Backend changes are minimal — `state_machine.py` splits the celebrate/closing branch into two distinct widgets, and `directive.py` learns to send `concept_reveal` at Cat5 closing. Cat1 is untouched.

---

## Context — read this first if you're a fresh session

**Project:** WonderLens Activity Demo. Split-view React frontend (conversation panel on bottom, device panel on top inside a toy-camera frame). A multi-agent Python backend orchestrates a Cat5 scavenger-hunt activity.

**The user flow we're redesigning:**

1. Child collects 3 items (STEP_3_COLLECT_1..3).
2. Synthesis step (STEP_4_SYNTHESIS) generates narration + images showing what they found.
3. **STEP_5_CELEBRATE** — the AI celebrates and an achievement image (AI-generated at synthesis time) is shown.
4. **STEP_6_CLOSING** — IB learning concepts are surfaced (Form, Connection, Function, Change, Perspective, Responsibility, Reflection, Causation).

**What the user complained about (brainstorming session, 2026-04-10):**

- The generated celebration image keeps getting cut off inside the device panel, even after bumping `max-h` from `28rem` to `34rem`. The image has unpredictable aspect ratios and the panel is too constrained.
- At celebrate/closing, `AchievementImage.jsx` stacks role title → image → character name pills → IB concept pills all in the same widget. The user said the character names and IB concepts listed together "make no sense" because they're conceptually unrelated — names come from the journey, concepts are the learning outcome.
- IB concept badges are tiny text pills (`text-base`, `px-4 py-1.5`) — they don't feel like earned rewards. The user wants them to be large visual tokens, "like the icons during collection steps" (referring to `ExplorerMap` `ZoneSlot` circles at ~6rem).
- The user also noted that the existing PNG badge assets already live at `frontend/public/badges/{concept.lower()}.png` — no need to create new icons.

**Existing assets:**

- `frontend/public/badges/causation.png`, `change.png`, `connection.png`, `form.png`, `function.png`, `perspective.png`, `reflection.png`, `responsibility.png` — ready to use.
- `frontend/src/canvas/ExplorerMap.jsx` — contains `ZoneSlot` component that's the visual reference for medallion shape, size, and animation.
- `frontend/src/widgets/AchievementImage.jsx` — current celebrate/closing widget, will be simplified.

---

## Goals & non-goals

### Goals

1. **Celebration image no longer gets cut off** at any aspect ratio. Solved by giving the image the full viewport.
2. **Celebrate and closing have distinct focus.** Celebrate = the image. Closing = the concept medallions. Nothing competes for attention on either screen.
3. **IB concept medallions feel earned** — same circular visual language as collection zone slots, larger, with staggered reveal animation. Uses existing PNG assets.
4. **The toy-camera frame stays visible** throughout the transition — no modal, no portal. The device panel grows; the toy camera grows with it.
5. **Minimum backend surface area** — the split is mostly frontend. Backend only needs to tell the frontend which widget to render and what params.
6. **Cat1 path is completely unchanged** — this is Cat5-only.

### Non-goals

- Not adding tap-to-expand interactions on medallions (future enhancement).
- Not backend-sourcing the closing role line text ("You are now a {title}!") — hardcoded in the widget for now.
- Not handling the `concepts == []` edge case (all current games ship with at least 1).
- Not changing game YAML format or any content authoring workflow.
- Not touching synthesis flow, scene delivery, image generation, or any structured story handling.
- Not adding a "replay celebration" or "share achievement" feature.
- Not rebuilding `AchievementImage` as a swiss-army component that handles both modes — two clean widgets with distinct contracts.
- Not adding new IB concept emoji / SVG / monogram — reuse the existing PNGs.

---

## Design

### Section 1 — Stage mode mechanics

**What triggers stage mode:**

In `frontend/src/App.jsx`, derive a boolean:

```jsx
const stageMode = ['STEP_5_CELEBRATE', 'STEP_6_CLOSING'].includes(sessionState?.current_step);
```

Apply a CSS class to the `<main>` element:

```jsx
<main className={`app-main flex flex-col flex-1 overflow-hidden ... ${stageMode ? 'stage-mode' : ''}`}>
```

**What animates (CSS-only transitions on existing elements):**

| Element | Normal | Stage mode | Transition |
|---|---|---|---|
| `.app-top-panel` (device section) | `h-[55%] max-h-[34rem]` | `flex: 1 1 auto`, `max-height: none` | `transition: flex-basis 500ms ease-out, max-height 500ms ease-out, height 500ms ease-out` |
| Conversation `<section>` | `flex-1 min-h-0` | `flex: 0 0 48px`, `overflow: hidden` | same transition |
| `<ConversationPanel>` contents | full message list + mic + composer | `hidden` (display: none) | instant |
| `<StageModeFooter>` | not rendered | slides up, fades in after 300ms | `animate-fade-in` |

The toy-camera frame (`ToyCameraFrame`) stays mounted the entire time — it just grows inside the expanded panel. `DeviceScreen` does NOT remount, so its internal widget animations keep running smoothly through the transition.

**CSS rule additions** (location: wherever `.app-top-panel` base rule lives — likely `frontend/src/index.css` or a dedicated layout CSS file):

```css
.app-top-panel,
.app-main > section[aria-label="Conversation panel"] {
  transition: flex-basis 500ms ease-out, max-height 500ms ease-out, height 500ms ease-out;
}

.stage-mode .app-top-panel {
  flex: 1 1 auto;
  max-height: none;
}

.stage-mode > section[aria-label="Conversation panel"] {
  flex: 0 0 3rem; /* 48px footer strip */
  overflow: hidden;
}
```

If adjusting `.app-top-panel`'s tailwind classes directly is cleaner than CSS selectors, use Tailwind's `data-` attribute variants or a conditional `className` join. Implementation detail — pick whichever pattern matches the codebase's existing convention for conditional styling.

**Collapsed conversation footer (new component `StageModeFooter.jsx`):**

A thin 48px strip at the bottom that shows the latest AI dialogue line.

```jsx
export default function StageModeFooter({ messages, isSpeaking }) {
  const latestAi = [...(messages || [])].reverse().find((m) => m.role === 'ai');
  if (!latestAi) return null;

  return (
    <div className="h-12 flex items-center gap-2 px-4 surface-primary border-t border-black/5
                    animate-fade-in">
      <SpeakerIcon
        className={`w-4 h-4 shrink-0 ${isSpeaking ? 'text-[var(--color-forest)] animate-pulse' : 'text-gray-400'}`}
      />
      <p className="text-sm text-gray-700 truncate italic">
        "{latestAi.text}"
      </p>
    </div>
  );
}
```

- Reads `messages` + `isSpeaking` from the same source `ConversationPanel` uses (passed down from `App.jsx`).
- Single line, truncated with ellipsis.
- Speaker icon animates when TTS is playing (resolves Open Question 1 — decision: yes, show `isSpeaking` state).
- No mic, no text input, no scroll — purely informational.

**App.jsx conditional render:**

```jsx
<section className="... conversation-panel" aria-label="Conversation panel">
  {stageMode ? (
    <StageModeFooter messages={messages} isSpeaking={isSpeaking} />
  ) : (
    <ConversationPanel {...conversationProps} />
  )}
</section>
```

Keeping the `<section>` wrapper mounted (rather than unmounting + remounting) lets the flex transition animate its height change.

**State machine interaction:** none. Stage mode is pure frontend derived state. The backend flow (auto-advance from synthesis → celebrate → closing) is unchanged. When the user clicks "new session", `current_step` clears and `stageMode` returns to `false`, animating the layout back over 500ms.

---

### Section 2 — AchievementImage simplification (celebrate only)

**File:** `frontend/src/widgets/AchievementImage.jsx`

Simplified to focus entirely on the image. Character name pills and IB concept pills are removed.

```jsx
import { FallbackTrophy } from './FallbackTrophy';

export default function AchievementImage({ image_data_url, title, animation }) {
  return (
    <div
      className={`relative flex flex-col h-full w-full p-4 ${
        animation === 'badge_reveal' ? 'animate-celebration-large' : ''
      }`}
    >
      {/* Role title — top, centered, generous */}
      <h2
        className="text-2xl max-[380px]:text-xl font-bold font-display text-center
                   text-[var(--color-forest-dark)] tracking-tight pb-3 shrink-0"
      >
        {title || 'Explorer'}
      </h2>

      {/* Achievement image takes ALL remaining space */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-3xl shadow-2xl object-contain animate-fade-in"
          />
        ) : (
          <FallbackTrophy title={title} />
        )}
      </div>
    </div>
  );
}
```

**What's removed from the widget:**

- `concepts` prop — the widget no longer accepts it. Closing moves to a separate widget (Section 3).
- `sessionState` prop — only needed for `collected_names`, which also goes away.
- The `collectedNames.map()` pill row.
- The `concepts.map()` pill row.

**What changed:**

- `object-contain` gets real room now. At full viewport in stage mode, a 16:9 image gets ~80% viewport width with no competing elements shrinking its height budget.
- Corners bumped to `rounded-3xl` and shadow to `shadow-2xl` for a more "trophy case" feel.
- Title bumped from `text-xl` → `text-2xl` to match the increased scale.
- Padding kept at `p-4` (no need to grow — the image is what grows).

**FallbackTrophy extraction:**

Extract the gradient-circle-with-trophy-emoji fallback into a sibling file `frontend/src/widgets/FallbackTrophy.jsx` (or a local component in the same file — pick whichever matches the codebase's convention for small internal components). Keeps `AchievementImage` readable as a thin container.

```jsx
// frontend/src/widgets/FallbackTrophy.jsx
export function FallbackTrophy({ title }) {
  return (
    <div
      className="w-full h-full rounded-3xl
                 bg-gradient-to-br from-[var(--color-sunflower-light)]/30 via-white/50 to-[var(--color-forest)]/10
                 flex flex-col items-center justify-center gap-5"
    >
      <div className="relative">
        <div className="w-40 h-40 max-[380px]:w-32 max-[380px]:h-32 rounded-full
                        bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)]
                        shadow-xl flex items-center justify-center border-4 border-white/80">
          <div className="w-24 h-24 max-[380px]:w-20 max-[380px]:h-20 rounded-full bg-white/70
                          flex items-center justify-center">
            <span className="text-6xl max-[380px]:text-5xl">🏆</span>
          </div>
        </div>
        <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-[var(--color-sunflower)] animate-sparkle-large" />
        <div className="absolute -bottom-2 -left-3 w-5 h-5 rounded-full bg-[var(--color-forest-light)] animate-sparkle-large" style={{ animationDelay: '0.8s' }} />
        <div className="absolute top-0 -left-4 w-4 h-4 rounded-full bg-[var(--color-teal)] animate-sparkle-large" style={{ animationDelay: '1.4s' }} />
      </div>
      <p className="text-2xl max-[380px]:text-xl font-display font-bold text-[var(--color-forest-dark)]">
        {title || 'Explorer'}
      </p>
    </div>
  );
}
```

Trophy sized up from `w-32 h-32` → `w-40 h-40` since it now has a full viewport to fill.

---

### Section 3 — ConceptReveal widget (closing only)

**New file:** `frontend/src/widgets/ConceptReveal.jsx`

Closing step widget. Distinct from `AchievementImage` because it renders something structurally different (concept tokens, not an image).

```jsx
import ConceptMedallion from './ConceptMedallion';

export default function ConceptReveal({ title, concepts = [], animation }) {
  return (
    <div
      className={`flex flex-col items-center justify-center h-full w-full p-6 gap-8
                  bg-gradient-to-b from-[var(--color-sunflower-light)]/20
                                  via-white/40
                                  to-[var(--color-forest)]/5
                  ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}
    >
      {/* Title with flanking sparkle emojis */}
      <div className="flex items-center gap-3">
        <span className="text-3xl animate-sparkle-large">✨</span>
        <h2 className="text-2xl max-[380px]:text-xl font-display font-bold
                       text-[var(--color-forest-dark)] tracking-tight text-center">
          {title || 'Explorer'}
        </h2>
        <span className="text-3xl animate-sparkle-large" style={{ animationDelay: '0.6s' }}>✨</span>
      </div>

      {/* Concept medallions row — wraps on small screens */}
      <div className="flex flex-wrap justify-center items-start gap-6 max-[380px]:gap-4">
        {concepts.map((concept, i) => (
          <ConceptMedallion key={concept} concept={concept} delayMs={i * 250} />
        ))}
      </div>

      {/* Role line */}
      <p className="text-base font-display text-[var(--color-forest-dark)]/80 text-center">
        {`You are now a ${title || 'Explorer'}!`}
      </p>
    </div>
  );
}
```

**Why a separate widget (not bolt onto `AchievementImage`):**

1. Two fundamentally different things being rendered — image vs concept tokens. Mixing them makes the prop contract ambiguous.
2. Backend can evolve each path independently in the future (e.g., add tap-to-explain on concepts without touching celebrate).
3. Matches existing convention: `story_scene`, `story_loading`, `achievement_image`, `explorer_map` are all distinct widgets for distinct moments.

**Registration in `DeviceScreen.jsx`:**

```jsx
// Import
import ConceptReveal from '../widgets/ConceptReveal';

// Add to WIDGET_MAP
const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  // ... existing entries ...
  achievement_image: AchievementImage,
  concept_reveal: ConceptReveal,      // NEW
  explorer_map: ExplorerMap,
};
```

And add `'concept_reveal'` to the full-panel widget list on line 131 (currently: `'explorer_map'`, `'story_scene'`, `'story_loading'`, `'achievement_image'`). This list controls which widgets render in the `w-full h-full` pass-through container vs the constrained `max-w-[17rem]` inner wrapper.

---

### Section 4 — ConceptMedallion component

**New file:** `frontend/src/widgets/ConceptMedallion.jsx`

```jsx
import { asset } from '../utils/basePath';
import { StarIcon } from '../icons';

export default function ConceptMedallion({ concept, delayMs = 0 }) {
  const badgeSrc = asset(`/badges/${concept.toLowerCase()}.png`);

  return (
    <div
      className="flex flex-col items-center gap-2 animate-badge-pop"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {/* Outer gradient circle */}
      <div className="relative">
        <div
          className="w-[clamp(6rem,22vw,8rem)] h-[clamp(6rem,22vw,8rem)]
                     rounded-full
                     bg-gradient-to-br from-[var(--color-sunflower)]
                                       via-[var(--color-sunflower-light)]
                                       to-[var(--color-forest)]
                     border-[4px] border-white/90
                     shadow-xl
                     flex items-center justify-center
                     animate-gentle-float"
          style={{ animationDelay: `${delayMs + 200}ms` }}
        >
          {/* Inner white disc holds the PNG */}
          <div className="w-[78%] h-[78%] rounded-full bg-white/90
                          flex items-center justify-center overflow-hidden">
            <img
              src={badgeSrc}
              alt={concept}
              className="w-[85%] h-[85%] object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement.innerHTML = '<span class="text-3xl">✨</span>';
              }}
            />
          </div>
        </div>

        {/* Star accent top-right, mirrors ZoneSlot's checkmark */}
        <div
          className="absolute -top-1 -right-1 animate-sparkle-large"
          style={{ animationDelay: `${delayMs + 800}ms` }}
        >
          <StarIcon className="w-6 h-6 text-[var(--color-sunflower)] drop-shadow" />
        </div>
      </div>

      {/* Concept name pill — same treatment as ZoneSlot character name label */}
      <span
        className="px-4 py-1 bg-white/90 backdrop-blur-sm rounded-full
                   text-base max-[380px]:text-sm
                   font-semibold text-[var(--color-forest-dark)]
                   shadow-sm border border-[var(--color-forest)]/15
                   animate-fade-in"
        style={{ animationDelay: `${delayMs + 400}ms` }}
      >
        {concept}
      </span>
    </div>
  );
}
```

**Size rationale:**

- `ExplorerMap` → `ZoneSlot` uses `w-[clamp(4.5rem, 18vw, 6rem)]` because 3 zone slots must fit inside the collection-phase device panel (which is constrained).
- At closing we're in **stage mode** — full viewport — so medallions go larger: `clamp(6rem, 22vw, 8rem)`. Same visual language, scaled up for the stage.
- Lower bound bumped from `4.5rem` → `6rem` (+33%); upper bound from `6rem` → `8rem` (+33%).

**Asset loading:**

- Path: `asset(/badges/${concept.toLowerCase()}.png)` using the existing `utils/basePath` helper.
- All 8 existing concepts have PNGs — `causation.png`, `change.png`, `connection.png`, `form.png`, `function.png`, `perspective.png`, `reflection.png`, `responsibility.png`.
- No new assets to create.

**Animation sequence per medallion (staggered via `delayMs = i * 250`):**

| Time (relative to medallion's `delayMs`) | What happens |
|---|---|
| 0 ms | Outer circle + label scale in via `animate-badge-pop` |
| +200 ms | `animate-gentle-float` begins (subtle continuous bob) |
| +400 ms | Concept name pill fades in |
| +800 ms | Star accent sparkles |

With `delayMs = i * 250`:
- Concept 1: starts at 0 ms (full sequence 0–800 ms)
- Concept 2: starts at 250 ms (full sequence 250–1050 ms)
- Concept 3: starts at 500 ms (full sequence 500–1300 ms)

A left-to-right reveal that feels earned and ceremonial.

**Fallback on image load failure:**

If `/badges/{concept}.png` 404s (e.g. a game YAML references a new concept without its asset), the `onError` handler swaps in a `✨` emoji so the widget still renders. Quiet degradation, not a crash.

**Wrapping behavior:**

The parent `ConceptReveal` uses `flex flex-wrap justify-center gap-6`. 1, 2, or 3 concepts all look intentional on any screen. 4+ concepts wrap cleanly to a second row. Today's max is 2 concepts per game; headroom for future expansion costs nothing.

---

### Section 5 — Backend changes

Minimal — almost everything is frontend. Three backend edits.

#### Edit 1: Split celebrate and closing into distinct widgets

**File:** `backend/state_machine.py` — the Cat5 celebrate/closing block (currently around line 325, anchor: `if template_type == "cat5" and step in ("STEP_5_CELEBRATE", "STEP_6_CLOSING"):`).

**BEFORE:**

```python
# Cat5 celebrate/closing: always use achievement_image widget (with or without generated image)
if template_type == "cat5" and step in ("STEP_5_CELEBRATE", "STEP_6_CLOSING"):
    structured = context.get("structured_story")
    achievement_url = structured.achievement_image_data_url if structured else None
    role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
    widget_params: dict = {"title": role_title}
    # Show IB concepts only at closing — celebrate just shows the badge/image
    if step == "STEP_6_CLOSING":
        widget_params["concepts"] = key_concepts
    if achievement_url:
        widget_params["image_data_url"] = achievement_url
    return ScreenFrame(
        widget="achievement_image",
        widget_params=widget_params,
        animation="badge_reveal",
        trigger="on_correct",
        sfx_cue="badge_awarded",
    )
```

**AFTER:**

```python
# Cat5 celebrate: achievement image only — no concepts, no character names
if template_type == "cat5" and step == "STEP_5_CELEBRATE":
    structured = context.get("structured_story")
    achievement_url = structured.achievement_image_data_url if structured else None
    role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
    widget_params: dict = {"title": role_title}
    if achievement_url:
        widget_params["image_data_url"] = achievement_url
    return ScreenFrame(
        widget="achievement_image",
        widget_params=widget_params,
        animation="badge_reveal",
        trigger="on_correct",
        sfx_cue="badge_awarded",
    )

# Cat5 closing: concept reveal — large IB concept medallions, no image
if template_type == "cat5" and step == "STEP_6_CLOSING":
    role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
    return ScreenFrame(
        widget="concept_reveal",
        widget_params={"title": role_title, "concepts": key_concepts},
        animation="badge_reveal",
        trigger="on_enter",
        sfx_cue="celebration_fanfare",
    )
```

Celebrate never sends concepts. Closing never sends an image. Two distinct widget contracts.

#### Edit 2: Update directive.py closing widget override

**File:** `backend/turn_handling/directive.py` — closing speaker-output handler (currently around line 981, anchor: `if is_closing: turn_response.screen_widget = "achievement_image"`).

**BEFORE:**

```python
# For closing, keep the achievement/badge visible
if is_closing:
    turn_response.screen_widget = "achievement_image"
```

**AFTER:**

```python
# For closing: Cat5 uses concept_reveal, Cat1 still uses achievement_image
if is_closing:
    if state.template_type == "cat5":
        turn_response.screen_widget = "concept_reveal"
    else:
        turn_response.screen_widget = "achievement_image"
```

The pre-advance screen frame snapshot trick (added in an earlier session to fix the "Your adventure begins..." ENDED-step fallthrough bug) stays in place. The change is only the widget name.

#### Edit 3: Celebrate handler — snapshot screen frame BEFORE advancing (critical)

**File:** `backend/turn_handling/directive.py` — celebrate handler (currently around line 940, anchor: `if _is_celebrate_step(state.current_step):`).

**Why this edit is required under the new design.** The current celebrate handler does:

```python
_advance_state(state)  # state → STEP_6_CLOSING
return TurnResult(
    turn_response=turn_response,
    screen_frame=_get_screen_frame(state),  # gets frame for STEP_6_CLOSING !
    ...
)
```

Today this quirk is invisible because STEP_5_CELEBRATE and STEP_6_CLOSING both render as `achievement_image` (with slightly different params). Under the new design, celebrate is `achievement_image` and closing is `concept_reveal` — so computing `_get_screen_frame(state)` AFTER the advance means the celebrate turn returns a `concept_reveal` frame, and the achievement image would never render to the user. Instead, the frontend would jump from synthesis straight to concept medallions.

**The fix** mirrors the existing closing-step pre-advance-frame-snapshot trick:

**BEFORE:**

```python
if _is_celebrate_step(state.current_step):
    directive.screen_widget = "achievement_image"
    directive.sfx_cue = "badge_awarded"
    try:
        turn_response = await script_agent.generate_turn_from_directive(state, directive)
    except Exception as e:
        speaker_errors.append(f"celebrate: {e}")
        logger.warning("Directive speaker failed at celebrate, falling back: %s", e)
        turn_response, _ = await _generate_with_retry(script_agent, state)
    turn_response.screen_widget = "achievement_image"
    turn_response.sfx_cue = "badge_awarded"
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    # Advance to closing now, so the next auto-advance turn
    # arrives at STEP_6_CLOSING instead of looping at celebrate.
    _advance_state(state)
    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=_should_auto_advance(state),
        response_type="celebrate",
        error_exit=False,
        debug=_debug(None, turn_response),
    )
```

**AFTER:**

```python
if _is_celebrate_step(state.current_step):
    directive.screen_widget = "achievement_image"
    directive.sfx_cue = "badge_awarded"
    try:
        turn_response = await script_agent.generate_turn_from_directive(state, directive)
    except Exception as e:
        speaker_errors.append(f"celebrate: {e}")
        logger.warning("Directive speaker failed at celebrate, falling back: %s", e)
        turn_response, _ = await _generate_with_retry(script_agent, state)
    turn_response.screen_widget = "achievement_image"
    turn_response.sfx_cue = "badge_awarded"
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    # Snapshot the celebrate screen frame BEFORE advancing — otherwise
    # _get_screen_frame(state) would return the closing frame
    # (concept_reveal) and the achievement image would never render.
    celebrate_screen_frame = _get_screen_frame(state)

    # Advance to closing so the next auto-advance turn arrives at STEP_6_CLOSING.
    _advance_state(state)

    return TurnResult(
        turn_response=turn_response,
        screen_frame=celebrate_screen_frame,
        auto_advance=_should_auto_advance(state),
        response_type="celebrate",
        error_exit=False,
        debug=_debug(None, turn_response),
    )
```

This is structurally identical to the existing closing-handler snapshot (added in an earlier session to fix the "Your adventure begins..." ENDED-fallthrough bug). One snapshot line, one variable rename in the `return`.

**Verification:** after applying Edits 1+2+3, manually trace both games:
1. dandelion (collaborative_story): synthesis last scene → celebrate → verify achievement_image renders during celebrate dialogue → auto-advance → closing → verify concept_reveal renders with Connection medallion.
2. polka_dot_patrol (comparison_reveal): synthesis reveal scene → celebrate → verify achievement_image renders → auto-advance → closing → verify concept_reveal renders with Form + Connection medallions.

#### What does NOT change on the backend

- `backend/turn_handling/synthesis.py` — synthesis flow unchanged.
- `backend/schemas/structured_story.py` — no schema changes.
- `backend/schemas/creative_slots.py` — no schema changes.
- `_generate_and_advance`, `_generate_structured_story`, `_generate_comparison_reveal` — unchanged.
- Auto-advance logic, `_should_auto_advance`, response types — unchanged.
- Cat1 celebrate/closing path — completely unchanged.
- Game YAML format (`backend/games/*.md`) — unchanged.

#### Tests to update

Grep `backend/tests/` for `STEP_6_CLOSING` and `achievement_image` to find test assertions that expect the old widget. Expected hits:

- Any test calling `get_screen_frame("STEP_6_CLOSING", "cat5", ...)` and asserting on widget name → expect `"concept_reveal"` instead.
- Any snapshot/fixture of the closing screen frame → regenerate.
- Cat1 closing tests → no change (Cat1 still uses `achievement_image` / `badge_award`).

Commands during implementation:

```bash
cd backend
uv run grep -rn STEP_6_CLOSING tests/
uv run grep -rn 'widget.*achievement_image' tests/
```

---

### Section 6 — File change summary

#### Files created

| File | Purpose | Approx lines |
|---|---|---|
| `frontend/src/widgets/ConceptReveal.jsx` | Closing widget: title + medallion row + role line | ~45 |
| `frontend/src/widgets/ConceptMedallion.jsx` | Single medallion circle, name pill, staggered animation | ~55 |
| `frontend/src/widgets/FallbackTrophy.jsx` | Extracted fallback for `AchievementImage` when no image_data_url | ~35 |
| `frontend/src/components/StageModeFooter.jsx` | 48px footer strip showing latest AI line + speaker icon | ~30 |

#### Files modified

| File | Change |
|---|---|
| `frontend/src/App.jsx` | Derive `stageMode` from `sessionState.current_step`; apply `stage-mode` class to `<main>`; conditionally render `<StageModeFooter>` instead of `<ConversationPanel>` contents when `stageMode` is true |
| `frontend/src/index.css` (or the equivalent layout CSS file) | Add `.stage-mode` rules for `.app-top-panel` and the conversation section; add `transition: flex-basis 500ms ease-out` base rule |
| `frontend/src/components/DeviceScreen.jsx` | Import `ConceptReveal`; add to `WIDGET_MAP`; add `'concept_reveal'` to full-panel widget list (currently line 131) |
| `frontend/src/widgets/AchievementImage.jsx` | Simplify per Section 2: remove `concepts`, remove `sessionState` / `collectedNames`, extract fallback, bump sizes/shadows/corners |
| `backend/state_machine.py` | Split Cat5 celebrate/closing branch into two distinct returns per Section 5 Edit 1 |
| `backend/turn_handling/directive.py` | Two changes: (a) closing widget override sends `concept_reveal` for Cat5 (Section 5 Edit 2); (b) celebrate handler snapshots `_get_screen_frame(state)` BEFORE `_advance_state(state)` so the celebrate turn actually returns the `achievement_image` frame (Section 5 Edit 3 — critical) |
| `backend/tests/**` | Update any test asserting `widget="achievement_image"` at STEP_6_CLOSING for Cat5 to expect `"concept_reveal"` |

#### Files NOT touched

- `backend/turn_handling/synthesis.py`
- `backend/schemas/*.py`
- `frontend/src/canvas/ExplorerMap.jsx` (the reference, not the target)
- `frontend/src/widgets/StoryScene.jsx`, `StoryLoading.jsx`
- `backend/games/*.md`
- Cat1 code paths anywhere

---

## Success criteria

1. At STEP_5_CELEBRATE, the device panel has grown to fill the viewport and the achievement image renders at its natural aspect ratio with no cutoff, regardless of whether the image is 16:9 or squarer. Verified manually across dandelion (3-scene story) and polka_dot_patrol (1-scene comparison).
2. At STEP_5_CELEBRATE, no character name pills and no concept pills appear — only role title + image.
3. At STEP_6_CLOSING, the screen shows only: role title flanked by sparkle emojis, large circular concept medallions using `/badges/{concept.lower()}.png`, and a role line ("You are now a {title}!"). No image, no character names.
4. Medallions animate in staggered with 250ms gaps, using `animate-badge-pop` → `animate-gentle-float` → name pill fade-in → star sparkle. Order matches Section 4.
5. Medallion circle size is `clamp(6rem, 22vw, 8rem)` — visibly larger than `ExplorerMap` `ZoneSlot` (`clamp(4.5rem, 18vw, 6rem)`).
6. During stage mode, the conversation panel hides and a 48px footer strip shows the latest AI dialogue line. Speaker icon animates when TTS is playing.
7. Exiting stage mode (new session button or returning to an earlier step somehow) animates the layout back over 500ms without jank or content flashing.
8. Cat1 celebrate/closing path is unchanged — Cat1 games still render their existing widgets.
9. All existing backend tests pass after updating STEP_6_CLOSING widget assertions.
10. `frontend/public/badges/*.png` is unchanged (assets were already there; we just consume them).

---

## Open questions (resolved during brainstorming)

1. **Footer shows `isSpeaking` TTS state?** → **Yes.** Small animated speaker icon when TTS is playing. Cheap and reassuring.
2. **Tap-to-explain on medallions?** → **No, out of scope.** Design the component so `onClick` can be added later without restructuring.
3. **Role line text source?** → **Hardcoded English in the widget** for this pass. Promote to backend-sourced when i18n or per-game customization is needed.
4. **Explicit exit animation?** → **No.** The `transition: flex-basis 500ms ease-out` handles the reverse direction fine. Flag during implementation if it feels abrupt.
5. **Handling `concepts == []` edge case?** → **Punt.** Today's minimum is 1 concept per game. If a game ever ships with empty concepts, `ConceptReveal` will render title + role line with no medallions — acceptable degradation. Revisit if real content hits this case.

---

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Flex transition jitters on some browsers during the stage-mode toggle | Medium | Low — cosmetic only | Test on Safari + Chrome + Firefox before merging. Fall back to `transform: scaleY()` wrapper if needed. |
| Conversation panel messages list unmounts + loses scroll position when returning to normal mode | Low | Low — only a problem if the user bounces between modes (rare) | `ConversationPanel` should preserve scroll via its own state; verify with manual testing. |
| Badge PNG fails to load (file naming mismatch, case sensitivity) | Low | Low — `onError` handler degrades to ✨ emoji | Verify at implementation that `concept.toLowerCase()` matches all 8 filenames exactly. |
| Tests assert on `widget="achievement_image"` in more places than expected | Medium | Low — caught by test run | Run full backend test suite immediately after the state_machine edit; fix all breakage before moving on. |
| `concept_reveal` widget registered but not added to the full-panel list in DeviceScreen (line 131) | Medium | High — widget renders inside the constrained 17rem wrapper and looks broken | Both changes in DeviceScreen.jsx must happen in the same edit. Included in the checklist. |
| Someone adds a new IB concept to a game YAML without adding the PNG | Low | Low — `onError` handles it | Document the convention in a code comment near `ConceptMedallion`'s `badgeSrc`. |
| Cat1 closing accidentally routed through `concept_reveal` | Low | Medium — Cat1 games would render empty closing | Section 5 Edit 2's `if state.template_type == "cat5"` guard prevents this. Add a backend test. |
| Celebrate handler forgets to snapshot `screen_frame` before `_advance_state` | High if overlooked | **Critical** — achievement image never renders to the user; celebrate turn returns `concept_reveal` frame because state is already at STEP_6_CLOSING when `_get_screen_frame` is called | Section 5 Edit 3 explicitly calls this out and shows the before/after code. Manual E2E trace in the verification commands confirms the achievement image renders during the celebrate dialogue before transitioning to closing. |

---

## Verification commands

```bash
# Backend
cd backend
uv run pytest tests/ -q --ignore=tests/test_ai_quality.py
uv run ruff check state_machine.py turn_handling/directive.py
uv run mypy state_machine.py turn_handling/directive.py

# Frontend
cd ../frontend
npm run lint
npm run build

# E2E manual sanity check (requires live backend + Vertex AI credentials)
cd ../backend && uv run uvicorn server:app --port 8000 &
cd ../frontend && npm run dev
# Then in browser:
# 1. Start dandelion (fluffy_expedition_dandelion) game
# 2. Run to celebrate — verify:
#    - Device panel grows to full viewport
#    - Conversation panel collapses to 48px footer
#    - Latest AI line visible in footer with speaker icon
#    - Achievement image renders without cutoff
#    - No character names, no concept pills on screen
# 3. Auto-advance to closing — verify:
#    - Concept medallions animate in staggered (Connection for dandelion)
#    - Role title "Dandelion Explorer" (or whatever the game sets)
#    - Role line "You are now a Dandelion Explorer!"
#    - No image, no character names
#    - Medallions sized larger than ZoneSlots from collection phase
# 4. Click "new session" from closing — verify layout animates back to split view
# 5. Repeat with polka_dot_patrol (ladybug, 2 concepts: Form + Connection)
# 6. Repeat with a Cat1 game (mood_changer_dog) — verify Cat1 closing unchanged
```

---

## Reference: exact file paths and line anchors (2026-04-10 snapshot)

Line numbers drift — use the anchor strings.

| What | File | Anchor |
|---|---|---|
| Current `AchievementImage` widget | `frontend/src/widgets/AchievementImage.jsx` | `export default function AchievementImage` |
| Current `ExplorerMap` `ZoneSlot` reference | `frontend/src/canvas/ExplorerMap.jsx` | `function ZoneSlot(` |
| `WIDGET_MAP` registration | `frontend/src/components/DeviceScreen.jsx` | `const WIDGET_MAP = {` |
| Full-panel widget list | `frontend/src/components/DeviceScreen.jsx` | `screenFrame.widget === 'explorer_map' \|\| screenFrame.widget === 'story_scene'` |
| Device panel size classes | `frontend/src/App.jsx` | `app-top-panel h-[55%] max-h-[34rem]` |
| Conversation panel wrapper | `frontend/src/App.jsx` | `aria-label="Conversation panel"` |
| Cat5 celebrate/closing branch | `backend/state_machine.py` | `if template_type == "cat5" and step in ("STEP_5_CELEBRATE", "STEP_6_CLOSING"):` |
| Closing widget override | `backend/turn_handling/directive.py` | `if is_closing: turn_response.screen_widget = "achievement_image"` |
| Celebrate widget override | `backend/turn_handling/directive.py` | `if _is_celebrate_step(state.current_step):` |
| Badge PNG assets | `frontend/public/badges/` | 8 files: causation, change, connection, form, function, perspective, reflection, responsibility |
| IB concept sources | `backend/games/*.md` | frontmatter `concepts_earned:` |
