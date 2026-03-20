# Fix: LLM Conversation Flow Guardrails

## Problem 1: Synthesis skips to celebration

During Cat5 STEP_4_SYNTHESIS, the Script Agent sometimes sets `stay_on_step: false` when its response still invites child input (ends with a question). This auto-advances to celebration without waiting for the child.

## Problem 2: Premature completion language during collection

During Cat5 STEP_3_COLLECT, the LLM says things like "perfect final treasure" when items still remain (e.g., 2/3 collected). The progress numbers are injected into the prompt but the LLM ignores them.

## Solutions Implemented

### 1. Synthesis guardrail (`turn_handler.py`)
- Override `stay_on_step` to `true` when synthesis dialogue ends with `?`
- Override `stay_on_step` to `true` when fewer than 2 child turns on synthesis (minimum engagement)

### 2. Collection completion language guardrail (`turn_handler.py`)
- Regex-based detection of premature completion language ("final treasure", "mission complete", "all done", etc.)
- When detected and `remaining_count > 0`: inject corrective hint, regenerate response, remove hint from history
- Single retry — if the second attempt also fails, it goes through (avoids infinite loops)

### 3. Prompt improvements
- `cat5_step4_synthesis.md`: Added explicit "inspire me" handling as `stay_on_step: true`
- `cat5_step3_collect.md`: Added FORBIDDEN WORDS list when `remaining_count > 0`

## Files Modified

1. `backend/turn_handler.py` — Both guardrails + `_has_completion_language()` helper
2. `backend/skills/step_instructions/cat5_step4_synthesis.md` — "Inspire me" handling
3. `backend/skills/step_instructions/cat5_step3_collect.md` — Forbidden words for premature completion
