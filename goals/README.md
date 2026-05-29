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
| 2026-05-29 | Planned | [Pilot Flow Robustness, Asset Regeneration, and Crown UI Goal](./2026-05-29-pilot-flow-robustness-and-asset-regen-goal.md) | [Plan](../docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen-implementation.md) | Autonomous `/goal` gate = Streams 1+2 & 4 + Stream 3 scaffolding (offline checks); Stream 3 art sign-off, live smoke, and browser walkthrough are human-gated. |
