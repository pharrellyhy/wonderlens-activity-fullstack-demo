# Creative Diversity Framework — Implementation Plan

**Goal:** Replace the current fixed-example prompt system with a multi-layered diversity framework that injects variety at every level of the prompt pipeline — from which examples the LLM sees, to what narrative voice it adopts, to per-turn creative constraints and output selection.

**Problem:** Dialogue turns are repetitive across sessions because the LLM sees the same baked-in few-shot examples every time and copies them. The current variety mechanism (`_VARIETY_HINTS` × 10, `_SYNTHESIS_HINTS` × 10) only covers early steps. No narrator personality variation exists, and there's no measurement infrastructure to quantify improvement.

**Architecture:** Four diversity components layered at different points in the prompt pipeline, plus an eval harness to measure before/after:

```
Session start
  └─ Personality assigned (session-level voice)

Per-turn generation
  ├─ System prompt
  │   ├─ Tier constraints (fixed)
  │   ├─ Personality voice ← Component 2 (HOW to speak)
  │   ├─ Step rules (structural only, no examples)
  │   └─ Sampled examples ← Component 1 (WHAT patterns to follow)
  ├─ User prompt
  │   ├─ Turn context (child input, round, phase)
  │   └─ Variety hint ← Component 3 (per-turn micro-constraint)
  └─ Generate N candidates → pick best ← Component 4 (output filter)
```

---

## Phase 1: Eval Harness (Measurement Baseline)

Repurposed from `docs/plans/2026-03-26-autoresearch-prompt-optimization.md`. Build the scoring module and evaluation harness only. The autonomous agent loop (`program.md`) is not built — the eval harness is a measurement tool, not an optimization engine.

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/scoring.py` | 6 scoring functions: `score_validation_pass`, `score_item_suggestion_free`, `score_completion_language`, `score_tier_compliance`, `score_phrasing_variety`, `compute_composite_score` |
| `scripts/evaluate_prompts.py` | Headless harness — runs 6 scenario YAMLs against live backend, scores responses, outputs composite score |
| `tests/test_scoring.py` | ~16 unit tests for scoring functions |
| `results/.gitkeep` | Experiment results directory |

### Files to Modify

| File | Change |
|------|--------|
| `.gitignore` | Add `results/*.tsv`, `results/*.log` |

### Composite Weights (adjusted for single-pass, two-pass disabled)

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Validation pass rate | 50% | T0 scaffolding, open question avoidance |
| Item suggestion free | 25% | No specific item suggestions in collection prompts |
| Completion language | 15% | No premature "all done" when items remain |
| Tier compliance | 5% | Sentence count, emotion tag presence |
| Phrasing variety | 5% | Progress note diversity across rounds |

### Key Details

- `scoring.py` imports `_ends_with_open_question`, `_has_model_phrase`, `_has_completion_language` from `turn_handler.py` via `sys.path.insert`
- `evaluate_prompts.py` adapts scenario walking from `scripts/run_dandelion_scenarios.py` (session start, turn walking, auto-advance), replacing `must_contain`/`must_not_contain` with scoring calls
- Phrasing variety uses Jaccard distance on word sets (no scikit-learn dependency)
- Evaluation scenarios: fluffy_expedition_dandelion (T0), _t1, _decline, _silent, _wrong_photos, _offtopic

### Verification

- `uv run pytest tests/test_scoring.py -v` — all pass
- `uv run ruff check scripts/ tests/test_scoring.py`
- With backend running: `uv run python scripts/evaluate_prompts.py --repeats 1` — outputs composite_score
- Record baseline in `results/results.tsv`

---

## Phase 2: Dynamic Example Library (Highest Impact)

Replace baked-in examples in step instruction `.md` files with dynamically sampled examples from YAML libraries, so each session sees different few-shot examples.

### Files to Create

| File | Step Group | Examples (approx) |
|------|-----------|-------------------|
| `backend/skills/examples/cat5_hook_mission.yaml` | STEP_1_HOOK + STEP_2_MISSION | ~10 |
| `backend/skills/examples/cat5_collect.yaml` | STEP_3_COLLECT_* (all phases/tiers) | ~20 |
| `backend/skills/examples/cat5_synthesis.yaml` | STEP_4_SYNTHESIS | ~10 |
| `backend/skills/examples/cat5_celebrate_closing.yaml` | STEP_5_CELEBRATE + STEP_6_CLOSING | ~8 |
| `backend/skills/examples/cat1_round.yaml` | STEP_3_ROUND_* (all game mechanics) | ~12 |

### Example YAML Schema

```yaml
step_group: cat5_collect
examples:
  - tier: T0
    phase: A
    scenario: correct_photo
    style: naming_story
    text: |
      **Phase A — Correct photo (1st find, item is fuzzy moss):**
      AI: "[excited] Ooh, fuzzy moss! Your first one! Give it a little poke — squishy or bumpy?"
```

Each example tagged with tier, phase, scenario, style. Content strategy: existing baked-in examples become the seed, then 2-3 additional variations per tier/phase/scenario to reach ~60 total.

### Files to Modify

**`backend/agents/script_agent.py`** — Add 3 functions:
- `_load_example_library(step_group)` — `@lru_cache` YAML loading
- `_sample_examples(step_group, tier, n=3, phase=None, style=None)` — filter + random sample, returns formatted markdown
- `_map_step_to_example_group(step, template_type)` — maps step name to YAML file

In `_load_step_instructions()`: resolve `{sampled_examples}` placeholder after existing template variable replacements.

**18 step instruction `.md` files** — For each:
1. Keep structural rules, goal, context sections intact
2. Remove per-tier example blocks (`#### T0`, `#### T1`, `#### T2` under `### EXAMPLES`)
3. Replace with `{sampled_examples}` placeholder with anti-copying annotation:

```markdown
### EXAMPLES (sampled for this session — do NOT memorize or reuse these exact words)

{sampled_examples}
```

Files: `cat5_step1_hook.md`, `cat5_step2_mission.md`, `cat5_step3_collect.md`, `cat5_step3_collect__naming_story.md`, `cat5_step3_collect__sorting_game.md`, `cat5_step3_collect__comparison_chart.md`, `cat5_step4_synthesis.md`, `cat5_step4_synthesis__naming_story.md`, `cat5_step4_synthesis__sorting_game.md`, `cat5_step4_synthesis__comparison_chart.md`, `cat5_step5_celebrate.md`, `cat5_step6_closing.md`, `cat1_step3_round.md`, `cat1_step3_round__riddle_game.md`, `cat1_step3_round__prediction_game.md`, `cat1_step3_round__helper_hotline.md`, `cat1_step3_round__voice_acting.md`, `cat1_step3_round__storytelling_chain.md`

### Verification

- `uv run pytest` — all existing tests pass
- `uv run ruff check backend/agents/script_agent.py`
- Manual: start 2 sessions, diff system prompts (DEBUG log) → different examples appear
- `uv run python scripts/evaluate_prompts.py --repeats 3` — no regression

---

## Phase 3: Session Personality System

5 narrator personalities randomly assigned per session, describing style (not complexity) so they don't conflict with tier sentence limits.

### Files to Create

**`backend/skills/personalities.yaml`** — 5 personalities:

| ID | Voice | Celebration Style |
|----|-------|-------------------|
| `curious_explorer` | Wonder, tiny details, "I wonder..." | Genuine amazement at each discovery |
| `silly_scientist` | Funny comparisons, sound effects, pretend experiments | Quirky professor declaring findings |
| `gentle_storyteller` | Calm, metaphors, storybook energy | Wraps celebrations in narrative |
| `excited_friend` | High energy, exclamations, cheerleader | Over-the-moon, can't contain joy |
| `wise_guide` | Calm, observational, "Let's take a closer look" | Quiet pride, specific observations |

### Files to Modify

| File | Change |
|------|--------|
| `backend/schemas/session_state.py` | Add `narrator_personality: str = ""` field |
| `backend/recipe_loader.py` | Add `_load_personalities()` (cached), `_pick_narrator_personality()`. Call in `recipe_to_session_state()`. Add `import yaml` |
| `backend/agents/script_agent.py` | Add `_load_personalities_map()` (cached), `_format_personality(id)`. Add `{personality}` to replacements in `_build_system_prompt()` |
| `backend/skills/script_turn.md` | Add `{personality}` placeholder between Section 1 (Persona, line 19) and Section 2 (Tier Rules, line 21) |

### Design Decisions

- Personality stored as plain ID string in session state (lightweight, serializable)
- Resolved to formatted prompt text at assembly time via cached YAML lookup
- Placed after persona section, before tier rules → style from personality, complexity from tier
- Personality describes style only → tier constraints still control sentence limits

### Verification

- `uv run pytest` — all pass (new field defaults to `""`)
- Manual: start 5 sessions, check logs for different personality IDs
- `uv run python scripts/evaluate_prompts.py --repeats 3` — stable or improved

---

## Phase 4: Expanded Variety Hints

Extend the variety hint mechanism from early steps to ALL steps, with step-specific hint pools.

### File to Modify: `backend/agents/script_agent.py`

Add 4 new hint pools (module-level):
- `_COLLECT_PHASE_A_HINTS` (15 items) — celebrate finds, texture, comparison, sensory words
- `_COLLECT_PHASE_B_HINTS` (10 items) — naming, cast building, child's words, character connection
- `_CELEBRATE_HINTS` (10 items) — specific moments, personality, journey recap
- `_CLOSING_HINTS` (10 items) — concept weaving, forward-looking, gratitude

Replace `_VARIETY_STEPS` set with `_STEP_HINT_MAP` dict mapping step names → hint pools.

Update hint selection in `_build_user_prompt()`:

| Step | Hint Pool |
|------|-----------|
| `STEP_4_SYNTHESIS` | `_SYNTHESIS_HINTS` (unchanged) |
| `STEP_3_COLLECT_*` (ALL rounds) | `_COLLECT_PHASE_A_HINTS` or `_COLLECT_PHASE_B_HINTS` based on `collection_phase` |
| `STEP_3_ROUND_*` | `_COLLECT_PHASE_A_HINTS` |
| Hook/rules/mission | `_VARIETY_HINTS` (unchanged) |
| Celebrate | `_CELEBRATE_HINTS` |
| Closing | `_CLOSING_HINTS` |

**Key change:** Remove the `is_first_collect` gate — all collection rounds now get hints.

### Verification

- `uv run pytest` — all pass
- Manual: round 2 and 3 collect steps now include style hints
- `uv run python scripts/evaluate_prompts.py --repeats 3` — phrasing_variety improves

---

## Phase 5: Best-of-N Selection (Optional Polish)

Generate 2 candidates in parallel for key steps, pick the better one using lightweight scoring.

### Files to Modify

| File | Change |
|------|--------|
| `backend/config.py` | Add `best_of_n: int = 1` (disabled by default) |
| `backend/agents/script_agent.py` | Add `_score_candidate(turn, state)` and `_generate_best_of_n(state, n)`. Gate in `generate_turn()` for `STEP_3_COLLECT_*` and `STEP_4_SYNTHESIS` |

### Scoring Heuristic (lightweight, CPU-only)

| Component | Weight | Method |
|-----------|--------|--------|
| Phrase novelty | 50% | Jaccard distance from last 3 AI turns |
| Tier compliance | 30% | Emotion tag present + sentence count ≤ tier max |
| Structural checks | 20% | No item suggestions, no premature completion language |

### Design Details

- `asyncio.gather` for parallel generation → wall-clock = 1x (not 2x)
- Only for `STEP_3_COLLECT_*` and `STEP_4_SYNTHESIS` (~5-6 turns per session)
- Disabled by default (`best_of_n: 1`). Set to `2` to enable
- Cost: 2x LLM calls for those steps only

### Verification

- `uv run pytest` — all pass
- Manual with `best_of_n: 2`: logs show scoring and selection
- `uv run python scripts/evaluate_prompts.py --repeats 3` — compare with/without

---

## Implementation Sequence

```
Phase 1 (Eval Harness)        ← measure baseline
    ↓
Phase 2 (Dynamic Examples)     ← highest impact, measure after
    ↓
Phase 3 (Personality System)   ← measure after
    ↓
Phase 4 (Expanded Hints)       ← measure after
    ↓
Phase 5 (Best-of-N)            ← only if 2-4 leave room
```

Each phase: measure baseline → implement → measure after → verify no regression.
