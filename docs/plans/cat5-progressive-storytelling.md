# Cat5 Progressive Storytelling & Varied Detail Questions

## Problem

Two UX issues with the current 2-phase collection loop:

### 1. Repetitive detail question
The AI asks the same `detail_question_template` verbatim every round (e.g., "What does this fluffy thing remind you of?" three times in a row). This feels mechanical and boring.

### 2. Deferred story creation feels daunting
The current flow dumps all creative work into the final synthesis step:

```
Find → detail → Find → detail → Find → detail → Synthesis: "Make up a whole story!"
```

By the time synthesis arrives, the child has to create an entire story from scratch using 3 named characters they may have half-forgotten. This is cognitively heavy, especially for T0 (ages 2–4).

## Solution

### 1. Varied detail questions

Update the Phase A step instructions to tell the AI to **vary** the detail question based on round number and what came before. The `detail_question_template` becomes a starting point, not a script.

**naming_story variation pattern:**
- Round 1: `{detail_question_template}` as-is (e.g., "What does it remind you of?")
- Round 2: Compare to previous find ("This one feels different from Cloud Puff — what does THIS one remind you of?")
- Round 3: Playful twist ("If this fluffy thing could talk, what would its name be?")

**comparison_chart variation pattern:**
- Round 1: `{detail_question_template}` as-is (e.g., "How are the dots different?")
- Round 2: Explicit comparison ("Are these dots bigger or smaller than the ones on your first find?")
- Round 3: Superlative ("Is this the spottiest one yet, or the sneakiest?")

No schema changes needed — just prompt instruction updates.

### 2. Progressive narrative building

Instead of saving all story/comparison work for synthesis, the AI builds incrementally during each Phase B response:

**naming_story progression:**
```
R1 Phase B: "Cloud Puff! What a perfect name for your first fluffy friend!"
R2 Phase B: "Pillow Petal! Now Cloud Puff has a friend to play with!"
R3 Phase B: "Tickle Worm! The three fluffy friends are all together now — I wonder what they'll do!"
Synthesis:  "Cloud Puff, Pillow Petal, and Tickle Worm are all here. What happens when they meet?"
            (just the ending — not the whole story from scratch)
```

**comparison_chart progression:**
```
R1 Phase B: "Big round dots — great eyes! That's our first pattern."
R2 Phase B: "Tiny speckles! So different from the big dots on your first find."
R3 Phase B: "Perfect circles! So we have big splotches, tiny speckles, and perfect circles — three different kinds of dots!"
Synthesis:  "Which one has the biggest dots? Can you put them in order?"
            (just the final ranking — the observations are already laid out)
```

**sorting_game progression:**
```
R1 Phase B: "A clang sound! That's our first instrument."
R2 Phase B: "A tap-tap! Higher than the clang. Our sound collection is growing!"
R3 Phase B: "A whoosh! Three different sounds — clang, tap, and whoosh!"
Synthesis:  "Which sound was the highest? Can you put them in order?"
```

The key insight: **each Phase B response references ALL previous finds**, not just the current one. This creates a running narrative thread that makes synthesis feel like a natural conclusion rather than a cold start.

## Implementation Plan

### Changes Required

All changes are prompt-only — no backend logic, schema, or frontend changes needed.

#### 1. `cat5_step3_collect.md` — Add round-aware detail question variation

In the Phase A section (correct photo), replace the fixed detail question instruction with a round-aware variation rule:

```
### Detail question variation (NON-NEGOTIABLE — do NOT ask the same question every round):
- Round 1: Use `{detail_question_template}` naturally
- Round 2+: Vary the question — compare to previous finds, use a different angle, or add a playful twist
- NEVER repeat the exact same question from a previous round
- Reference previous finds by name when asking the question
```

#### 2. `cat5_step3_collect__naming_story.md` — Progressive character introduction

Update Phase B instructions to build a running cast:

```
#### Phase B — Progressive narrative:
- Round 1: Celebrate the name. "Cloud Puff! Your first fluffy friend!"
- Round 2: Connect to previous character. "Pillow Petal! Now Cloud Puff has a friend!"
- Round 3+: Build the ensemble. "Tickle Worm joins the group! All your fluffy friends are together!"
- Each response should reference ALL named characters so far, building anticipation for what they'll do together.
```

#### 3. `cat5_step3_collect__comparison_chart.md` — Progressive observation building

Update Phase B instructions to maintain a running comparison:

```
#### Phase B — Progressive comparison:
- Round 1: Anchor the first observation. "Big round dots — that's our first pattern!"
- Round 2: Compare explicitly. "Tiny speckles! So different from the big dots on your first find."
- Round 3+: Summarize the collection. "Perfect circles! So we have big splotches, tiny speckles, and perfect circles."
- Each response should recap the growing comparison, making the final synthesis feel like a natural next step.
```

#### 4. `cat5_step4_synthesis.md` — Lighten the synthesis ask

Update to acknowledge that the creative groundwork is already laid:

```
### The story/comparison is already started during collection.
- For naming_story: Characters are named AND introduced as a group. Synthesis = "What happens when they meet?" (just the adventure, not the setup)
- For comparison_chart: Observations are captured AND compared. Synthesis = "Can you put them in order?" (just the ranking, not the analysis)
- Keep the synthesis invitation to ONE simple question — the child already did the hard work.
```

#### 5. `cat5_step4_synthesis__naming_story.md` — Lighter story prompt

Replace "make up a story" with "finish the story":

```
The characters are already introduced as a group during collection.
- Invite the child to tell what happens NEXT: "Cloud Puff, Pillow Petal, and Tickle Worm are all together — what do they do?"
- NOT: "Would you like to make up a story?" (too open-ended, too daunting)
```

#### 6. `cat5_step4_synthesis__comparison_chart.md` — Lighter comparison prompt

Replace "compare your finds" with "put them in order":

```
The observations are already laid out during collection.
- Invite the child to rank: "Which one had the biggest dots? Can you sort them?"
- NOT: "Tell me how your finds are alike or different" (they already did this)
```

### Files to Modify

1. `backend/skills/step_instructions/cat5_step3_collect.md` — varied detail question rule
2. `backend/skills/step_instructions/cat5_step3_collect__naming_story.md` — progressive character building
3. `backend/skills/step_instructions/cat5_step3_collect__comparison_chart.md` — progressive observation building
4. `backend/skills/step_instructions/cat5_step4_synthesis.md` — lighter synthesis framing
5. `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — "finish the story" not "make a story"
6. `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md` — "rank them" not "compare them"

### What Does NOT Change

- No backend logic changes (turn_handler, state_machine, server)
- No schema changes (session_state, creative_slots)
- No frontend changes
- No game definition changes (the `detail_question_template` field stays as a starting point)
- Cat1 flows unaffected

### Verification

1. `cd backend && uv run ruff check . && uv run ruff format --check .` — no Python changes, but verify nothing broke
2. `uv run pytest tests/ -q` — all tests pass (prompt-only changes shouldn't break anything)
3. Manual test: Run `fluffy_expedition_dandelion` — verify:
   - Detail questions vary across rounds
   - Phase B responses reference previous characters by name
   - Synthesis asks "what happens next?" not "make up a story"
4. Manual test: Run `polka_dot_patrol` — verify:
   - Detail questions vary (bigger/smaller/spottiest)
   - Phase B responses build a running comparison
   - Synthesis asks "can you sort them?" not "compare them"
5. E2E: `python scripts/test_all_activities.py` — all 5 activities pass with no issues
