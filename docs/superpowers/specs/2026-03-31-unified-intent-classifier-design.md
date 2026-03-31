# Unified Child Intent Classifier

**Date:** 2026-03-31
**Status:** Draft

## Summary

Replace the fragmented intent classification system (Script Agent `child_intent`, `_classify_story_response`, `_is_affirmative_or_continuation`) with a single LLM-based pre-classifier that runs before the Script Agent on every turn with child input.

## Motivation

Intent classification is currently split across three mechanisms:

1. **Script Agent `child_intent`** — the dialogue-generating LLM also classifies intent as a side output. Unreliable because the LLM is focused on generation, not classification. Only used during invitation steps.
2. **`_classify_story_response`** — a separate LLM call during synthesis (T1/T2 only). Good classification but limited to one step.
3. **`_is_affirmative_or_continuation`** — a hardcoded frozenset for T0 synthesis. Misses natural language variations.

This fragmentation causes:
- Wasted LLM calls (invitation acceptance generates two responses, throws one away)
- Misclassified intent ("yes" treated as story content in T0)
- Repetitive questions (collection steps don't know the child is just confirming)
- Inconsistent classification quality across steps and tiers

## Data Model

New schema in `backend/schemas/child_intent.py`:

```python
class ChildIntentClassification(BaseModel):
    intent: Literal["confirm", "decline", "substantive", "off_topic"]
    # Synthesis extension — only populated during STEP_4_SYNTHESIS
    story_quality: Literal["good", "weak"] | None = None
    is_related_to_collection: bool | None = None
```

### Intent Taxonomy

| Intent | Meaning | Maps from (old) |
|--------|---------|-----------------|
| `confirm` | Affirmative, continuation, or "you do it" — child agrees/wants to proceed | `accepted`, `ask_ai`, affirmative patterns |
| `decline` | Refusal — child says no | `declined`, `decline` |
| `substantive` | Real content — an answer, detail, or story attempt | `story_attempt`, any meaningful text |
| `off_topic` | Unrelated to the current activity | `off_topic`, `unrelated` |

### Synthesis Extension

When the current step is `STEP_4_SYNTHESIS` and intent is `substantive`, the classifier also returns:
- `story_quality`: "good" (2+ story elements, relates to characters) or "weak" (single sentence, no progression)
- `is_related_to_collection`: whether the response references collected characters

## Classifier Function

New `_classify_child_intent(state, child_text)` in `turn_handler.py`:

- Runs once per turn, before the Script Agent, on any turn with non-empty child text
- Skips for silent turns and auto-advance turns (no child input)
- Uses the same LLM backend as the existing classifier (Ali/Qwen via OpenAI-compatible API)
- Prompt includes current step and context (collected characters, activity type) for relevance judgment
- For synthesis turns: prompt adds story quality evaluation instructions
- ~50 token response for non-synthesis, ~100 tokens for synthesis
- On LLM failure: falls back to `substantive` (safe default)

### Prompt Structure

**Base prompt (all steps):**
```
The child is playing a {activity_type} game. Current step: {step_description}.
The child said: "{child_text}"

Classify the child's intent:
- "confirm": agreeing, affirming, wanting to continue, asking the AI to proceed
  ("yes", "sure", "ok", "what's next", "go ahead", "tell me", "sounds fun", "yay!")
- "decline": refusing or saying no ("no", "I don't want to", "nah")
- "substantive": providing real content — an answer, description, detail, or story
- "off_topic": unrelated to the current activity

Output JSON: {"intent": "..."}
```

**Synthesis extension (appended when step is STEP_4_SYNTHESIS):**
```
If intent is "substantive", also evaluate the story:
- story_quality: "good" if 2+ story elements (character + action, or action + outcome)
  relating to these characters: {collected_names}. "weak" if single sentence/no progression.
- is_related_to_collection: true if mentions or relates to: {collected_names}

Output JSON: {"intent": "...", "story_quality": "...", "is_related_to_collection": ...}
```

## Integration with Step Handlers

### Invitation (STEP_2_RULES / STEP_2_MISSION)

Before:
```
Script Agent generates dialogue + child_intent → handler reads child_intent → routes
```

After:
```
Classifier → intent stored on state → handler routes → Script Agent generates dialogue
```

| Intent | Action |
|--------|--------|
| `confirm` | Set `invitation_accepted`, advance state, generate celebration |
| `decline` | Increment `invitation_decline_count`, generate re-invite or exit |
| `substantive` / `off_topic` | Stay on step, generate re-invite |

### Collection (STEP_3_COLLECT / STEP_3_ROUND)

Before: No intent signal — Script Agent generates and handler checks `stay_on_step`.

After: Intent is passed as context to Script Agent via `{child_intent}` template variable.

| Intent | Effect on Script Agent |
|--------|----------------------|
| `confirm` | Knows child is agreeing, not providing detail → generates fresh prompt, no repeated question |
| `substantive` | Normal detail/answer processing |
| `off_topic` | Gentle redirect |

### Synthesis (STEP_4_SYNTHESIS)

Before: T0 uses hardcoded frozenset, T1/T2 uses separate `_classify_story_response` LLM call.

After: All tiers use unified classifier.

| Intent | Action |
|--------|--------|
| `confirm` | AI generates full story (child wants AI to proceed) |
| `decline` | AI generates full story |
| `substantive` + `story_quality == "good"` | Celebrate and advance |
| `substantive` + `story_quality == "weak"` | Improve phase (T1/T2) or generate (T0) |
| `off_topic` | Re-invite (if prompt_count < 2), else generate |

## Script Agent Changes

- Remove `child_intent` from `TurnResponse` JSON output schema
- Add `{child_intent}` template variable to the script turn prompt so the Script Agent knows the classified intent
- Script Agent tailors tone based on the pre-classified intent (e.g., celebration for confirm on invitation) but does not classify itself

## State Changes

Add `child_intent` field to `SessionStateModel`:
```python
child_intent: str = Field(default="", description="Pre-classified intent for the current turn")
```

This is set at the top of `resolve_turn` before any step-specific logic runs.

## What Gets Removed

| Item | Location |
|------|----------|
| `_classify_story_response()` | `turn_handler.py` |
| `_is_affirmative_or_continuation()` | `turn_handler.py` |
| `_AFFIRMATIVE_PATTERNS` | `turn_handler.py` |
| `child_intent` field | `schemas/turn_response.py` |
| `StoryClassification` schema | `schemas/story_classification.py` (file deleted) |
| All `turn_response.child_intent` reads | `turn_handler.py` step handlers |

## Files Modified

| File | Change |
|------|--------|
| `backend/schemas/child_intent.py` | New: `ChildIntentClassification` schema |
| `backend/schemas/turn_response.py` | Remove `child_intent` field |
| `backend/schemas/story_classification.py` | Delete file |
| `backend/schemas/session_state.py` | Add `child_intent` field |
| `backend/turn_handler.py` | Add `_classify_child_intent`, remove old classifiers, update all step handlers |
| `backend/agents/script_agent.py` | Remove `child_intent` from output schema, add `{child_intent}` template var |
| `backend/skills/script_turn.md` | Update prompt to remove child_intent output, add child_intent context |
| `backend/skills/step_instructions/cat5_step2_mission.md` | Remove child_intent classification rules |
| `backend/skills/step_instructions/cat1_step2_rules.md` | Remove child_intent classification rules |
| `tests/test_turn_handler.py` | Update tests for new classification flow |
| `tests/test_debug_payload.py` | Update if affected |

## Latency Impact

| Step | Before | After | Net |
|------|--------|-------|-----|
| Invitation | 1 Script Agent call | 1 classifier (~150ms) + 1 Script Agent | +150ms |
| Invitation acceptance | 2 Script Agent calls | 1 classifier + 1 Script Agent | **-4000ms** |
| Collection | 1 Script Agent call | 1 classifier + 1 Script Agent | +150ms |
| Synthesis evaluate (T0) | 1 Script Agent call | 1 classifier + 1 Script Agent | +150ms |
| Synthesis evaluate (T1/T2) | 1 classifier (~200ms) + 1 Script Agent | 1 classifier (~150ms) + 1 Script Agent | -50ms |

## Out of Scope

- No changes to the planner pass
- No changes to visual agent or recipe assembler
- No changes to frontend (debug panel already shows intent via `llm_output.child_intent` — will need minor update to read from new location)
- No changes to TTS/STT pipeline
