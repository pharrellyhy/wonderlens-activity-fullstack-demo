# Cat5 Prompt Quality Hardening — Design Spec

## Problem

Eval run (12 sessions, 2 activities, 3 tiers) found 3 recurring quality violations:

| Issue | Prevalence | Example |
|-------|-----------|---------|
| AI suggests specific real-world items | 10/12 (83%) | "Try peeking at something round like a berry or a button" |
| AI uses directive language | 7/12 (58%) | "Go find!", "Look for!", "Try peeking", "scan the floor" |
| AI uses premature completion language | 5/12 (42%) | "All done!", "mission complete" when items remain |

Rules against all 3 issues already exist in step instructions. The violations persist because:

1. **Game spec files contain contaminated examples** that teach the LLM to violate rules
2. **Validation regex is too narrow** — misses directive variants and item names
3. **Step instructions lack positive examples** — only say what NOT to do

## Root Causes

### Contaminated game spec examples

`backend/games/polka_dot_patrol.md` line 239:
> "Try peeking at things up close. Flowers, rocks, leaves — dots could be anywhere!"

This violates 2 rules: directive language ("Try peeking") + specific items ("Flowers, rocks, leaves").

`backend/games/fluffy_expedition_dandelion.md` line 27:
> stuck_hint: "Try touching things around you — look for anything soft or fuzzy"

Directive language ("Try touching", "look for").

`backend/games/fluffy_expedition_dandelion.md` line 305:
> "Try touching things around you — look for anything soft or fuzzy! Maybe some grass? Or a flower petal?"

Directive + specific items ("grass", "flower petal").

### Incomplete validation regex

`_ITEM_SUGGESTION_RE` in `turn_handler.py` is missing:
- "berry", "petal", "grass" (not in noun list)
- 40-char lookahead window too short for some violations

Directive language has no regex validation at all — only the LLM-based rules in prompts.

## Fix Design

### Layer 1: Clean game spec examples

**Files:** `backend/games/polka_dot_patrol.md`, `backend/games/fluffy_expedition_dandelion.md`

Replace contaminated lines with invitational language using only the observation angle:

| Before | After |
|--------|-------|
| "Try peeking at things up close. Flowers, rocks, leaves — dots could be anywhere!" | "Would you like to look around? Something with dots might be closer than you think!" |
| stuck_hint: "Try touching things around you — look for anything soft or fuzzy" | stuck_hint: "Would you like to feel things nearby? Something soft might be waiting for you!" |
| "Try touching things around you — look for anything soft or fuzzy! Maybe some grass? Or a flower petal?" | "Would you like to reach out and touch something nearby? I wonder if it feels soft or fuzzy!" |

Also audit all other game spec files for similar patterns.

### Layer 2: Strengthen step instructions

**File:** `backend/skills/step_instructions/cat5_step3_collect.md`

After the existing FORBIDDEN words rule (line 15), add a DO/DON'T reference table:

```
### Quick Reference: What TO Say vs What NOT to Say

| Rule | DO say | DON'T say |
|------|--------|-----------|
| No item suggestions | "Something {observation_angle} might be nearby" | "Find a fuzzy blanket" / "Look for a rock" |
| No directive language | "Would you like to keep looking?" | "Go find the next one!" / "Try peeking!" |
| No premature completion | "{remaining_count} more to discover!" | "Almost done!" / "Just one more!" |
| Invitational tone | "I wonder what else is {observation_angle}..." | "Now let's find another one" |
```

**File:** `backend/skills/step_instructions/cat5_step2_mission.md`

Reinforce with a positive example after the existing invitational rule.

### Layer 3: Expand validation regex

**File:** `backend/turn_handler.py`

1. Add to `_ITEM_SUGGESTION_RE` noun list: `berry|berries|petal|petals|grass|furniture|carpet`
2. Add directive language validation: new `_DIRECTIVE_RE` regex catching `try\s+\w+ing|scan\s+the|check\s+the|go\s+find|look\s+for|search\s+for`
3. Call `_DIRECTIVE_RE` in `_validate_response()` for Cat5 steps, return hint if matched

## Files to Modify

| File | Change |
|------|--------|
| `backend/games/polka_dot_patrol.md` | Replace line 239 directive example |
| `backend/games/fluffy_expedition_dandelion.md` | Replace lines 27, 305 directive examples |
| `backend/skills/step_instructions/cat5_step3_collect.md` | Add DO/DON'T reference table |
| `backend/skills/step_instructions/cat5_step2_mission.md` | Add positive invitational example |
| `backend/turn_handler.py` | Expand `_ITEM_SUGGESTION_RE`, add `_DIRECTIVE_RE` |
| `tests/test_turn_handler.py` | Add tests for new regex patterns |

## Verification

```bash
# Re-run eval for T0 only (2 entities x 1 tier x 2 sessions = 4 sessions)
uv run python scripts/run_eval.py --tier T0 --sessions 2
```

**Success criteria:**
- 0 critical failures for both dandelion T0 and ladybug T0
- Combined score >= 80% for both
- No regressions in existing tests (`uv run pytest tests/ -v`)
