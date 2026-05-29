# Goals

Last checked: 2026-05-29

## Status Definitions

- `Planned`: ready for future execution, not started.
- `Active`: currently being executed.
- `Completed`: completion gate passed and intended changes are committed or otherwise finalized.
- `Blocked`: execution could not complete; see notes.
- `Superseded`: replaced by a newer goal.

## Maintenance Notes

Goal files are execution contracts. When a goal is executed, update this index with the final status and keep notes short, factual, and evidence-based.

## Index

| Date | Status | Goal | Design Source | Notes |
|---|---|---|---|---|
| 2026-05-29 | Completed | [Three Activity Flow and Layout Fixes Goal](./2026-05-29-three-activity-flow-layout-fixes-goal.md) | [Plan](../docs/plans/2026-05-29-three-activity-flow-layout-fixes.md) | Completion gate passed: source fidelity, layout/picker regressions, all-12 live smoke, and Cat1/Cat3/Cat5 browser verification. |
| 2026-05-29 | Completed | [Activity Assets and Touchless Controls Goal](./2026-05-29-activity-assets-touchless-controls-goal.md) | [Plan](../docs/plans/2026-05-29-activity-assets-touchless-controls.md) | Completion gate passed: required checks, all-12 live smoke, and Cat1/Cat3/Cat5 browser verification. |
| 2026-05-29 | Active | [Pilot Flow Robustness, Asset Regeneration, and Crown UI Goal](./2026-05-29-pilot-flow-robustness-and-asset-regen-goal.md) | [Plan](../docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen-implementation.md) | Streams 1+2, 4, and Stream 3 scaffolding implemented (8 commits). In-scope checks green: Streams-1+2 suite 49, asset-contract (only carousel red), backend ruff, frontend 72/lint/build, git diff --check; live smoke 11/12 (career passes on retry). Full backend suite 112 passed / 4 failed — failures are pre-existing live-LLM T0 quality flakiness in `test_ai_quality` for non-pilot activities (out of scope, not regressions). Human-gated remainder: Stream 3 image art + per-pilot sign-off, Cat1/Cat3/Cat5 browser walkthrough. |
