# Education Team Feedback Round 2 — Prompt Fixes

## Context

Second round of education team feedback (`docs/game_demo_feedback_2.txt`) identified remaining issues after our first pass. Three actionable items:

- **A) Short repeat phrases** — When AI models an answer for the child to echo/repeat, the phrase must be very short (2-4 words max). "SPLASH TIME!" is fine; "SPLASH TIME! This is the best day ever!" is too long for a child to remember.
- **B) Cat1 open questions** — Cat1 voice_acting round questions like "If your dinosaur could talk, what would it say right now?" are too open and lack story structure. Need more guided alternatives with scaffold/choices.
- **C) Synthesis entry** — The dandelion synthesis felt abrupt. The instruction says "NO celebration, NO recap" but the jump into story mode confuses testers. Add a brief 1-sentence transition.

## Changes

### A) Short repeat phrases

**File: `backend/prompts/script_system.md`**
- Add rule to Language Simplicity section: "When modeling a phrase the child might echo or repeat, keep it to 2-4 words max. 'SPLASH TIME!' not 'SPLASH TIME! This is the best day ever!'"

**File: `backend/skills/step_instructions/cat1_step2_rules.md`**
- Add to demo round instruction: "The demo phrase you model must be 2-4 words. Short enough for a child to repeat."

**File: `backend/skills/step_instructions/cat1_step2_rules__voice_acting.md`**
- Add: "When you model a voice for the entity, keep the example dialogue to 2-4 words max."

### B) Cat1 open questions — voice_acting and storytelling_chain

**File: `backend/skills/step_instructions/cat1_step3_round__voice_acting.md`**
- Replace open "what would it say?" pattern with scaffold: "Would it say [option A] or [option B]?" for T0/T1. T2 can be slightly more open.
- Add: "NEVER ask 'If X could talk, what would it say?' — too open. Instead model first: 'I think it would say ROAR! What do you think — ROAR or something different?'"

**File: `backend/skills/step_instructions/cat1_step3_round__storytelling_chain.md`**
- Add: "When asking the child to continue the story, offer 2 choices: 'Does the cat find a fish or a ball of yarn?' not 'What happens next?'"

### C) Synthesis entry — softer transition

**File: `backend/skills/step_instructions/cat5_step4_synthesis.md`**
- Change the "NO celebration, NO recap" rule to: "Do NOT re-celebrate the full collection. But you MAY use ONE short transition sentence to set up the creative activity. Example: 'Now that all your fluffy friends are here...' then launch straight into the story/comparison."

**File: `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md`**
- Update the "CRITICAL" block: allow one brief transition sentence before the 4-beat story.

## Files Modified

| File | Change |
|------|--------|
| `backend/prompts/script_system.md` | Add short-phrase rule |
| `backend/skills/step_instructions/cat1_step2_rules.md` | Short demo phrase |
| `backend/skills/step_instructions/cat1_step2_rules__voice_acting.md` | Short model phrase |
| `backend/skills/step_instructions/cat1_step3_round__voice_acting.md` | Replace open questions with scaffold |
| `backend/skills/step_instructions/cat1_step3_round__storytelling_chain.md` | Add choice-based continuation |
| `backend/skills/step_instructions/cat5_step4_synthesis.md` | Allow 1-sentence transition |
| `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` | Allow 1-sentence transition |

## Verification

- Start Cat1 voice_acting (dog/dinosaur): verify demo phrase is short, round questions offer choices not open "what would it say?"
- Start Cat5 naming_story (dandelion): verify synthesis has a brief transition before launching into the story
- Check that language simplicity rules still hold
