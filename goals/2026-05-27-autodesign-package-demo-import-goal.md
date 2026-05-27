# Autodesign Package Demo Import Goal

## Mode

Plan-backed.

## Objective

Implement fullstack-demo support for importing autodesign activity packages
after the autodesign demo contract lands, including entity binding, demo
frontmatter conversion, asset resolution, support gating, activity selection,
and prototype-style device preview UI.

## Design Source

- Plan: `docs/plans/2026-05-27-autodesign-package-demo-import.md`
- Producer contract:
  `/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/docs/plans/2026-05-27-demo-package-contract-assets.md`

The linked plan is authoritative for design rationale and implementation
context. This goal is authoritative for constraints, required checks, and
completion. If they conflict, stop and document the conflict before changing
behavior.

## Hard Constraints

- Do not execute against an unstable package contract. Use the merged
  autodesign contract or a pinned fixture from its final commit.
- Do not modify the autodesign repo in this goal.
- Do not replace the existing Cat1/Cat5 runtime before attempting conversion
  into the current game/frontmatter shape.
- Do not mark unsupported mechanics playable.
- Do not remove the horizontal reviewer/debug mode.
- Do not treat catalog clicks as production camera validation.
- Do not accept random generated images for reference-bound real-world assets
  such as constellations, artworks, maps, scientific diagrams, cultural
  artifacts, species, historical objects, or named places.
- Do not require live provider credentials for ordinary importer, parser, or UI
  tests.
- Do not edit secrets, `.env`, credentials, or machine-local config.
- Do not perform unrelated refactors, broad formatting sweeps, or dependency
  upgrades.

## Required Scope

- Add a deterministic package import layer for autodesign packages.
- Convert imported packages into parseable demo game frontmatter or an
  equivalent additive loader path.
- Bind activity and entity explicitly in the imported demo instance.
- Resolve `asset_manifest.yaml` into browser-safe asset paths.
- Validate reference-bound asset provenance and block or degrade activities
  whose required factual assets are missing or unverified.
- Gate supported, degraded, and unsupported mechanics.
- Update activity selection to show support status, entity binding, and asset
  readiness.
- Add prototype-style device preview mode with a round child-facing screen.
- Preserve the current horizontal screen as debug/reviewer mode.
- Browser-test at least one imported Cat1 and one imported Cat5 activity.

## Delegated Agent Rule

The user explicitly requested delegated-agent rules for this goal.

Use sub-agents only for independent exploration, implementation, verification,
or code review with disjoint ownership. Keep tightly coupled importer,
runtime-state, and frontend integration work local to the main agent unless
the ownership boundary is clear. The main agent remains responsible for
sequencing, integrating returned work, resolving conflicts, running final
checks, committing, and reporting.

Good delegation candidates:

- inspect the current game parser, converter scripts, and fixture patterns;
- audit frontend device/screen components and activity selection surfaces;
- design importer/support-gate test cases;
- verify asset resolver behavior and reference-bound provenance handling;
- run independent browser or code review after integration.

## Execution Rules

- Work in `wonderlens-activity-fullstack-demo`.
- Preserve the existing modified `AGENTS.md` or any other unrelated user
  changes; stage only goal files and implementation files you intentionally
  touch.
- Prefer using current backend parser and frontend widgets before adding new
  abstractions.
- Keep unsupported mechanics out of the playable list unless runtime/UI support
  is actually implemented and tested.
- Use conventional commits and do not push unless explicitly asked.

## Mandatory Ordering

1. Confirm the autodesign contract is merged or record a pinned fixture commit.
2. Add importer/parser tests before or alongside importer behavior.
3. Add support gate and asset resolver before activity selection UI depends on
   them.
4. Add device preview UI after backend selection state is available.
5. Run backend and frontend automated checks before browser verification.
6. Update plan and goal indexes to `Completed` or `Blocked` only after the
   implementation result is known.

## Preconditions

```bash
git status --short --branch
test -f docs/wonderlens_activity_demo_build_spec.md
test -f backend/server.py
test -f frontend/package.json
```

Also confirm one of:

```bash
test -f /Users/pharrelly/codebase/github/wonderlens-activity-autodesign/activities/<activity_id>/demo_support.yaml
test -f tests/fixtures/autodesign_packages/<activity_id>/demo_support.yaml
```

Replace `<activity_id>` with the selected fixture package. If neither exists,
stop and create or request the pinned fixture before implementation.

## Success Criteria

- A Cat1 autodesign package fixture imports into a playable demo activity.
- A simple Cat5 autodesign package fixture imports into a playable demo
  activity with separate catalog assets.
- Entity binding is explicit in generated IDs, frontmatter, and selection UI.
- `supported`, `degraded`, and `unsupported` mechanics are handled visibly and
  honestly.
- Missing required assets fail import or block playability; optional missing
  assets use declared fallback behavior.
- Reference-bound assets display only approved/verified files or block/degrade
  the activity with an explicit reason.
- Device preview mode renders the prototype-inspired shell and round screen
  without overlapping text.
- Horizontal debug mode remains available.
- Existing supported demo games continue to work.

## Required Checks

Minimum backend checks:

```bash
uv run pytest tests/test_game_parser.py tests/test_convert_game.py tests/test_photo_selector_fallbacks.py -q
```

Add and run focused importer/support-gate tests created by the implementation.

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
npm run test -- --run
```

Diff hygiene:

```bash
git diff --check
```

Browser verification after automated checks:

- start backend and frontend on available local ports;
- open the demo in a browser;
- complete a smoke path for one imported Cat1 fixture;
- complete a smoke path for one imported Cat5 fixture;
- verify unsupported activities are hidden or disabled;
- verify round device preview and horizontal debug mode both render;
- record screenshots or artifact paths.

If frontend or backend tooling is unavailable, document the missing tool and
perform the narrowest manual validation against the build spec and touched
files.

## Final Completion Gate

Do not mark achieved until:

- required scope is implemented or a real blocker is documented with evidence;
- success criteria are met;
- required backend, frontend, diff, and browser checks pass or a concrete
  tooling blocker is documented;
- plan and goal indexes are updated as appropriate;
- intended changes are committed with conventional commit messages.

Final response must include changed files, checks run, browser verification,
fixture coverage, remaining risks, and commit hashes.

## Goal Invocation

```text
/goal Implement goals/2026-05-27-autodesign-package-demo-import-goal.md. The user explicitly requests delegated-agent work for independent exploration, implementation, verification, and code review where ownership is disjoint. Stop only when its completion gate is satisfied or a blocker is documented.
```
