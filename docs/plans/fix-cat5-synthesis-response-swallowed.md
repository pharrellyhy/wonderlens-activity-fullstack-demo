# Fix: Cat5 Synthesis Response Swallowed

## Problem

In Cat5 Step 4 (synthesis), when the child responds to the synthesis prompt, the AI's
synthesis response is never shown. Instead, the turn handler advances to STEP_5_CELEBRATE,
generates a new response, and returns only that. The child sees celebrate + closing but
never the AI's creative engagement with their input.

Additionally, "can you help me" is misclassified as "do it for me" instead of "stuck/confused",
causing the AI to skip synthesis entirely and jump to closing.

## Fix

### A. Prompt fix — `backend/skills/step_instructions/cat5_step4_synthesis.md`

Add help requests ("can you help me", "help", "I need help") to the stuck/confused bucket
with explicit `stay_on_step: true` guidance.

### B. Architecture fix — `backend/turn_handler.py` section 7d

**Interactive step completion** (lines 534-549): When `stay_on_step: false`, return the
current step's response instead of generating the next step's. Capture response_type and
screen_frame before advancing, then return with auto_advance based on the new step.

**Auto-advance path** (lines 550+): Use `_already_prompted_on_step` to decide:
- Already generated (e.g., Cat1 celebrate from round advance): advance through, generate
  the next step (preserves current behavior).
- Not yet generated (e.g., Cat5 celebrate after synthesis fix): generate for current step,
  then advance. Special-case closing steps to return auto_advance=False.

### Result

User sees: synthesis response → celebrate → closing (each as a separate visible turn).

## Files Changed

- `backend/skills/step_instructions/cat5_step4_synthesis.md`
- `backend/turn_handler.py`
