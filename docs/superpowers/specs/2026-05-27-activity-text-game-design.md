# Activity Text Game Prototype - Design Spec

**Date:** 2026-05-27
**Status:** Draft for review
**Scope:** Standalone text-only activity game mode for the 12 exported activity packages.

## Context

The activity export bundle at
`/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/runs/20260521_163621_workbook_review_packet_full/activity_exports`
contains 12 generated activity exports. The reference implementation at
`/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo` already has a React/Vite frontend,
FastAPI backend, text turn API, Cat1 and Cat5 recipe flows, and live provider integration.

This work adds a standalone activity game surface inside a feature worktree of the fullstack demo repo. The user-facing
experience is text-only for v1, but it still calls the existing backend and provider APIs for activity responses.

The supplied device image is the physical UI reference: a compact white vertical handheld body, large circular black
lens/screen, mint left grip, mint top-right scroll control, small gray button, and larger mint action button.

## Confirmed Decisions

- Build inside `.worktrees/feat/activity-text-game` from the fullstack demo repo.
- Make all 12 exported activities playable in v1.
- Use the existing backend API path and live provider configuration rather than a frontend-only scripted engine.
- Preserve existing Cat1 and Cat5 flow semantics instead of redesigning the whole runtime.
- Add only the minimum Cat3 flow support needed for Guided Drawing.
- Keep the v1 UI text-only: typed input and AI text output only.
- Do not show microphone, TTS, audio, photo upload, or camera controls in v1.
- Generate style-consistent static activity display assets with Codex's internal imagegen workflow during implementation,
  then store the selected assets and manifest in the repo.
- Do not generate activity display assets invisibly at runtime.
- Use the word "activity" in product UI and docs for selectable items. Use "concept" only for educational fields such
  as "Core IB Key Concepts".

## Activity Set

| Activity | Export ID | Category | Mechanic | Tier | Core IB Key Concepts |
|---|---|---:|---|---|---|
| Phoneme Treasure Hunt | `concept_phoneme_hunt_collect` | cat5 | collect | T1 | Form and Connection |
| Partial Reveal Guess | `concept_partial_reveal_deduce` | cat1 | deduce | T1 | Form and Causation |
| Animal Sound Imitation | `concept_animal_sound_motion_voice` | cat1 | motion_voice | T1 | Form and Perspective |
| Word Echo Practice | `concept_word_echo_remember` | cat1 | remember | T1 | Form and Connection |
| Emotion Reader | `concept_emotion_reader_care` | cat1 | care | T1 | Form and Responsibility |
| Constellation Star Count | `concept_constellation_star_count_enumerate` | cat1 | enumerate | T1 | Form |
| Career Decision Role Play | `concept_career_decision_decide` | cat1 | decide | T1 | Form and Responsibility |
| Vegetable Sort | `concept_vegetable_sort_sort` | cat1 | sort | T1 | Form |
| Travel Planner | `concept_travel_planner_predict` | cat1 | predict | T1 | Form and Causation |
| Guided Drawing | `concept_guided_drawing_probe` | cat3 | build | T1 | Form and Change |
| Story Challenge Unlock | `concept_story_unlock_probe` | cat1 | imagine | T1 | Form and Perspective |
| Recognition Pop Challenge | `concept_recognition_pop_probe` | cat1 | compare | T1 | Form and Perspective |

## Feature Summary

The activity text game is a standalone tester-facing browser surface for trying 12 workbook-derived activities through
the real WonderLens backend. A user chooses an activity, starts a backend session, reads the AI turn, types a child
response, and watches the device screen update with current activity state.

The surface is child-friendly enough to match the prototype device, but it is primarily a product prototype for
reviewing activity flow quality, backend recipe behavior, and turn progression.

## Primary User Action

Choose an activity, start it, and continue the activity by typing child responses until the backend reaches completion
or graceful exit.

## Design Direction

**Selected direction:** Hybrid A+B from the visual companion probes.

- A contributes the child-facing toy feel and the physical device language.
- B contributes the tester-usable activity selector, transcript density, backend status, and preserved device scale.
- C is deferred because it makes the experience more immersive but weaker for testing 12 activities quickly.

**Color strategy:** Restrained product palette.

- Warm off-white app background.
- Soft white device body with subtle material depth.
- Mint controls, side grip, and scroll control.
- Small activity accent colors for badges and progress only.
- No gradient text, glass panels, decorative blobs, or marketing-style hero treatment.

**Theme scene sentence:** An education/product reviewer is testing activity quality at a desk in normal indoor light,
with a physical WonderLens prototype next to the browser. The UI should feel practical and reviewable while still
reflecting the child-facing object.

**Anchor references:**

- The provided WonderLens device screenshot for proportions and control placement.
- Existing fullstack demo split interaction pattern for transcript plus screen.
- Probe B for preserving product-prototype device scale.

## Layout Strategy

Desktop layout uses two main zones.

Left zone:

- Activity library with all 12 activities.
- Current activity metadata: tier, category, mechanic, activity status.
- Text conversation transcript.
- Single text input and send button.

Right zone:

- Preserved-ratio WonderLens device, not stretched to fill the panel.
- Device body uses a compact vertical rounded rectangle.
- The large circular black lens acts as the active screen.
- Top-right mint scroll wheel/rocker is visible and physically attached to the device edge.
- Lower physical controls match the screenshot: one small gray button and one larger mint action button.
- Supplemental tester status can sit near the device, but must not visually stretch or distort it.

Responsive behavior:

- Desktop keeps selector/conversation on the left and device on the right.
- Narrow screens stack activity selector, device, then transcript/input.
- Device maintains aspect ratio at all breakpoints.

## Device Interaction Model

The v1 device is mostly representational, but its physical controls should map to simple product behavior:

- Top-right scroll control:
  - Before a session: cycles through activities in the activity library.
  - During a session: scrolls or steps through lens-screen text/history when content overflows.
  - Must be keyboard accessible with a clear `aria-label`.
- Large mint button:
  - Starts the selected activity before a session.
  - Can restart the current activity after completion.
- Small gray button:
  - Opens compact session/debug metadata or toggles lens detail, if implemented.
  - It is secondary and must not compete with the text input.

The text input remains the only way to send child responses in v1.

## Activity Display Assets

The exported activity bundle includes visual exports, but they are not sufficient as final in-device assets. They are
not style-consistent with the provided WonderLens device appearance, and some files are contact-sheet style images with
multiple small phase panels inside one image.

V1 should include static display assets for activity identity and in-device phase display. These are visual support for
the activity, not user input or AI output controls. "Text-only" means the child interacts through typed text only.

Asset generation requirements:

- Use Codex's internal imagegen skill/tooling during implementation, not a separate app API or backend runtime API.
- Generate assets before or during development, then copy selected outputs into committed project paths.
- Keep original generated outputs outside the repo untouched unless copied into the project intentionally.
- Store final selected assets under a clear path such as `frontend/public/activity-assets/<activity_id>/`.
- Add a visible manifest mapping each activity to its icon, phase images, fallback label, and intended screen usage.
- Use exported visual assets only as semantic/reference material, not as final UI assets when they conflict with the
  device style.
- Use a shared WonderLens asset prompt/style guide so all activity assets share the device's soft white, mint,
  rounded-toy material language.
- Avoid in-image text wherever possible. Activity titles and prompts should be rendered by the UI for accessibility and
  localization.
- If a generated asset is missing or fails to load, the lens must show an honest text fallback instead of implying an
  image is present.

Recommended v1 asset set:

- One activity icon/thumbnail per activity for the activity library.
- Lens phase images should match the activity's runtime beats rather than a fixed count.
- Typical activity beats are intro/bridge, rules/setup, each core round, magic moment/synthesis, and closing/recap.
- The manifest should allow any number of beat images per activity, keyed by stable beat ids such as `intro`, `rules`,
  `round_1`, `round_2`, `round_3`, `synthesis`, and `recap`.
- If a beat does not have a usable image, the UI should fall back to the nearest activity-level image plus rendered text.

Asset generation must be inspectable:

- The prompts or prompt templates should live in the repo.
- Generated file paths should be listed in the manifest.
- Regeneration steps should be documented in the implementation plan or a follow-up authoring guide.
- The running activity game should only render assets already present in the repo or served from the local frontend
  public path.

## Backend Architecture

The activity game should call the existing backend, not a local scripted frontend engine.

Required backend behavior:

- Use `/api/start-deep-link` or a compatible new start endpoint for activity selection.
- Use `/api/turn` for typed child turns.
- Do not use `/api/turn-speak` in this v1 surface.
- Do not display or depend on STT, TTS, image upload, or photo recognition controls.
- Keep all activity definitions in backend-owned recipe/game data so future activities follow the same workflow.

Existing Cat1 and Cat5 behavior should be reused:

- Cat1 activities should map to existing in-device verbal flow: hook, rules, rounds, celebrate, closing.
- Cat5 activities should map to existing out-of-device collection flow, adapted for text-only collection by using typed
  responses or selectable text stand-ins rather than photo upload.

Guided Drawing requires Cat3 support:

- Add a minimal Cat3 "build" flow that fits the existing recipe/session model.
- Target steps: hook, tool/setup prompt, guided build rounds, celebrate, closing.
- Keep the Cat3 implementation narrow and testable. Do not redesign Cat1/Cat5 to accommodate Cat3.
- If implementation risk becomes high, the acceptable fallback is a documented Cat3-to-Cat1 compatibility mode for
  Guided Drawing, but only with explicit note in the implementation plan.

## Activity Authoring And Future Reuse

Adding future activities should be repeatable and documented.

Preferred workflow:

1. Start from an exported activity package containing `spec.md` and `prod.md`.
2. Convert metadata, premise, trigger, role, mechanic, rounds, and screen hints into a backend game/recipe definition.
3. Register the activity so the backend can start it by activity id or activity name.
4. Expose activity metadata to the frontend activity library.
5. Verify activity start, one typed turn, progression through rounds, and completion/exit.

Implementation should avoid hardcoding the 12 activities directly in UI behavior. The frontend may include display
metadata, but session behavior must come from backend recipe definitions.

## Key UI States

Default:

- Shows activity library, no active session, device lens invites user to choose an activity.

Loading:

- Starting activity: disable input and show activity start status.
- Sending turn: preserve transcript, disable send, show backend processing state.

Active:

- Transcript shows AI and child text turns.
- Lens shows the latest AI prompt, current activity, progress, mechanic, and saved text tokens.
- Activity selector remains visible but changing activity should require starting a new session.

Completed:

- Lens shows recap badge and saved turns.
- Input is disabled.
- Primary action becomes "Restart activity" or "Choose another activity".

Error:

- Backend unavailable, unknown activity, provider error, or session not found should appear inline.
- Error state should preserve current transcript when possible.
- UI should suggest retrying start or turn without exposing secret/config details.

Empty/No Response:

- Silence is represented only by typed empty/no-response controls if implemented later.
- V1 should not auto-send silence from timers because this surface is text-only and review-oriented.

## Content Requirements

Use "activity" terminology:

- "Choose an activity"
- "Activity library"
- "Current activity"
- "12 activities"
- "Start activity"
- "Restart activity"

Avoid "concept" in user-facing selection copy. Keep "Core IB Key Concepts" when referring to IB learning metadata.

The activity card should show:

- Activity name
- Category
- Mechanic
- Tier
- Short premise

The lens should show:

- Latest AI text
- Activity name
- Current round/progress
- Mechanic badge
- Saved child text tokens

## Live API And Credentials

Live backend verification must use credentials from the backend root and must not print or commit secret values.

Operator requirements:

- Load `.env` from `backend/` before starting the server.
- Ensure `.elaborate-baton-480304-r8-a8a39bcb34f1.json` from `backend/` is active for provider authentication.
- If the JSON file is a service-account credential file, use it as a credential path according to the existing backend
  configuration rather than echoing or editing its contents.
- Do not modify `.env`, the JSON credential file, or any generated secret material.

## Non-Goals For V1

- No microphone input.
- No TTS or audio playback.
- No image upload.
- No camera/photo recognition.
- No runtime image generation for activity assets.
- No replacement of existing Cat1/Cat5 turn flow.
- No broad frontend redesign outside the standalone activity game route/surface.
- No dependency upgrades.

## Implementation References

Most relevant existing code:

- `frontend/src/utils/api.js`
- `frontend/src/hooks/useConversation.js`
- `frontend/src/components/ConversationPanel.jsx`
- `frontend/src/components/DeviceScreen.jsx`
- `frontend/src/components/ToyCameraFrame.jsx`
- `backend/server.py`
- `backend/game_loader.py`
- `backend/game_parser.py`
- `backend/entity_registry.py`
- `backend/recipe_loader.py`
- `backend/state_machine.py`
- `backend/turn_handling/`
- `backend/skills/step_instructions/`

Most relevant design references:

- `docs/wonderlens_activity_demo_build_spec.md`
- `docs/plans/deep-link-game-entry.md`
- `docs/plans/game-md-single-source.md`
- `docs/plans/instruction-based-recipes.md`

## Open Questions For Implementation Planning

- Should the activity library use a new backend endpoint, or extend `/api/entities` to include activity entries beyond
  the existing demo entity allowlist?
- Should Cat3 be a true `template_type: "cat3"` in schemas and state machine, or a narrow compatibility layer that uses
  Cat1 mechanics with Cat3 labels for v1?
- For Cat5 text-only collection, should child typed text count as the collected item directly, or should the UI offer
  temporary text choices while still avoiding photo upload?
- Should the activity definitions keep their export ids as `activity_type`, or should they use cleaner product slugs
  with export ids stored as metadata?

## Self-Review

- The brief uses "activity" for product vocabulary and reserves "concept" for IB metadata only.
- The device proportions and top-right scroll control are explicit requirements.
- The v1 scope is text-only even though the repo supports STT, TTS, and photo upload elsewhere.
- Static activity display assets are now explicitly in scope, with build-time Codex imagegen generation and visible
  manifests rather than runtime generation.
- Existing Cat1/Cat5 runtime behavior is preserved.
- Cat3 is scoped as the only new flow gap.
- Future activity authoring is included as a design requirement, not left as an afterthought.
