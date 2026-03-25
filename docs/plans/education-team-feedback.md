# Education Team Feedback: Full Implementation Plan

## Context

The education team reviewed the WonderLens Activity Demo and provided 6 feedback items (in `docs/game_demo_feedback.txt`). The core issues: activity flow is unclear, AI language is too decorated for kids, questions are too open-ended, TTS auto-play is disruptive for testers, the pre-start page is too abstract, and activities lack "game feel." We're addressing all 6 with a **prompt-first approach** — most changes live in step instruction markdown files, with 2 small frontend changes.

## Changes Overview

| # | Feedback | Approach | Scope |
|---|----------|----------|-------|
| 1 | Flow unclear, need mini-rewards | Add SFX/progress language to step instructions | Prompt |
| 2 | GameDetailView too abstract | Plain summary + expandable steps | Frontend + Backend data |
| 3 | AI language too decorated | Global simplicity rules in script_system.md + per-file reminders | Prompt |
| 4 | TTS should default muted | Add ttsEnabled state + toggle | Frontend |
| 5 | Questions too open-ended | Scaffold+model pattern in step instructions | Prompt |
| 6 | Lacks game feel | Mission/quest framing in step instructions | Prompt |

## Implementation Order

### Phase 1: Language Foundation (Change 3)

**File: `backend/prompts/script_system.md`**
- Add a `## Language Simplicity Rules` section with:
  - Short, direct sentences. One idea per sentence.
  - Max one metaphor per turn. Limit decorative adjectives to one per noun.
  - Tier calibration: T0 max ~6 words/sentence, no metaphors. T1 max ~10 words. T2 max ~15 words.
  - Prefer everyday words: "round" not "perfectly spherical", "big" not "enormous".

**Files: All 26 step instruction files in `backend/skills/step_instructions/`**
- Add a one-line language reminder near the top of each file:
  > **Language: Short, plain sentences. One metaphor max. Match sentence length to tier.**

### Phase 2: Scaffold + Model Pattern (Change 5)

**Key principle to add to collection and synthesis instructions:** "Default: model your own idea first, then invite child to agree/modify. Fallback on silence/'I don't know': offer 2-3 concrete choices."

**Files to modify:**
- `backend/skills/step_instructions/cat5_step3_collect.md` — Add T0 modeling guidance for Phase A; add model-first principle for Phase B detail responses; update silence handler to model+offer-choices
- `cat5_step3_collect__naming_story.md` — Phase B silence path: model a name + offer binary choice
- `cat5_step3_collect__comparison_chart.md` — Phase B silence path: model observation + offer binary
- `cat5_step4_synthesis.md` — Default: model your answer first; stuck/silence: offer 2-3 choices
- `cat5_step4_synthesis__naming_story.md` — Scaffold the ONE question with a model
- `cat5_step4_synthesis__comparison_chart.md` — T0: always binary; T1/T2: can use open ranking
- `cat1_step3_round.md` — Add model-first for hesitation; existing "I don't know" handler already has binary choices

### Phase 3: Example Step + Game Feel (Changes 6, 1, 7)

**Change 6 — Example demonstration embedded in mission briefing:**

**File: `backend/skills/step_instructions/cat5_step2_mission.md`**
- Add section: "Embedded Example Demonstration (NON-NEGOTIABLE)"
- After explaining the 3-part mission, before invitation: demonstrate one round in 2-3 sentences
  - naming_story: "Let me show you — see that cloud? It looks fluffy! I'd call it Cloud Puff!"
  - comparison_chart: "Let me try — see the ladybug's spots? Big and round! When you find yours, we'll compare."
- Demo item does NOT count toward collection_count
- End with: "Now it's your turn! Would you like to go find one?"

**Note:** Cat1 `cat1_step2_rules.md` and its 5 variants already include demo round instructions — no changes needed there.

**Changes 1+7 — Progress tracking, SFX cues, and mission framing:**

**File: `backend/skills/step_instructions/cat5_step3_collect.md`**
- Add framing note: "Frame as a mission/quest. Use words like 'found', 'spotted', 'discovered', 'mission'."
- Correct photo in Phase A: celebrate with count — "That's {n} out of {total}!" + `[AUDIO] sfx: slot_fill_chime`
- Phase B ideal response, remaining > 0: add `[AUDIO] sfx: slot_fill_chime`
- Phase B ideal response, remaining = 0: add `[AUDIO] sfx: mission_complete_fanfare`
- Replace "avoid mechanical progress counters" with "always pair numbers with enthusiasm"

**Files: `cat5_step3_collect__naming_story.md`, `cat5_step3_collect__comparison_chart.md`**
- Add SFX cues after each progressive character introduction (slot_fill_chime per find, mission_complete_fanfare on final)

**File: `backend/skills/step_instructions/cat5_step2_mission.md`**
- When child accepts mission: `[AUDIO] sfx: mission_accepted` + "Mission accepted!"

**File: `backend/skills/step_instructions/cat5_step5_celebrate.md`**
- Add: `[AUDIO] sfx: celebration_fanfare` + "Mission accomplished!" framing

**File: `backend/skills/step_instructions/cat1_step3_round.md`**
- After each round: brief progress note with enthusiasm + `[AUDIO] sfx: slot_fill_chime`
- Frame each round as a challenge, not a quiz question

**File: `backend/skills/step_instructions/cat1_step4_celebrate.md`**
- Add: `[AUDIO] sfx: celebration_fanfare` + "You beat all {total_rounds} rounds!" framing

### Phase 4: GameDetailView Redesign (Change 2)

**Backend data changes:**

**File: `backend/entity_registry.py`**
- Add to `EntityConfig`: `plain_description: str = ""` and `steps_summary: list[str] = []`
- In `_build_entity_summary()` (~line 205): add both fields to the summary dict

**File: `backend/game_parser.py`**
- Ensure `plain_description` and `steps_summary` are parsed from game MD frontmatter

**Files: All 18 game MD files in `backend/games/`** (only 5 are in the demo, but add to all for completeness)
- Add to each frontmatter:
  ```yaml
  plain_description: "Your child will [plain language activity description]."
  steps_summary:
    - "Step 1 description"
    - "Step 2 description"
    - "Step 3 description"
    - "Earn the [role] badge!"
  ```

**Frontend changes:**

**File: `frontend/src/components/GameDetailView.jsx`**
- Replace metaphor-heavy "About This Activity" section with:
  - Plain-language summary paragraph from `s.plain_description`
  - Keep role_title badge and IB theme/concept tags
  - Add expandable "See detailed steps" toggle showing `s.steps_summary` as ordered list
  - Move metaphor to expandable section (or remove)

### Phase 5: TTS Default Muted (Change 4)

**File: `frontend/src/hooks/useSessionOrchestration.js`**
- Add state: `const [ttsEnabled, setTtsEnabled] = useState(() => localStorage.getItem('ttsEnabled') === 'true')`
- Persist to localStorage on change
- In the auto-speak effect (~line 84-107): wrap TTS call in `if (ttsEnabled)` condition; else call `handleSpeakingDone()` directly (via setTimeout to avoid state-during-render) so silence timer and auto-advance still work
- Export `ttsEnabled` and `toggleTts` callback

**File: `frontend/src/App.jsx`**
- Destructure `ttsEnabled` and `toggleTts` from orchestration hook
- Add mute/unmute toggle button in the footer bar, near the "Speaking..." indicator
- Use speaker icon (muted/unmuted) as visual indicator

## Files Modified (Complete List)

| Category | Files | Count |
|----------|-------|-------|
| System prompt | `backend/prompts/script_system.md` | 1 |
| Step instructions | All 26 files in `backend/skills/step_instructions/` | 26 |
| Game definitions | All 18 files in `backend/games/` | 18 |
| Backend Python | `backend/entity_registry.py`, possibly `backend/game_parser.py` | 1-2 |
| Frontend JS | `useSessionOrchestration.js`, `App.jsx`, `GameDetailView.jsx` | 3 |
| **Total** | | **~50** |

## Verification

1. **Language (Change 3):** Start sessions at T0, T1, T2. Check AI output uses short, plain sentences appropriate to tier.
2. **Scaffold (Change 5):** During Cat5 collection, respond with silence or "I don't know." Confirm AI models an answer and offers choices.
3. **Example (Change 6):** Start Cat5 session. Confirm mission briefing includes a demo round before the invitation.
4. **Progress/Game Feel (Changes 1+7):** Play through full Cat5. Confirm progress counts with enthusiasm, SFX directives in output, mission/quest framing.
5. **GameDetailView (Change 2):** Click a game photo. Confirm plain summary visible, "See detailed steps" expands, tier/IB info preserved.
6. **TTS (Change 4):** Start session. Confirm no audio by default, toggle visible in footer, enabling toggle plays TTS, silence timer works when muted, setting persists in localStorage.
7. **Lint:** `cd backend && uv run ruff check . && uv run ruff format .`
