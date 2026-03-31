# Prompt Quality Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 recurring Cat5 quality issues (item suggestions, directive language, premature completion) by cleaning game spec examples, strengthening step instructions, and expanding validation regex.

**Architecture:** Three layers — clean contaminated game spec examples that teach violations, add DO/DON'T tables to step instructions, expand validation regex to catch missed variants. Verify with T0 eval run.

**Tech Stack:** Markdown prompt edits, Python regex (turn_handler.py), pytest

**Spec:** `docs/superpowers/specs/2026-03-30-prompt-quality-hardening-design.md`

---

## File Map

| File | Change |
|------|--------|
| `backend/games/polka_dot_patrol.md` | Replace contaminated examples (lines 237-239) |
| `backend/games/fluffy_expedition_dandelion.md` | Replace contaminated examples (lines 27, 305) |
| `backend/skills/step_instructions/cat5_step3_collect.md` | Add DO/DON'T reference table after line 20 |
| `backend/skills/step_instructions/cat5_step2_mission.md` | Add positive invitational example after line 14 |
| `backend/turn_handler.py` | Expand `_ITEM_SUGGESTION_RE` nouns, add `_DIRECTIVE_RE`, add validation check |
| `tests/test_turn_handler.py` | Add tests for directive detection |

---

### Task 1: Clean game spec examples

**Files:**
- Modify: `backend/games/polka_dot_patrol.md:237-239`
- Modify: `backend/games/fluffy_expedition_dandelion.md:27,305`

- [ ] **Step 1: Fix polka_dot_patrol.md lines 237-239**

Replace the 3 AI follow-up lines that contain directive language + item suggestions:

Old (lines 237-239):
```
1. (cheering) "Officer on the case! Keep your eyes peeled for dots and spots. Snap a photo when you find one!"
2. (helpful, warm) "A patrol means you go looking, like a detective! Try looking at flowers up close, or at the ground near your feet. Spots love to hide!"
3. (wait 2s) (encouraging) "Try peeking at things up close. Flowers, rocks, leaves — dots could be anywhere! Would you like to start with something nearby?"
```

New:
```
1. (cheering) "Officer on the case! Dots and spots are all around — would you like to start looking?"
2. (helpful, warm) "A patrol means you look really carefully, like a detective! Would you like to see if something dotty is hiding nearby?"
3. (wait 2s) (encouraging) "I bet there's something with dots closer than you think! Would you like to peek around?"
```

- [ ] **Step 2: Fix fluffy_expedition_dandelion.md line 27**

Old:
```
  stuck_hint: "Try touching things around you — look for anything soft or fuzzy"
```

New:
```
  stuck_hint: "Would you like to feel things nearby? Something soft might be waiting for you!"
```

- [ ] **Step 3: Fix fluffy_expedition_dandelion.md line 305**

Old:
```
**STUCK BRANCH:** "Try touching things around you — look for anything soft or fuzzy! Maybe some grass? Or a flower petal? Would you like to feel that?"
```

New:
```
**STUCK BRANCH:** "Would you like to reach out and touch something nearby? I wonder if it feels soft or fuzzy!"
```

- [ ] **Step 4: Audit remaining game specs for similar patterns**

Run: `cd backend && grep -rn "Try \|Go find\|Look for\|grab a\|search for" games/*.md`

Fix any additional violations found.

- [ ] **Step 5: Commit**

```bash
git add backend/games/polka_dot_patrol.md backend/games/fluffy_expedition_dandelion.md
git commit -m "fix(prompts): remove directive language and item suggestions from game specs"
```

---

### Task 2: Strengthen step instructions

**Files:**
- Modify: `backend/skills/step_instructions/cat5_step3_collect.md:20`
- Modify: `backend/skills/step_instructions/cat5_step2_mission.md:14`

- [ ] **Step 1: Add DO/DON'T table to cat5_step3_collect.md**

After line 20 (after "The child notices repetition instantly."), insert:

```markdown

### Quick Reference: What TO Say vs What NOT to Say

| Rule | DO say | DON'T say |
|------|--------|-----------|
| No item suggestions | "Something {observation_angle} might be nearby" | "Find a fuzzy blanket" / "Look at that rock" |
| No directive language | "Would you like to keep looking?" / "I wonder what else is {observation_angle}..." | "Go find the next one!" / "Try peeking!" / "Look for something round" |
| No premature completion | "{remaining_count} more to discover!" / "Another one!" | "Almost done!" / "Just one more!" / "Last one!" (when remaining > 1) |
| Invitational tone | "I wonder if something {collection_criterion} is hiding nearby..." | "Now let's find another one" / "Scan the floor" |
```

- [ ] **Step 2: Add positive example to cat5_step2_mission.md**

After line 14 (after the screen widget rule), insert:

```markdown
6. **Use invitational language throughout.** Frame discovery as the child's choice: "Would you like to see if something {observation_angle} is hiding nearby?" Never command: "Go find 3 dotty things!"
```

- [ ] **Step 3: Commit**

```bash
git add backend/skills/step_instructions/cat5_step3_collect.md backend/skills/step_instructions/cat5_step2_mission.md
git commit -m "fix(prompts): add DO/DON'T reference tables to collection step instructions"
```

---

### Task 3: Expand validation regex

**Files:**
- Modify: `backend/turn_handler.py:452-460,436-441`
- Test: `tests/test_turn_handler.py`

- [ ] **Step 1: Write tests for expanded item suggestion regex**

Add to `tests/test_turn_handler.py` (after existing tests, before the helper tests section):

```python
from turn_handler import _DIRECTIVE_RE, _ITEM_SUGGESTION_RE


def test_item_suggestion_catches_berry() -> None:
    assert _ITEM_SUGGESTION_RE.search("Try finding a berry or a button nearby!")


def test_item_suggestion_catches_petal() -> None:
    assert _ITEM_SUGGESTION_RE.search("Look for a soft petal on the ground")


def test_item_suggestion_catches_grass() -> None:
    assert _ITEM_SUGGESTION_RE.search("Feel the grass — is it soft?")


def test_item_suggestion_allows_observation_angle() -> None:
    assert not _ITEM_SUGGESTION_RE.search("Something soft might be nearby")


def test_directive_catches_try_peeking() -> None:
    assert _DIRECTIVE_RE.search("Try peeking at something round!")


def test_directive_catches_scan_the() -> None:
    assert _DIRECTIVE_RE.search("Scan the floor for dots!")


def test_directive_catches_go_find() -> None:
    assert _DIRECTIVE_RE.search("Go find the next one!")


def test_directive_catches_look_for() -> None:
    assert _DIRECTIVE_RE.search("Look for something soft!")


def test_directive_allows_invitational() -> None:
    assert not _DIRECTIVE_RE.search("Would you like to keep looking?")


def test_directive_allows_wonder() -> None:
    assert not _DIRECTIVE_RE.search("I wonder what else is soft nearby...")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -k "directive or berry or petal or grass" -v`
Expected: FAIL — `_DIRECTIVE_RE` doesn't exist yet, "berry"/"petal"/"grass" not in regex

- [ ] **Step 3: Expand `_ITEM_SUGGESTION_RE` noun list**

In `backend/turn_handler.py`, replace lines 456-459:

Old:
```python
    r"\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
    r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
    r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble"
    r"|rug|carpet|towel|cloth|cushion|teddy|doll|stuffed)\b"
```

New:
```python
    r"\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
    r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
    r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble"
    r"|rug|carpet|towel|cloth|cushion|teddy|doll|stuffed|berry|berries|petal|petals"
    r"|grass|furniture|acorn|pinecone|mushroom|feather|twig|bark|seed|moss)\b"
```

- [ ] **Step 4: Add `_DIRECTIVE_RE` after `_ITEM_SUGGESTION_RE`**

After line 460, insert:

```python

# Directive language patterns that command the child to take action.
# Invitational alternatives ("Would you like to...?", "I wonder...") are OK.
_DIRECTIVE_RE = re.compile(
    r"(?i)\b(?:try\s+\w+ing|scan\s+the|check\s+the|go\s+find|go\s+look"
    r"|look\s+for|search\s+for|now\s+let'?s|let'?s\s+go)\b"
)
```

- [ ] **Step 5: Add directive validation check in `_validate_response`**

In `backend/turn_handler.py`, after the item suggestion check (after line 441 `return True, ""`), insert a directive check. Replace lines 436-443:

Old:
```python
    # 6. Collection steps: no specific item suggestions
    if step.startswith("STEP_3_COLLECT_") and _ITEM_SUGGESTION_RE.search(dialogue):
        return False, (
            "CORRECTION: Do NOT name specific objects to find (blanket, toy, pillow, etc.). "
            "You cannot see the child's environment. Say 'something soft' not 'a fuzzy blanket'."
        )

    return True, ""
```

New:
```python
    # 6. Collection steps: no specific item suggestions
    if step.startswith("STEP_3_COLLECT_") and _ITEM_SUGGESTION_RE.search(dialogue):
        return False, (
            "CORRECTION: Do NOT name specific objects to find (blanket, toy, pillow, etc.). "
            "You cannot see the child's environment. Say 'something soft' not 'a fuzzy blanket'."
        )

    # 7. Cat5 steps: no directive language
    if state.template_type == "cat5" and _DIRECTIVE_RE.search(dialogue):
        return False, (
            "CORRECTION: Do NOT use directive language ('Go find!', 'Look for!', 'Try peeking!'). "
            "Use invitational phrasing: 'Would you like to...?' or 'I wonder if...' instead."
        )

    return True, ""
```

- [ ] **Step 6: Update the import in test file**

Add `_DIRECTIVE_RE` and `_ITEM_SUGGESTION_RE` to the imports at the top of `tests/test_turn_handler.py`:

```python
from turn_handler import (
    TurnInput,
    _DIRECTIVE_RE,
    _ITEM_SUGGESTION_RE,
    _generate_with_retry,
    _maybe_record_generated_name,
    _record_collection_detail,
    resolve_turn,
)
```

- [ ] **Step 7: Run tests**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All PASS

- [ ] **Step 8: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

- [ ] **Step 9: Commit**

```bash
git add backend/turn_handler.py tests/test_turn_handler.py
git commit -m "fix(validation): expand item suggestion regex, add directive language detection"
```

---

### Task 4: Verify with T0 eval

- [ ] **Step 1: Run full project tests**

Run: `cd backend && uv run pytest ../tests/ -v`
Expected: All pass, no regressions

- [ ] **Step 2: Run T0 eval**

Run: `cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo && uv run python scripts/run_eval.py --tier T0 --sessions 2`

Expected: Fewer critical failures than the baseline run. Target: 0 critical failures for "suggested specific items" and "directive language".

- [ ] **Step 3: Review results**

Read: `eval_results/{latest}/report.md`

Compare with baseline: `eval_results/2026-03-30_03-42/report.md`

---

## Verification

1. `cd backend && uv run pytest ../tests/ -v` — all pass
2. `cd backend && uv run ruff check turn_handler.py` — clean
3. `uv run python scripts/run_eval.py --tier T0 --sessions 2` — critical failures reduced
4. `grep -rn "Try \|Go find\|Look for" backend/games/*.md` — no directive violations in game specs
