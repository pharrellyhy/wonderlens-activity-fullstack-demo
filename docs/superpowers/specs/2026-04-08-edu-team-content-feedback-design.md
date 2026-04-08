# Edu Team Content Feedback — Design Spec

**Date:** 2026-04-08
**Source:** `edu_team_feedback_0406.txt` (edu team review, 2026-04-06)
**Approach:** Content design principles + systematic pass (Approach B)

---

## Problem Statement

The edu team reviewed demo sessions and identified five content quality issues:

1. **Overly narrow answer acceptance** — Open-ended questions have narrow `acceptable_themes` lists. Valid creative answers (e.g., "hungry" for "how does his tummy feel?") are classified as wrong and the child gets redirected, which feels dismissive.
2. **Directive action language** — Phrases like "Touch each one and describe how it feels" command the child instead of inviting. Creative slot templates contain imperatives that get injected into dialogue.
3. **Story activities lack follow-through** — After naming characters, the system says "ready to play" but doesn't deliver a story. The transition from collection to synthesis feels like a reset, not a continuation.
4. **Scavenger hunt instructions too complex** — Abstract observation angles ("fluffy", "shimmery") lack concrete anchors for T0 (ages 2-4). Children don't know what to look for.
5. **Summary paragraphs too long + no visual recall** — Closing packs 4 elements into 2 sentences (for T0). No photos shown on screen during review, despite photos being the core of the activity.

## Content Design Principles

A new file `backend/skills/content_design_rules.md` will codify these as reusable rules referenced by the Script Agent and Speaker:

- **P1 — Accept creative answers.** Any child answer that engages with the scenario is valid, even if it doesn't match the expected theme list. Only classify as off-topic when the child is clearly not engaging with the current scenario. "Hungry" is a valid answer to "how does the tummy feel?" even if the expected themes were cozy and sleepy.
- **P2 — Invitational framing.** All prompts to the child must be phrased as invitations or wonderings, never as instructions. Test: if the sentence works as a command from a teacher, rewrite it. "I wonder how it feels..." not "Touch it and describe how it feels."
- **P3 — Concrete before abstract.** For T0, anchor abstract concepts to the entity the child already knows. "Your dandelion friend is so fluffy! I wonder if something else fluffy is nearby..." not just "Something fluffy might be nearby."
- **P4 — Story continuity.** Naming characters is the beginning of a story, not a standalone activity. The transition from naming to story should be seamless — bridge from the last character named into the story invitation.
- **P5 — Show, don't summarize.** During review and closing, show collected photos on screen and reference 1-2 specific discoveries. Don't narrate a long recap.

---

## Issue #1: Overly Narrow Answer Acceptance

### Root cause

Round definitions in game `.md` files have `acceptable_themes` lists (e.g., `[happy, cozy, warm, comfy, nice, sleepy, relaxed]`). The Script Agent injects these as "Acceptable themes: ..." into the Speaker prompt. The Turn Director classifies child input as "good/creative" vs "wrong/unexpected" — but "wrong/unexpected" is too broad, causing valid creative answers to trigger re-prompting.

### Changes

**A — Reframe `acceptable_themes` label in Script Agent (`backend/agents/script_agent.py`)**

Change the injection from:
```
Acceptable themes: happy, cozy, warm, comfy, nice, sleepy, relaxed
```
To:
```
Theme examples (for inspiration — any on-topic answer is valid): happy, cozy, warm, comfy, nice, sleepy, relaxed
```

The field name in the schema stays `acceptable_themes` for backward compat, but the prompt label changes.

**B — Split "wrong/unexpected" in Turn Director rules (`backend/agents/turn_director.py`)**

In `_CAT1_ROUND_RULES_VOICE_ACTING`, replace:
```
- Child gave a wrong/unexpected answer:
  action=stay, direction="Warmly acknowledge. Model a SOUND or ACTION..."
```
With:
```
- Child gave an unexpected-but-on-topic answer (related to the scenario but not a listed theme — e.g., "hungry" when asked about feelings):
  action=advance, direction="Celebrate their creative take! Echo back what they said and build on it with wonder."
- Child gave an off-topic answer (clearly unrelated to the scenario — e.g., talking about a TV show during a mood scene):
  action=stay, direction="Warmly acknowledge what they said, then gently redirect to the scenario."
```

Apply the same split to `_CAT1_ROUND_RULES_STORYTELLING`.

**C — Add acceptance principle to Turn Director system prompt (`backend/skills/turn_director_system.md`)**

Add after the Action Definitions section:
```
## Answer Acceptance

A child's answer is "good" if it engages with the scenario. It does NOT need to match
a specific expected theme. Children are imaginative — "hungry" is a valid response to
"how does the tummy feel?" even if expected themes were cozy and sleepy. Only classify
as off-topic when the child is clearly not engaging with the current scenario at all.
```

---

## Issue #2: Directive Action Language

### Root cause

Creative slot templates contain imperative verbs that get injected verbatim into dialogue. Example: `detail_question_template: "Touch it gently — how does it feel?"` Step instructions ban directives in most places, but the templates bypass these rules.

### Changes

**A — Rewrite `detail_question_template` values in game `.md` files**

Audit all game definitions. Replace imperative templates with invitational ones:
- "Touch it gently — how does it feel?" → "I wonder how it feels..."
- "Describe what you see" → "What do you notice about it?"
- Any template starting with an imperative verb gets rewritten.

**B — Expand `forbidden_directives` in `backend/tier_rules.yaml`**

Add to all tiers:
```yaml
forbidden_directives:
  - "Go find!"
  - "Now let's..."
  - "Look for..."
  - "Tell me!"
  - "Touch..."       # NEW
  - "Describe..."     # NEW
  - "Show me..."      # NEW
  - "Try to..."       # NEW
  - "Find..."         # NEW (imperative, not "Go find" specifically)
```

**C — Add invitational framing rule to content design principles doc**

Already covered by P2 above. The Script Agent and Speaker both reference this doc.

---

## Issue #3: Story Activities Lacking Follow-Through

### Root cause

Collection ends → system auto-transitions to synthesis → synthesis INVITE phase asks "Would you like to make up a story?" This feels like a new activity, not a continuation of what the child just built through naming.

### Changes

**A — Bridge from last collection round to synthesis (`backend/skills/step_instructions/cat5_step3_collect.md`)**

When `remaining_count = 0` (last item), the Phase B celebration should plant a story seed:
```
When remaining_count = 0: After celebrating the last character, add a bridge sentence
that connects all named characters: "Now Puffy, Mossy, and Woolly are all together...
I wonder what adventure they'll have!" Set sfx_cue to "mission_complete_fanfare".
```

**B — Rework synthesis INVITE phase (`backend/skills/step_instructions/cat5_step4_synthesis.md`)**

Remove rule 1 ("Do NOT re-celebrate or recap the collection. One brief transition sentence (max 8 words), then invite."). Replace with:

For T0: Start the story and invite the child in:
```
"One day, {first_character} was sitting quietly when {last_character} came
bouncing over... What do you think happened next?"
```

For T1/T2: Bridge from collection to story with the characters:
```
"{collected_names} are all together now. Would you like to find out what
adventure they have?"
```

The key change: the story invitation **uses the characters immediately**, not as an abstract "would you like to make a story?"

---

## Issue #4: Scavenger Hunt Instructions Too Complex

### Root cause

Abstract `observation_angle` values ("fluffy", "shimmery", "textured") lack concrete anchors for T0. The system avoids suggesting specific items (correctly), but doesn't provide enough scaffolding for very young children.

### Changes

**A — Entity anchoring for T0 (`backend/skills/step_instructions/cat5_step3_collect.md`)**

Add a T0-specific rule for Phase A (first collection prompt):
```
For T0, the FIRST collection prompt must reference the entity as a concrete example:
"Your dandelion friend is so fluffy! I wonder if something else fluffy is nearby..."
This gives the child a sensory reference point they already understand.
```

**B — Simplify observation_angle vocabulary for T0 in game `.md` files**

Audit T0 game definitions. Replace multi-syllable abstract words:
- "shimmery" → "shiny"
- "textured" → "bumpy"
- Keep T1/T2 vocabulary richer

**C — Improve stuck scaffolding for T0 (`backend/skills/step_instructions/cat5_step3_collect.md`)**

After one silence on a collection prompt, model with the entity:
```
"Your dandelion feels soft and fluffy... maybe something else nearby feels
like that too?"
```

Currently silence just gets a generic binary choice, which doesn't help if the child doesn't understand the observation concept. The entity-anchored scaffold provides a concrete reference.

---

## Issue #5: Summary Too Long + Missing Visual Recall

### Root cause: summary length

The closing packs 4 elements (celebrate + award role + name concepts + forward hook) into tier-limited sentences. For T0, that's 2 sentences — too dense for 4 elements.

### Root cause: no visual recall

The closing uses `badge_award` widget. No collected photos are shown on screen during review, despite the child's photos being the emotional core of the activity.

### Changes

**A — Reduce closing density (`backend/skills/step_instructions/cat5_step6_closing.md`)**

Restructure element count per tier:
- **T0**: 2 elements — concept weave + warm goodbye. Role title and celebration already happened in Step 5.
- **T1**: 3 elements — concept weave + one specific callback to a character/discovery + goodbye.
- **T2**: 4 elements (current behavior, unchanged).

Add explicit max word counts:
- T0 = 20 words total
- T1 = 35 words total
- T2 = 50 words total

**B — Add photo recall widget (`frontend/src/widgets/`)**

Create a new `PhotoRecallGrid` widget component:
- Renders a grid of collected photos with character name labels overlaid
- Used in Step 5 (celebrate) and optionally Step 6 (closing)
- Props: `photos` (array of photo URLs), `names` (array of character names)

**C — Wire photo recall into celebrate step (`backend/skills/step_instructions/cat5_step5_celebrate.md`)**

Change screen widget from `character_display` to `photo_recall_grid`. The Visual Agent generates a frame showing all collected photos with character names while the AI delivers the celebration speech.

**D — Keep badge visible in closing**

In Step 6, keep `badge_award` widget but consider a combined view that shows the badge alongside a smaller photo strip. This may be a frontend layout decision — the spec defines the intent, implementation plan will detail the component.

---

## Files Affected (Summary)

| Area | Files |
|------|-------|
| New: content design principles | `backend/skills/content_design_rules.md` |
| Turn Director rules | `backend/agents/turn_director.py` |
| Turn Director prompt | `backend/skills/turn_director_system.md` |
| Speaker prompt | `backend/skills/speaker_directive_system.md` |
| Step instructions | `cat5_step3_collect.md`, `cat5_step4_synthesis.md`, `cat5_step5_celebrate.md`, `cat5_step6_closing.md`, `cat1_step3_round.md` |
| Game definitions | ~16 files in `backend/games/` (reframe acceptable_themes label, rewrite directive templates, simplify T0 vocabulary) |
| Tier rules | `backend/tier_rules.yaml` |
| Frontend widget | New `PhotoRecallGrid` in `frontend/src/widgets/` |
| Script Agent | `backend/agents/script_agent.py` (change acceptable_themes label) |

## Out of Scope

- Turn Director architecture changes (no new classification logic, just prompt refinement)
- Schema field renaming (`acceptable_themes` field name stays, only prompt label changes)
- Scoring/evaluation updates (these follow separately once content changes land)
- New game definitions (existing games get updated, no new activities)
