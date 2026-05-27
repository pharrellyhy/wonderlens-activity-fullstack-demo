# Autodesign Package Demo Import Implementation Plan

Date: 2026-05-27

Status: Completed

## Goal

Make the fullstack demo consume autodesign activity packages through a small
import layer, explicit entity binding, generated asset resolution, support
gating, and a prototype-device preview UI.

This is the consumer-side follow-up to the autodesign producer contract:

```text
/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/docs/plans/2026-05-27-demo-package-contract-assets.md
```

## Dependency

Execute this goal after the autodesign contract is merged, or against a pinned
generated package fixture from the final autodesign contract commit.

The fullstack demo should not build against a moving package contract unless
the fixture commit is recorded in the implementation notes.

## Current Context

The demo already has a useful runtime shape:

- top-level `backend/games/*.md` files with YAML frontmatter;
- `backend/game_parser.py` for frontmatter parsing;
- Cat1 dialogue and Cat5 collection flows;
- Cat5 synthesis support;
- frontend widgets for photos, progress, badges, and scenes;
- current horizontal split-view reviewer UI.

Existing Cat5 asset planning lives in `docs/cat5-image-asset-list.md`, but it
is manually curated for two games and does not define a general package asset
contract. It also uses storybook/photo prompt styles, while the next demo
should align with the physical prototype: warm porcelain body, dark circular
screen, mint controls, and soft 3D toy-like visuals.

The current fullstack demo can use catalog choices for web play, but
WonderLens AI production capture remains real-camera and criterion based. This
repo should keep catalog choices as demo scaffolding and never treat them as a
claim about production validation.

## Settled Decisions

- Do not rewrite the runtime before importing packages. Convert autodesign
  packages into the existing demo game/frontmatter shape first.
- Bind entity and activity explicitly for each imported demo instance.
- Use existing Cat1 and Cat5 UI templates whenever the package honestly fits.
- Gate unsupported mechanics rather than building minimal runtimes for every
  new activity type.
- Treat `collection_catalog` and asset manifests as demo scaffolding.
- Add a prototype-style device preview with a round child-facing screen.
- Keep the horizontal screen/debug view for reviewer and developer workflows.
- Do not execute this goal before the autodesign contract is merged unless a
  pinned package fixture is committed for tests.

## Import Contract

The importer should read one package directory with at least:

```text
spec.md
prod.md
tag_block.yaml
recap.template.yaml
dashboard.template.yaml
```

For demo-ready packages, it should also read:

```text
demo_support.yaml
asset_manifest.yaml
runtime.yaml       # when available from the runtime converter
```

Output should be deterministic and reviewable:

```text
backend/games/<demo_id>.md
frontend/public/activity-assets/<demo_id>/...
```

`demo_id` should bind package and entity, for example:

```text
fluffy_expedition_dandelion__dandelion
```

The generated game frontmatter should preserve the current parser contract:

- `activity_type`
- `entity_name`
- `category`
- `template_type`
- `display_label`
- `tier`
- `play_rounds`
- `creative_slots`
- `step_instructions`
- `collection_catalog`
- `screen_frames`
- `celebration_frame`
- `plain_description`
- synthesis metadata when present

## Support Gate

Use `demo_support.yaml` when present. If it is absent, infer conservatively and
mark the package as not demo-ready unless a fixture explicitly overrides it.

MVP status handling:

| Status | Demo behavior |
|---|---|
| `supported` | Show as playable by default. |
| `degraded` | Show only when the user enables degraded demos or show with a visible reviewer warning. |
| `unsupported` | Hide by default or render disabled with reasons. |

MVP templates:

| Template | Behavior |
|---|---|
| `cat1_dialogue` | Existing Cat1 conversation UI. |
| `cat5_collection` | Existing Cat5 collection UI with catalog candidates as clickable fake captures. |
| `cat5_judgment` | Existing Cat5 UI plus text/name explanation or fixture judgment when available. |
| `none` | Not playable. |

Do not silently remap unsupported drawing, coloring, sorting, building,
tournament, certificate, or complex Cat3 activities into Cat1/Cat5.

## Asset Resolution

Read `asset_manifest.yaml` and copy or resolve separate assets into:

```text
frontend/public/activity-assets/<demo_id>/
```

The resolver should support:

- existing file paths from the manifest;
- generated file paths when present;
- placeholder or fallback rendering when an optional asset is missing;
- hard failure when a required supported asset has neither file, generation
  prompt, nor fallback.
- hard failure when a reference-bound asset lacks approved source/provenance
  metadata or a verified file. Constellations, artworks, maps, scientific
  diagrams, cultural artifacts, species, historical objects, named places, and
  similar factual references must not be replaced by random generated images.

Do not crop a six-image contact sheet at runtime as the normal path. A contact
sheet may be used as a review reference or temporary fixture only when clearly
marked.

Required MVP asset roles:

- entity hero;
- Cat5 correct item icons;
- Cat5 distractor icons;
- badge or celebration image;
- story or synthesis scene when the package requires it;
- optional activity preview thumbnail.

## Device Preview UI

The main demo should gain a product-facing device preview mode that resembles
the prototype device:

- warm off-white shell;
- dark circular screen;
- mint side controls and button accents;
- soft shadows and subtle bevels;
- child-facing content inside the round screen.

The round screen is smaller and more constrained than the current horizontal
panel. Do not squeeze the horizontal layout into the circle.

Round screen content should be minimal:

- one hero asset, catalog item, or scene at a time;
- compact progress dots or ring;
- simple capture or status icon;
- very short prompt text only when it fits safely;
- no transcript, debug JSON, large catalog grids, or dense controls.

Keep outside the device frame:

- conversation transcript;
- activity selection;
- catalog/debug choices;
- support status and asset readiness;
- runtime/frontmatter inspection.

The existing horizontal screen should remain available as a reviewer/debug
mode.

## Activity Selection

Update the selection surface to account for imported packages:

- show `supported` activities by default;
- optionally include `degraded` with a visible warning;
- hide or disable `unsupported`;
- display entity binding;
- display asset readiness;
- allow filtering by category, template, support status, and entity;
- avoid presenting unavailable assets as playable.

## Implementation Areas

### Package Importer

Likely files:

- `scripts/import_autodesign_package.py`
- `backend/game_parser.py` only if the current frontmatter contract needs a
  compatible additive field
- tests near `tests/test_convert_game.py` and `tests/test_game_parser.py`

Expected outcome:

- A fixture package imports into parseable game frontmatter.
- Entity binding is explicit in the output filename and frontmatter.
- Unsupported packages are skipped or emitted into a disabled registry, not
  loaded as playable games.

### Asset Resolver

Likely files:

- importer script or a small helper under `backend/` or `scripts/`
- `frontend/public/activity-assets/` fixture outputs when intentionally
  committed
- tests for missing required and optional assets

Expected outcome:

- Manifest paths resolve to browser-safe public URLs.
- Required assets are present or fail import with a useful error.
- Optional missing assets use declared fallback behavior.
- Reference-bound assets preserve the approved source identity and surface
  provenance or verification status for reviewers.

### Demo Runtime And API State

Likely files:

- `backend/server.py`
- backend schemas or state helpers if imported support metadata is exposed
- tests near `tests/test_api.py`, `tests/test_turn_flow.py`, and
  `tests/test_photo_selector_fallbacks.py`

Expected outcome:

- Imported Cat1 and simple Cat5 games run through existing flows.
- Cat5 catalog picks can simulate demo captures without weakening production
  camera semantics in other repos.
- Support status and asset readiness are available to the frontend.

### Frontend Device UI

Likely files:

- `frontend/src/`
- current device or widget components;
- CSS or design token files;
- frontend tests if available.

Expected outcome:

- Prototype-style device preview mode renders a circular screen.
- Horizontal debug mode remains available.
- Round screen layout has stable dimensions and no overlapping text.
- Device palette aligns with warm porcelain and mint prototype colors.

### Activity Selection

Likely files:

- frontend selection components;
- backend activity/game listing endpoint if selection data comes from API;
- tests for filters and disabled states.

Expected outcome:

- Supported activities are easy to start.
- Degraded activities are visible only when deliberately enabled.
- Unsupported activities are hidden or disabled with reasons.

## Validation Strategy

Minimum backend checks should include the importer, parser, and one Cat1/Cat5
fixture:

```bash
uv run pytest tests/test_game_parser.py tests/test_convert_game.py tests/test_photo_selector_fallbacks.py -q
```

Add focused tests for the importer and support gate. Include them in the final
check command.

Frontend checks after UI changes:

```bash
cd frontend
npm run lint
npm run build
npm run test -- --run
```

Run `git diff --check` from the repo root.

Browser verification is required after the device UI changes:

- start backend and frontend on available local ports;
- open the demo in a browser;
- verify one imported Cat1 activity starts and advances;
- verify one imported Cat5 activity shows catalog assets and advances;
- verify unsupported activities are hidden or disabled;
- verify round device preview and horizontal debug mode both render;
- capture screenshots or describe artifact paths.

## Implementation Notes

Completed on 2026-05-27 against the merged autodesign producer contract at
`72b97241b4f3bd235fe23df91f2fb3aa08ce8b47`.

The importer now consumes package fixtures, writes deterministic generated game
frontmatter under `backend/games/`, resolves browser-safe assets under
`frontend/public/activity-assets/`, and gates supported, degraded, blocked, and
unsupported package states before play starts. Cat1 dialogue and Cat5
collection fixtures import as playable demos; a reference-bound Cat5 judgment
fixture imports as degraded only when the asset provenance contract is
satisfied; an unsupported sorting fixture is skipped with an explicit reason.

Generated `step_instructions` come from the matching curated base game
frontmatter when the package `activity_id` already exists in `backend/games/`.
If no curated base exists, the importer emits deterministic default step
instructions for the supported template.

Frontend selection now shows entity binding, support status, asset readiness,
and degraded gating. Runtime start is blocked for unsupported demos and demos
with required missing assets. The default play surface uses the prototype-style
round device frame, while horizontal debug mode remains available.

## Non-Goals

- Do not change the autodesign package contract in this repo.
- Do not implement Cat3, drawing, coloring, sorting, building, tournament, or
  certificate runtimes.
- Do not remove the horizontal reviewer/debug surface.
- Do not claim catalog click validation equals real camera validation.
- Do not require live provider credentials for ordinary importer or UI tests.
- Do not edit secrets, `.env`, credentials, or machine-local config.

## Completion Gate

This plan is complete when:

- the importer consumes a merged or pinned autodesign package fixture;
- entity binding is explicit;
- generated game frontmatter parses and runs through existing Cat1/Cat5 flows;
- assets resolve from `asset_manifest.yaml` into browser-safe URLs;
- reference-bound assets are accepted only when source/provenance and verified
  files are present, or the activity is blocked/degraded with an explicit
  reason;
- unsupported and degraded mechanics are gated honestly;
- activity selection reflects support and asset readiness;
- device preview mode matches the prototype direction and keeps horizontal
  debug mode;
- backend, frontend, diff, and browser checks pass;
- intended changes are committed in this repo.
