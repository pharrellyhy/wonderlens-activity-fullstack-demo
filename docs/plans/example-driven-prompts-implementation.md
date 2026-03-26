# Example-Driven Prompt Refactor — Implementation Plan

## Context

The current prompt system uses 28 step instruction files with 889 total lines and 65+ rules in the heaviest file (`cat5_step3_collect.md`). More rules means worse per-rule compliance — we've been in a cycle of: AI violates rule → add more rules → prompt gets longer → AI violates different rule.

LLMs are pattern-matching engines, not rule-followers. Examples are concrete and composable; rules are abstract and competing.

**Goal:** Replace rule-heavy step instructions with a **hybrid** format: minimal structural rules + few-shot example transcripts per tier. The LLM imitates tone, length, and scaffolding from examples. Code continues to handle structure and hard constraints.

**Prototype:** fluffy_expedition_dandelion (Cat5, T0) — our biggest quality gap.

**Reference:** See `docs/plans/example-driven-prompts.md` for the original problem analysis and motivation.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Output format rules (JSON schema, emotion tags, widgets) | Keep intact in `script_turn.md` |
| Structural rules (phase logic, branching, progress) | Keep as ~5 rules per step |
| Conversational guidance (tone, scaffolding, phrasing) | Replace with examples |
| Variant overlay files | Convert to example-driven too |
| Post-processing validation | Keep as-is, add retry-rate logging |
| Script agent code changes | None — format change is transparent to template system |

## New Step Instruction File Format

```markdown
## Current Step: {step_name}

### GOAL
{One sentence — the LLM's north star for this step.}

### CONTEXT
{Template variables rendered by the engine — collected_count, remaining_count, etc.}

### STRUCTURAL RULES
{3-7 rules max. Only: phase/branching logic, state field instructions (stay_on_step),
progress constraints, things the LLM must NEVER do. No tone/style rules.}

### EXAMPLES

#### T0 (ages 2-4)

**{scenario label}:**
Child: "{input}"
AI: "{response with emotion tag}"

#### T1 (ages 4-6)
...

#### T2 (ages 6-8)
...
```

**What moves from rules → examples:**
- Tone guidance → demonstrated by example tone
- Scaffolding patterns (model-first) → shown in T0 examples
- Sentence length → demonstrated by example length
- Progressive narrative threading → shown across 1st/2nd/3rd find examples
- Question variation → shown by varied example questions
- Invitational language → demonstrated in every example

**What stays as structural rules:**
- Phase A/B branching logic
- `stay_on_step: true` when...
- `remaining_count` constraints (NEVER say "mission complete" when > 0)
- Never suggest specific items
- Original entity doesn't count

### Variant Overlay Format

```markdown
### Style: {variant_name}

### VARIANT RULES
{1-3 variant-specific structural rules}

### VARIANT EXAMPLES
#### T0
...
```

Base + variant concatenation (`text += "\n\n" + variant`) still works unchanged.

## System Prompt Changes

**File:** `backend/skills/script_turn.md`

**Sections unchanged:** 1 (Role & Persona), 3 (Step Instructions placeholder), 4 (Creative Slots), 5 (Vision Context), 6 (Output Rules), 7 (Conversation State).

**Section 2 (Tier Rules) — simplify** from ~14 lines of constraints to compact summary:
```
Tier: {tier} ({label}, ages {ages})
Sentences: max {max_sentences}, ~{words_per_sentence} words each. Style: {tone}.
T0: Always model your idea first, then offer a choice. Never ask open questions alone.
T1: Light scaffolding. Can ask guided questions.
T2: Can invite child to try first. Scaffold only if stuck.
```

Remove the invitational/forbidden language rule block (moves into examples).

## Retry-Rate Logging

**File:** `backend/turn_handler.py` in `_generate_with_retry()` (line 434)

Add structured logging after line 472 (success) and line 487 (exhausted):
```python
logger.info(
    "script_generation",
    extra={"step": state.current_step, "attempts": attempt + 1,
           "validation_passed": True, "tier": state.tier}
)
```

Add module-level stats dict for per-step retry rates:
```python
_retry_stats: dict[str, dict[str, int]] = {}  # step → {total, first_pass, retried, exhausted}
```

Log summary at session end for before/after comparison.

## Implementation Steps

### Step 1: Add retry-rate logging (baseline)
- `backend/turn_handler.py` — add logging in `_generate_with_retry()`

### Step 2: Convert Cat5 step instruction files (in order)
1. `backend/skills/step_instructions/cat5_step1_hook.md` (30 → ~20 lines)
   - GOAL + 2 structural rules + 6 examples (2 per tier)
2. `backend/skills/step_instructions/cat5_step2_mission.md` (68 → ~40 lines)
   - GOAL + 5 structural rules + 9 examples (accept/decline/silence × tiers)
3. `backend/skills/step_instructions/cat5_step3_collect.md` (125 → ~80 lines)
   - GOAL + 7 structural rules + ~30 examples (correct/wrong/silence × phase A/B × tiers)
   - **Main test.** If this works, everything else will be easier.
4. `backend/skills/step_instructions/cat5_step3_collect__naming_story.md` (39 → ~25 lines)
   - VARIANT RULES (2) + variant examples
5. `backend/skills/step_instructions/cat5_step4_synthesis.md` (35 → ~25 lines)
   - GOAL + 3 structural rules + 9 examples (T0/T1/T2 × ideal/stuck)
6. `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` (96 → ~50 lines)
   - VARIANT RULES (3) + variant examples
7. `backend/skills/step_instructions/cat5_step5_celebrate.md` (23 → ~15 lines)
8. `backend/skills/step_instructions/cat5_step6_closing.md` (23 → ~15 lines)
9. `backend/skills/step_instructions/early_exit.md` (16 → ~12 lines)

### Step 3: Simplify system prompt tier section
- `backend/skills/script_turn.md` — rewrite SECTION 2 to compact format
- `backend/agents/script_agent.py` — slim down `_load_tier_constraints()` (lines 63-99)

### Step 4: Create test scenario
- `backend/scenarios/fluffy_expedition_dandelion.yaml` — full Cat5 T0 happy path + edge cases

### Step 5: Measure
- Run test scenario 5+ times with new prompts
- Compare retry rates before vs after
- Manual review of response quality
- Measure prompt token count reduction

## No Code Changes Required (except logging)

The script agent's template system is format-agnostic:
- `_load_step_instructions()` — loads base file + appends variant. Works with any content.
- Template variable substitution (`str.replace()`) — works on examples same as rules.
- `_build_instruction_overlay()` — appends recipe goals/constraints after step instructions. Still works.
- `_build_system_prompt()` — assembles all sections. No changes needed.

Post-processing validation in `turn_handler.py` (`_validate_response`, `_ends_with_open_question`, `_has_model_phrase`) — completely unchanged.

## Example: cat5_step3_collect.md (Before → After)

**Before (125 lines):** 65 rules covering phase logic, correct/wrong/silence branches, detail question variation, progressive narrative, tone guidelines, avoid lists, screen widgets.

**After (~80 lines):**
```markdown
## Current Step: Photo Collection Round {round_number} of {total_rounds}

### GOAL
Celebrate each find, ask a varied detail question (model first for T0), and build the character cast progressively.

### CONTEXT
Collected: {collected_count} of {total_rounds} | Still needed: {remaining_count}
Phase: {collection_phase} | Item: [from child message]
Previous characters: {collected_names} | Previous details: {collected_details}

### STRUCTURAL RULES
1. Two phases per round: Phase A (photo selection) → Phase B (detail response).
2. If child selected WRONG photo: set `stay_on_step: true`. Acknowledge warmly, redirect.
3. If child selected CORRECT photo: celebrate with progress count, ask a detail question,
   set `stay_on_step: true` (child must answer before advancing).
4. If remaining_count > 0: mission NOT done. FORBIDDEN: "final", "last", "all done", "complete".
5. If remaining_count = 0: this is the last item. Use sfx: mission_complete_fanfare. No question.
6. The original {entity_name} does NOT count as a collected item.
7. NEVER suggest specific items. Use {observation_angle} and {collection_criterion} only.

### EXAMPLES

#### T0 (ages 2-4)

**Phase A — Correct photo (1st find):**
AI: "[excited] Fuzzy moss! 1 out of 3! I think it looks like a cloud. Cloud or pillow?"

**Phase A — Correct photo (2nd find):**
AI: "[excited] Soft petal! 2 out of 3! Cloud Puff has a friend! I think it's silky. Silky Star or Petal Pillow?"

**Phase A — Wrong photo:**
AI: "[gentle] Ooh, a pinecone! But it feels pokey, not soft. Something fluffy might be near you."

**Phase A — Silence:**
AI: "[gentle] I wonder if something fluffy is hiding close by? Would you like to peek around?"

**Phase B — Ideal response (1st find):**
Child: "a cloud!"
AI: "[celebrating] Cloud Puff! Your first fluffy friend! Would you like to find another soft friend?"

**Phase B — Ideal response (2nd find):**
Child: "a pillow!"
AI: "[celebrating] Pillow Petal! Cloud Puff and Pillow Petal together! One more to find?"

**Phase B — Ideal response (3rd/final find):**
Child: "tickles!"
AI: "[celebrating] Tickle Worm! Cloud Puff, Pillow Petal, and Tickle Worm — all your fluffy friends together!"

**Phase B — Off-topic:**
Child: "it's green!"
AI: "[gentle] Green and fuzzy! I think it looks like a little Green Cloud. Green Cloud or Fuzzy Bean?"

**Phase B — Silence:**
AI: "[gentle] I think this one looks like a marshmallow! Marshmallow Munch or Cloud Pillow — which one?"

#### T1 (ages 4-6)

**Phase A — Correct photo (1st find):**
AI: "[excited] Fuzzy moss — 1 out of 3! It looks so soft and squishy. What does it remind you of?"

**Phase A — Correct photo (2nd find):**
AI: "[excited] A soft petal! 2 out of 3! This one feels different from Cloud Puff — what do you notice?"

**Phase A — Wrong photo:**
AI: "[gentle] That rock is cool, but does it feel soft? Maybe there's something fluffy hiding nearby."

**Phase B — Ideal response:**
Child: "it's like a tiny blanket"
AI: "[celebrating] A tiny blanket — Blanket Bud! Cloud Puff and Blanket Bud make quite the cozy pair!"

**Phase B — Silence:**
AI: "[gentle] Hmm, this one is interesting. What do you think it feels like compared to Cloud Puff?"

#### T2 (ages 6-8)

**Phase A — Correct photo:**
AI: "[excited] Amazing find — 1 out of 3! What do you notice about how soft this one is compared to the dandelion?"

**Phase B — Ideal response:**
Child: "it's softer but not as fluffy"
AI: "[celebrating] Good observation! So it's a different kind of soft. What would you name this character?"
```

## Verification

1. **Baseline:** Run `uv run pytest` to confirm all existing tests pass before changes
2. **Retry logging:** After adding logging, run a manual session and check logs show retry stats
3. **Prompt conversion:** After converting each step file:
   - Run `uv run pytest` — tests should still pass
   - Run a manual fluffy_expedition_dandelion session in the browser
   - Check responses match the example tone/style
   - Verify post-processing validation still triggers correctly for T0
4. **Token count:** Compare prompt token counts before/after (log in script_agent)
5. **Quality comparison:** Run test scenario 5+ times, compare:
   - Retry rate (from new logging)
   - Response naturalness (manual review)
   - T0 scaffolding compliance (model-first pattern)
   - Progressive naming thread consistency

## Future Phases (out of scope for prototype)

- **Phase 3:** Roll out to Cat1 files (5 base + 10 variant files)
- **Phase 4:** Add richer T1/T2 examples, test across all tiers
