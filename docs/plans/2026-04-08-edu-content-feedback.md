# Edu Team Content Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address five content quality issues from the edu team review: narrow answer acceptance, directive language, story follow-through gaps, complex scavenger hunt instructions, and over-long summaries without visual recall.

**Architecture:** All changes are prompt/content-level — no schema renames, no new LLM calls, no pipeline changes. A new `content_design_rules.md` doc establishes shared principles. Turn Director rules, step instructions, game definitions, tier rules, and one new frontend widget are updated.

**Tech Stack:** Python (prompt strings, YAML), Markdown (step instructions), React/JSX (frontend widget), Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-04-08-edu-team-content-feedback-design.md`

---

### Task 1: Create Content Design Principles Document

**Files:**
- Create: `backend/skills/content_design_rules.md`

- [ ] **Step 1: Create the content design rules file**

```markdown
## Content Design Rules

These rules apply to ALL child-facing dialogue generation. The Script Agent, Turn Director, and Speaker must follow them.

### P1 — Accept Creative Answers
Any child answer that engages with the scenario is valid, even if it doesn't match the expected theme list. Only classify as off-topic when the child is clearly not engaging with the current scenario at all. "Hungry" is a valid answer to "how does the tummy feel?" even if expected themes were cozy and sleepy.

### P2 — Invitational Framing
All prompts to the child must be phrased as invitations or wonderings, never as instructions. Test: if the sentence works as a command from a teacher, rewrite it.
- DO: "I wonder how it feels..." / "Would you like to look for...?"
- DON'T: "Touch it and describe how it feels" / "Go find a soft thing"

### P3 — Concrete Before Abstract
For T0 (ages 2-4), anchor abstract concepts to the entity the child already knows. Use the entity as a sensory reference point.
- DO: "Your dandelion friend is so fluffy! I wonder if something else fluffy is nearby..."
- DON'T: "Something fluffy might be nearby."

### P4 — Story Continuity
Naming characters is the beginning of a story, not a standalone activity. The transition from naming to story should be seamless — bridge from the last character named into the story invitation. Never reset the emotional arc.

### P5 — Show, Don't Summarize
During review and closing, show collected photos on screen and reference 1-2 specific discoveries. Don't narrate a long recap. Let the visuals do the heavy lifting.
```

- [ ] **Step 2: Commit**

```bash
git add backend/skills/content_design_rules.md
git commit -m "docs(content): add content design principles"
```

---

### Task 2: Widen Answer Acceptance in Turn Director (Issue #1)

**Files:**
- Modify: `backend/agents/turn_director.py:103-139` (Cat1 round rules strings)
- Modify: `backend/skills/turn_director_system.md:9` (after Action Definitions)
- Modify: `backend/agents/script_agent.py:644` (acceptable_themes label)

- [ ] **Step 1: Split "wrong/unexpected" into two categories in `_CAT1_ROUND_RULES_VOICE_ACTING`**

In `backend/agents/turn_director.py`, replace the single "wrong/unexpected" rule in `_CAT1_ROUND_RULES_VOICE_ACTING` (line ~112):

```python
- Child gave a wrong/unexpected answer:
  action=stay, direction="Warmly acknowledge. Model a SOUND or ACTION (e.g., 'Woof!', 'Yawn!', tremble), then offer a binary choice between two emotions."
```

With these two rules:

```python
- Child gave an unexpected-but-on-topic answer (related to the scenario but not a listed theme — e.g., "hungry" when asked about feelings):
  action=advance, direction="Celebrate their creative take! Echo back their specific word and build on it with wonder before transitioning."
- Child gave an off-topic answer (clearly unrelated to the scenario — e.g., talking about a TV show during a mood scene):
  action=stay, direction="Warmly acknowledge what they said, then gently redirect to the scenario with a SOUND or ACTION and offer a binary choice between two emotions."
```

- [ ] **Step 2: Apply the same split to `_CAT1_ROUND_RULES_STORYTELLING`**

In `backend/agents/turn_director.py`, replace in `_CAT1_ROUND_RULES_STORYTELLING` (line ~130):

```python
- Child gave a wrong/unexpected answer:
  action=stay, direction="Warmly acknowledge. Then offer a binary choice between two concrete things the {entity_name} might see, find, or do in the scene."
```

With:

```python
- Child gave an unexpected-but-on-topic answer (related to the scene but not a listed theme):
  action=advance, direction="Celebrate their creative idea! Echo back their specific word and weave it into the story before transitioning."
- Child gave an off-topic answer (clearly unrelated to the current scene):
  action=stay, direction="Warmly acknowledge, then gently redirect with a binary choice between two concrete things the {entity_name} might see or do in the scene."
```

- [ ] **Step 3: Add answer acceptance principle to Turn Director system prompt**

In `backend/skills/turn_director_system.md`, add after the `## Action Definitions` section (after line 13):

```markdown

## Answer Acceptance

A child's answer is "good" if it engages with the scenario. It does NOT need to match a specific expected theme. Children are imaginative — "hungry" is a valid response to "how does the tummy feel?" even if expected themes were cozy and sleepy. Only classify as off-topic when the child is clearly not engaging with the current scenario at all.
```

- [ ] **Step 4: Reframe acceptable_themes label in Script Agent**

In `backend/agents/script_agent.py`, change line 644 from:

```python
            lines.append(f"Acceptable themes: {', '.join(goal_source.acceptable_themes)}")
```

To:

```python
            lines.append(f"Theme examples (for inspiration — any on-topic answer is valid): {', '.join(goal_source.acceptable_themes)}")
```

- [ ] **Step 5: Update Cat1 step instruction to match new acceptance model**

In `backend/skills/step_instructions/cat1_step3_round.md`, replace lines 18-19:

```markdown
- **Good/creative answer**: Enthusiastic affirmation that references what they said. Set sfx_cue to "slot_fill_chime". Optionally add ONE short imaginative tidbit (1 sentence max). Do NOT say "Round X done!" or any explicit round counter — just celebrate what they said. That's it — stop here.
- **Wrong/unexpected answer**: Warmly acknowledge the attempt ("Ooh, interesting thought!"), then model your idea and offer a binary choice.
```

With:

```markdown
- **Good/creative answer** (including unexpected-but-on-topic — any answer that engages with the scenario): Enthusiastic affirmation that references what they said. Set sfx_cue to "slot_fill_chime". Optionally add ONE short imaginative tidbit (1 sentence max). Do NOT say "Round X done!" or any explicit round counter — just celebrate what they said. That's it — stop here.
- **Off-topic answer** (clearly unrelated to the scenario): Warmly acknowledge the attempt ("Ooh, interesting thought!"), then model your idea and offer a binary choice.
```

- [ ] **Step 6: Run linting**

```bash
cd backend && uv run ruff check agents/script_agent.py agents/turn_director.py && uv run ruff format agents/script_agent.py agents/turn_director.py
```

- [ ] **Step 7: Commit**

```bash
git add backend/agents/turn_director.py backend/skills/turn_director_system.md backend/agents/script_agent.py backend/skills/step_instructions/cat1_step3_round.md
git commit -m "fix(content): widen answer acceptance in Turn Director

Split wrong/unexpected into on-topic-creative (advance) vs
off-topic (stay). Reframe acceptable_themes as non-exclusive
theme examples."
```

---

### Task 3: Fix Directive Language (Issue #2)

**Files:**
- Modify: `backend/tier_rules.yaml:41-45, 76-80, 111-115` (forbidden_directives for all tiers)
- Modify: `backend/games/fluffy_expedition_dandelion.md:29` (detail_question_template)
- Modify: `backend/games/fluffy_expedition_dandelion.md:22` (collection_criterion)
- Modify: All 9 Cat5 game `.md` files (collection_criterion values)

- [ ] **Step 1: Expand forbidden_directives in tier_rules.yaml**

In `backend/tier_rules.yaml`, for each tier (T0, T1, T2), expand the `forbidden_directives` list. For T0 (lines 41-45), replace:

```yaml
    forbidden_directives:
      - "Go find!"
      - "Now let's..."
      - "Look for..."
      - "Tell me!"
```

With:

```yaml
    forbidden_directives:
      - "Go find!"
      - "Now let's..."
      - "Look for..."
      - "Tell me!"
      - "Touch..."
      - "Describe..."
      - "Show me..."
      - "Try to..."
      - "Find..."
```

Apply the same expansion to T1 (lines 76-80) and T2 (lines 111-115).

- [ ] **Step 2: Rewrite directive `detail_question_template` values**

In `backend/games/fluffy_expedition_dandelion.md`, line 29, change:

```yaml
  detail_question_template: "Touch it gently — how does it feel?"
```

To:

```yaml
  detail_question_template: "I wonder how it feels..."
```

No other game files have directive `detail_question_template` values — the rest are already invitational ("What does this remind you of?", "How are the dots different?", etc.).

- [ ] **Step 3: Rewrite directive `collection_criterion` values across all Cat5 games**

All 9 Cat5 games start with "Find..." which is imperative. Rewrite each to invitational framing:

**`backend/games/fluffy_expedition_dandelion.md:22`:**
```yaml
  collection_criterion: "Things that are fluffy, fuzzy, or soft"
```

**`backend/games/polka_dot_patrol.md:22`:**
```yaml
  collection_criterion: "Things with dots, spots, or circles"
```

**`backend/games/color_friends_adventure_crayons.md:21`:**
```yaml
  collection_criterion: Things that match your favorite crayon color
```

**`backend/games/circle_spotter_challenge_eye.md:21`:**
```yaml
  collection_criterion: "Things outside that have eye-like shapes: circles, rings, dots, or concentric patterns"
```

**`backend/games/shimmer_spotter_safari_goldfish.md:21`:**
```yaml
  collection_criterion: Water creatures or shimmery things nearby
```

**`backend/games/sound_detective_agency_piano.md:21`:**
```yaml
  collection_criterion: Things outside that make interesting sounds when you tap, shake, or blow on them
```

**`backend/games/rain_guard_patrol_raincoat.md:21`:**
```yaml
  collection_criterion: Things that cover, shelter, or protect from rain
```

**`backend/games/brave_things_hunt_lion.md:21`:**
```yaml
  collection_criterion: Things that look big, strong, or tough
```

**`backend/games/neighborhood_safety_patrol_firefighter.md:30`:**
```yaml
  collection_criterion: Things in the neighborhood that help keep people safe (warn, protect, or guide)
```

The pattern: remove the leading "Find" imperative verb. The `collection_criterion` is referenced in prompts as `{collection_criterion}`, where the step instruction already builds the invitational framing around it.

- [ ] **Step 4: Commit**

```bash
git add backend/tier_rules.yaml backend/games/fluffy_expedition_dandelion.md backend/games/polka_dot_patrol.md backend/games/color_friends_adventure_crayons.md backend/games/circle_spotter_challenge_eye.md backend/games/shimmer_spotter_safari_goldfish.md backend/games/sound_detective_agency_piano.md backend/games/rain_guard_patrol_raincoat.md backend/games/brave_things_hunt_lion.md backend/games/neighborhood_safety_patrol_firefighter.md
git commit -m "fix(content): remove directive language from templates

Expand forbidden_directives with Touch/Describe/Show me/Find.
Rewrite collection_criterion values to drop imperative 'Find'.
Fix fluffy_expedition detail_question_template to invitational."
```

---

### Task 4: Bridge Collection → Synthesis for Story Continuity (Issue #3)

**Files:**
- Modify: `backend/skills/step_instructions/cat5_step3_collect.md:17` (last-item rule)
- Modify: `backend/skills/step_instructions/cat5_step4_synthesis.md:11-24` (INVITE phase)

- [ ] **Step 1: Add story bridge to last collection round**

In `backend/skills/step_instructions/cat5_step3_collect.md`, replace rule 6 (line 17):

```markdown
6. If remaining_count = 0: this is the LAST item. Set sfx_cue to "mission_complete_fanfare" in Phase B. Do NOT ask any questions — the system transitions next.
```

With:

```markdown
6. If remaining_count = 0: this is the LAST item. Set sfx_cue to "mission_complete_fanfare" in Phase B. After celebrating the last character, add a bridge sentence connecting all named characters (e.g., "Now {collected_names} are all together... I wonder what adventure they'll have!"). Do NOT ask any questions — the system transitions next.
```

- [ ] **Step 2: Rework synthesis INVITE phase for seamless story entry**

In `backend/skills/step_instructions/cat5_step4_synthesis.md`, replace the INVITE phase (lines 11-23):

```markdown
### PHASE: INVITE (synthesis_phase == "invite")

**CRITICAL: Do NOT tell a story. Do NOT narrate. Do NOT generate story content.** Your ONLY job in this phase is to ASK the child if they want to make up a story. Then STOP and wait for their response.

**Rules:**
1. Do NOT re-celebrate or recap the collection. One brief transition sentence (max 8 words), then invite.
2. Use invitational language — "Would you like to...?" not "Now let's make a story!"
3. Name the characters to spark the child's imagination.
4. For T0: offer a simple starter — "Would you like to tell a little story about {collected_names}?"
5. For T1/T2: can be slightly more open — "Would you like to make up a story about what {collected_names} do together?"
6. **MUST set `stay_on_step: true`** — we MUST wait for the child's response before proceeding.
7. Screen widget: `photo_grid`. Set sfx_cue to null.
8. **Your response must END with a question mark.** If it doesn't end with "?", you've done it wrong.
```

With:

```markdown
### PHASE: INVITE (synthesis_phase == "invite")

**CRITICAL: Do NOT tell a full story. Do NOT narrate beyond the starter.** Your job is to bridge from the collection into a story and invite the child in.

**Rules:**
1. Bridge from the collection — reference the characters by name to maintain continuity.
2. For T0: Start the story with a short opener and invite the child in — "{first_character} was sitting quietly when {last_character} came bouncing over... What do you think happened next?"
3. For T1/T2: Bridge with the characters and invite — "{collected_names} are all together now. Would you like to find out what adventure they have?"
4. Use invitational language — never "Now let's make a story!"
5. **MUST set `stay_on_step: true`** — we MUST wait for the child's response before proceeding.
6. Screen widget: `photo_grid`. Set sfx_cue to null.
7. **Your response must END with a question mark.** If it doesn't end with "?", you've done it wrong.
```

- [ ] **Step 3: Commit**

```bash
git add backend/skills/step_instructions/cat5_step3_collect.md backend/skills/step_instructions/cat5_step4_synthesis.md
git commit -m "fix(content): bridge collection to synthesis seamlessly

Add story bridge sentence to last collection round. Rework
synthesis INVITE to use characters immediately instead of
abstractly asking 'would you like to make a story?'"
```

---

### Task 5: Simplify Scavenger Hunt Instructions for T0 (Issue #4)

**Files:**
- Modify: `backend/skills/step_instructions/cat5_step3_collect.md:13` (Phase A rule, add entity anchoring)

- [ ] **Step 1: Add entity anchoring and improved stuck scaffolding for T0**

In `backend/skills/step_instructions/cat5_step3_collect.md`, after rule 2 (line 13), add a new rule 2a. Insert after the Phase A opening rule:

Replace line 13:
```markdown
2. **Phase A opening (no photo selected yet, no "[selected" message in child input):** Invite the child to find and photograph something {observation_angle}. Do NOT say "you found" or celebrate — nothing was found yet. Use invitational language: "I wonder if something {observation_angle} is nearby..." Set `stay_on_step: true`. Screen widget: `photo_display`.
```

With:
```markdown
2. **Phase A opening (no photo selected yet, no "[selected" message in child input):** Invite the child to find and photograph something {observation_angle}. Do NOT say "you found" or celebrate — nothing was found yet. Use invitational language: "I wonder if something {observation_angle} is nearby..." Set `stay_on_step: true`. Screen widget: `photo_display`.
    - **T0 first-round anchoring:** For Tier T0, the FIRST collection prompt (round 1) must reference the {entity_name} as a concrete example: "Your {entity_name} friend is so {observation_angle}! I wonder if something else {observation_angle} is nearby..." This gives the child a sensory reference point they already understand.
    - **T0 stuck scaffolding:** If a T0 child is silent during Phase A, model with the entity: "Your {entity_name} feels {observation_angle}... maybe something else nearby feels like that too?" rather than offering a generic binary choice.
```

- [ ] **Step 2: Commit**

```bash
git add backend/skills/step_instructions/cat5_step3_collect.md
git commit -m "fix(content): add entity anchoring for T0 scavenger hunts

T0 first-round prompts now reference the entity as a concrete
sensory example. Stuck scaffolding uses entity-based modeling
instead of generic binary choices."
```

---

### Task 6: Reduce Closing Density + Add Photo Recall Widget (Issue #5)

**Files:**
- Modify: `backend/skills/step_instructions/cat5_step6_closing.md` (reduce element count, add word limits)
- Modify: `backend/skills/step_instructions/cat5_step5_celebrate.md:11` (screen widget)
- Create: `frontend/src/widgets/PhotoRecallGrid.jsx`
- Modify: `frontend/src/components/DeviceScreen.jsx:1-21` (import + register widget)

- [ ] **Step 1: Reduce closing density in cat5_step6_closing.md**

Replace the full content of `backend/skills/step_instructions/cat5_step6_closing.md` with:

```markdown
## Current Step: Closing Speech + IB Concept Badge

### GOAL
Name the IB concepts naturally in a sentence about what the child experienced, then end with a warm goodbye.

### CONTEXT
Concepts: {ib_key_concepts} | Characters: {collected_names} | Role: {role_title} | Entity: {entity_name} | Tier: {tier}

### STRUCTURAL RULES
1. Weave concept words INTO a sentence about what the child discovered — never announce them like a textbook ("That is called Connection").
2. Concept count: T0 = 1 concept | T1 = 2 concepts | T2 = up to 3 concepts.
3. Do NOT repeat "mission accomplished" or the role title — that was the previous step.
4. End with a forward-looking sentence that's personal, not generic.
5. Screen widget: `badge_award`.

### TIER-SPECIFIC DENSITY
- **T0**: 2 elements ONLY — concept weave + warm goodbye. Max 20 words total. The role title and celebration already happened in Step 5 — do NOT repeat them here.
- **T1**: 3 elements — concept weave + one specific callback to a character or discovery + goodbye. Max 35 words total.
- **T2**: 4 elements — concept weave + callback + reflection + goodbye. Max 50 words total.

### WHAT MAKES THIS GOOD
The closing should feel like saying goodbye to a friend, not reading a report card. Reference their specific characters or discoveries.

Bad: "Your friends share a special Connection! Keep exploring!"
Good (T0): "Mossy and Woolly are soft in different ways — that's Connection! See you next time?"
Good (T1): "Mossy, Petal, and Woolly are all soft in different ways — that's a Connection you found all by yourself! I wonder what you'll discover tomorrow?"

### EXAMPLES (for tone/structure reference ONLY — do NOT copy phrases, sentences, or patterns from these examples. Generate completely original wording every time.)

{sampled_examples}
```

- [ ] **Step 2: Update celebrate step to use photo_recall_grid widget**

In `backend/skills/step_instructions/cat5_step5_celebrate.md`, change line 11:

```markdown
2. Keep to 2-3 sentences. Set sfx_cue to "celebration_fanfare". Screen widget: `badge_award`.
```

To:

```markdown
2. Keep to 2-3 sentences. Set sfx_cue to "celebration_fanfare". Screen widget: `photo_recall_grid` (shows all collected photos with character names).
```

- [ ] **Step 3: Create PhotoRecallGrid widget**

Create `frontend/src/widgets/PhotoRecallGrid.jsx`:

```jsx
import BASE from '../utils/basePath';
import { PhotoFrameIcon } from '../icons';

export default function PhotoRecallGrid({ animation, sessionState }) {
  const collectedIds = sessionState?.collected_photos || [];
  const collectedNames = sessionState?.collected_names || [];

  if (collectedIds.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 p-3">
        <p className="text-sm text-gray-400">No photos yet</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center gap-2.5 max-[380px]:gap-2 p-3 max-[380px]:p-2.5 ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      <h3 className="text-sm font-bold font-display text-[var(--color-forest-dark)] tracking-tight">
        Your Discoveries
      </h3>

      <div className={`grid ${collectedIds.length <= 2 ? 'grid-cols-2' : 'grid-cols-3'} gap-3 max-[380px]:gap-2`}>
        {collectedIds.map((id, i) => (
          <div key={id} className="flex flex-col items-center gap-1">
            <div className="w-[clamp(3.1rem,14vw,4rem)] h-[clamp(3.1rem,14vw,4rem)] rounded-xl max-[380px]:rounded-lg overflow-hidden border-2 border-[var(--color-sunflower)]/40 shadow-sm">
              <img
                src={`${BASE}/icons/${id}.png`}
                alt={collectedNames[i] || `Item ${i + 1}`}
                loading="lazy"
                className="w-full h-full object-cover"
              />
            </div>
            {collectedNames[i] && (
              <span className="text-xs max-[380px]:text-[11px] font-medium text-[var(--color-forest-dark)] text-center leading-tight max-w-[4.5rem] truncate">
                {collectedNames[i]}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Register PhotoRecallGrid in DeviceScreen**

In `frontend/src/components/DeviceScreen.jsx`, add the import after line 5 (`import PhotoGrid...`):

```jsx
import PhotoRecallGrid from '../widgets/PhotoRecallGrid';
```

And add to the `WIDGET_MAP` object (after the `photo_grid` entry, line 18):

```jsx
  photo_recall_grid: PhotoRecallGrid,
```

- [ ] **Step 5: Commit**

```bash
git add backend/skills/step_instructions/cat5_step6_closing.md backend/skills/step_instructions/cat5_step5_celebrate.md frontend/src/widgets/PhotoRecallGrid.jsx frontend/src/components/DeviceScreen.jsx
git commit -m "fix(content): reduce closing density, add photo recall

T0 closing now max 20 words with 2 elements only. Celebrate
step shows photo_recall_grid instead of badge_award. New
PhotoRecallGrid widget displays collected photos with names."
```

---

### Task 7: Run Tests and Final Verification

**Files:**
- Read: All modified files for consistency check

- [ ] **Step 1: Run backend linting and type checks**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy agents/turn_director.py agents/script_agent.py
```

Expected: Clean pass. The only Python code changes are string edits in `turn_director.py` and a label change in `script_agent.py`.

- [ ] **Step 2: Run backend tests**

```bash
cd backend && uv run pytest -x -q
```

Expected: All tests pass. No schema changes were made. The `acceptable_themes` field name is unchanged, only its prompt label changed.

- [ ] **Step 3: Run frontend build check**

```bash
cd frontend && npm run build
```

Expected: Clean build. The new `PhotoRecallGrid.jsx` follows the same pattern as `PhotoGrid.jsx`.

- [ ] **Step 4: Commit any linting fixes if needed**

```bash
git add -A && git commit -m "style: fix lint issues from content feedback changes"
```

Only run this if Step 1 or Step 3 reported fixable issues.
