# Plan: Style-Specific Step Instruction Fragments

## Context

The current step instruction system uses **shared templates per category** — all Cat 1 entities share `cat1_step3_round.md`, all Cat 5 entities share `cat5_step3_collect.md`. Template variables like `{game_mechanic}` and `{synthesis_type}` are injected, but the actual guidance doesn't change.

This means all Cat 5 entities get the same analytical "compare your finds" synthesis, even though the design doc envisions creative storytelling for some entities (naming finds as characters, creating stories). Different entities should emphasize different aspects — not every entity suits the same game style.

**Goal:** Make step instructions adapt per entity's game style by loading **style-specific fragment files** that append to the shared base template. The loader picks the right fragment based on `creative_slots.game_mechanic` (Cat 1) or `creative_slots.synthesis_type` (Cat 5).

## Design

### Fragment composition (append model)

For steps that need variation, the loader looks for a style-specific fragment file and appends it to the base template:

```
base template (shared rules, structure, branching)
+
style fragment (mechanic-specific guidance, examples, scaffolding)
=
final instruction sent to LLM
```

If no fragment exists, the base template is used alone (backward-compatible).

### File naming convention

```
skills/step_instructions/
├── cat1_step2_rules.md                            ← base
├── cat1_step2_rules__what_would_it_say.md         ← fragment
├── cat1_step2_rules__storytelling_chain.md
├── cat1_step2_rules__riddle_game.md                ← NEW style
├── cat1_step3_round.md                             ← base
├── cat1_step3_round__what_would_it_say.md
├── cat1_step3_round__storytelling_chain.md
├── cat1_step3_round__riddle_game.md                ← NEW style
├── cat5_step3_collect.md                           ← base
├── cat5_step3_collect__comparison_chart.md
├── cat5_step3_collect__naming_story.md             ← NEW style
├── cat5_step4_synthesis.md                         ← base
├── cat5_step4_synthesis__comparison_chart.md
├── cat5_step4_synthesis__naming_story.md            ← NEW style
└── ...existing files unchanged...
```

Double-underscore `__` separates base name from style key.

### Which steps get fragments

| Category | Step | Fragment key source | Why |
|----------|------|-------------------|-----|
| Cat 1 | Step 2 (Rules+Demo) | `game_mechanic` | Demo structure differs fundamentally per mechanic |
| Cat 1 | Step 3 (Round) | `game_mechanic` | Question type, response handling, "correct" criteria differ |
| Cat 5 | Step 3 (Collect) | `synthesis_type` | Per-find engagement differs (naming vs describing vs imagining) |
| Cat 5 | Step 4 (Synthesis) | `synthesis_type` | Capstone experience is fundamentally different per style |

Steps 1 (Hook), 4/5 (Celebrate), 5/6 (Closing) stay shared — variables handle variation.

### Styles to implement

**Cat 1 (3 fragments each for steps 2+3 = 6 fragment files):**
- `what_would_it_say` — AI sets scene, child voices entity (dog, dinosaur)
- `storytelling_chain` — AI starts story, child continues (cat)
- `riddle_game` — AI gives clues, child guesses (**NEW**, unassigned for now)

**Cat 5 (2 fragments each for steps 3+4 = 4 fragment files):**
- `comparison_chart` — Compare finds, discover patterns (ladybug)
- `naming_story` — Name finds as characters, create story (**NEW**, assign to dandelion)

**Total: 10 new fragment files + loader change.**

### Entity reassignment

- `fluffy_expedition_dandelion`: change `synthesis_type` from `"comparison_chart"` to `"naming_story"` in entity registry
- All other entities unchanged

## Implementation Steps

### Task 1: Modify the step instruction loader

**File:** `backend/agents/script_agent.py`

In `_load_step_instructions()` (~line 135), after loading the base template:

1. Determine `style_key`:
   - If category is `category_1`: use `creative_slots.game_mechanic`
   - If category is `category_5`: use `creative_slots.synthesis_type`
2. Build fragment filename: `base_name__style_key.md`
3. Check if fragment file exists
4. If yes, append its content (with variable replacement) after the base

Only apply fragment lookup for steps that support it (steps 2+3 for Cat1, steps 3+4 for Cat5). Add a set of fragmentable step prefixes to control this.

~15 lines of code change.

### Task 2: Extract existing style guidance from base templates into fragments

Review current base templates and move any mechanic-specific guidance into the appropriate fragment files. The base should retain only shared structure.

**Cat 1 Step 2 (`cat1_step2_rules.md`):**
- Base keeps: explain rules in ≤2 sentences, run demo, end with invitation, re-invitation after decline
- Move game mechanic reference section into fragments

**Cat 1 Step 3 (`cat1_step3_round.md`):**
- Base keeps: round number framing, one-step-per-turn rule, escalation mention, avoid list, silence handling
- Move to fragments: how to present scenarios, what counts as good answer, scaffolding strategies

**Cat 5 Step 3 (`cat5_step3_collect.md`):**
- Base keeps: collection count tracking, correct/wrong/stuck branching, stay_on_step rules, tone guidelines
- Move to fragments: per-find engagement style (naming_prompt usage vs character naming)

**Cat 5 Step 4 (`cat5_step4_synthesis.md`):**
- Base keeps: child response handling, stay_on_step rules, silence/off-topic handling
- Move to fragments: synthesis question framing, celebration framing

### Task 3: Write new style fragments

**Cat 1 `riddle_game` fragments (2 files):**
- `cat1_step2_rules__riddle_game.md`: Demo = "I'll give you 3 clues, you guess! Clue 1: it's round. Clue 2: it bounces. It's a... BALL!"
- `cat1_step3_round__riddle_game.md`: Present clues one at a time, "correct" = any reasonable guess, scaffold = offer 2 choices

**Cat 5 `naming_story` fragments (2 files):**
- `cat5_step3_collect__naming_story.md`: After correct pick, ask child to give the find a character name
- `cat5_step4_synthesis__naming_story.md`: Ask child to create a story with their named characters

### Task 4: Update entity registry

**File:** `backend/entity_registry.py`

Change `fluffy_expedition_dandelion` creative slots:
- `synthesis_type`: `"comparison_chart"` → `"naming_story"`
- Optionally update `naming_prompt` to better fit the naming_story style

### Task 5: Update creative_slots schema if needed

**File:** `backend/schemas/creative_slots.py`

Verify that `"naming_story"` is already in the `synthesis_type` Literal. It is — the enum already includes `"naming_story"`. No change needed.

Similarly, `"riddle_game"` is already in `game_mechanic` Literal. No change needed.

### Task 6: Update tests

**File:** `tests/test_entity_registry.py`

- Update test for dandelion's expected synthesis_type
- Add test that fragment files exist for all styles referenced by entities in the registry

### Task 7: Integration test

- Run the server with the dandelion entity (naming_story style)
- Verify the LLM receives the naming_story fragment in its prompt
- Run the ladybug entity (comparison_chart style) to verify it still works
- Run a Cat 1 entity to verify fragments load correctly

## Files to modify

| File | Change |
|------|--------|
| `backend/agents/script_agent.py` | Add fragment loading logic to `_load_step_instructions()` |
| `backend/entity_registry.py` | Change dandelion `synthesis_type` to `"naming_story"` |
| `backend/skills/step_instructions/cat1_step2_rules.md` | Extract mechanic-specific guidance to base-only |
| `backend/skills/step_instructions/cat1_step3_round.md` | Extract mechanic-specific guidance to base-only |
| `backend/skills/step_instructions/cat5_step3_collect.md` | Extract per-find engagement to base-only |
| `backend/skills/step_instructions/cat5_step4_synthesis.md` | Extract synthesis guidance to base-only |
| `tests/test_entity_registry.py` | Update dandelion test, add fragment existence test |

## New files (10 fragment files)

| File | Style |
|------|-------|
| `cat1_step2_rules__what_would_it_say.md` | Extracted from current guidance |
| `cat1_step2_rules__storytelling_chain.md` | Extracted from current guidance |
| `cat1_step2_rules__riddle_game.md` | New |
| `cat1_step3_round__what_would_it_say.md` | Extracted from current guidance |
| `cat1_step3_round__storytelling_chain.md` | Extracted from current guidance |
| `cat1_step3_round__riddle_game.md` | New |
| `cat5_step3_collect__comparison_chart.md` | Extracted from current guidance |
| `cat5_step3_collect__naming_story.md` | New |
| `cat5_step4_synthesis__comparison_chart.md` | Extracted from current guidance |
| `cat5_step4_synthesis__naming_story.md` | New |

## Verification

1. `cd backend && uv run ruff check . && uv run ruff format --check .` — lint clean
2. `uv run pytest ../tests/ -v` — all tests pass
3. Start server, test dandelion activity — verify naming_story fragment appears in LLM prompt (check logs)
4. Test ladybug activity — verify comparison_chart fragment loads correctly
5. Test a Cat 1 activity — verify game_mechanic fragments load
6. Run `scripts/test_all_activities.py` — all 5 activities complete without errors
