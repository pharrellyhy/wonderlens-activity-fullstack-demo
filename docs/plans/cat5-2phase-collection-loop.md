# Cat5 2-Phase Collection Loop: Gap Analysis & Implementation Plan

## Context

New cat5 game designs (16 scenarios in `backend/games/cat5/`) introduce a **2-phase collection loop** where each round has:
- **Phase A (photo)**: child selects photo -> AI validates -> AI asks a detail-harvesting question
- **Phase B (detail)**: child responds verbally -> AI processes detail (names character or records observation) -> advance to next round

The current implementation uses a single-phase loop (photo -> react -> advance) and explicitly forbids text/verbal questions during collection. This plan updates the full stack to support the new design, using the existing 2 scenarios (polka_dot_patrol, fluffy_expedition_dandelion) as test cases.

---

## Gap Analysis Summary

| Area | Current State | New Design Requires | Gap Severity |
|------|--------------|---------------------|-------------|
| **Step 3 collection flow** | Single-phase: photo -> react -> advance | 2-phase: photo -> detail question -> verbal response -> advance | **Critical** |
| **Session state** | No phase tracking, no detail storage | `collection_phase`, `collected_details`, `collected_names` fields | **Critical** |
| **Turn handler** | Correct photo always advances step | Correct photo stays on step (Phase A); verbal response advances (Phase B) | **Critical** |
| **Step instructions (collect)** | "Do NOT ask text questions during collection" | Must ask detail-harvesting questions per round | **High** |
| **Step instructions (synthesis)** | Names/details created fresh at synthesis | Names/details already exist from collection; synthesis = story/sort | **High** |
| **Frontend photo gallery** | Shown for all STEP_3_COLLECT_ turns | Should only show in Phase A (photo); Phase B shows collected photo | **High** |
| **Creative slots schema** | Has `naming_prompt` but no `detail_question_template` or `sorting_criterion` | Needs per-scenario detail question and sorting criterion | **Medium** |
| **Script system prompt** | T0=0 concepts, T1=1 concept in closing | tier_rules.yaml says T0=1, T1=2, T2=3 | **Medium** |
| **Step 1 (hook)** | Generic first-turn/conversation variants | Explicit warm start vs cold start | **Low** |
| **Step 2 (mission)** | States criterion + count | 3-part mission (Find -> Name/Compare -> Synthesis) + role assignment | **Low** |
| **Step 5 (celebrate)** | Praise + badge | + reflective "WHY" question | **Low** |
| **Screen frames** | Always `progress_tracker` during collection | Phase B should show `photo_display` of just-collected item | **Medium** |

---

## Implementation Plan

### Phase 1: Schema & State Changes (no behavior change)

**1.1 Add phase tracking to `SessionStateModel`**
- File: `backend/schemas/session_state.py`
- Add fields:
  ```python
  collection_phase: Literal["photo", "detail"] = "photo"
  collected_details: list[str] = Field(default_factory=list)
  collected_names: list[str] = Field(default_factory=list)
  ```

**1.2 Add new fields to `Cat5CreativeSlots`**
- File: `backend/schemas/creative_slots.py`
- Add optional fields with defaults (backward-compatible):
  ```python
  detail_question_template: str = Field(default="", description="Detail-harvesting question template for each find")
  sorting_criterion: str = Field(default="", description="For comparison_chart: criterion to sort by in synthesis")
  ```

**1.3 Update existing game MD files with new creative slot fields**
- Files: `backend/games/polka_dot_patrol.md`, `backend/games/fluffy_expedition_dandelion.md`
- Add `detail_question_template` and `sorting_criterion` to YAML frontmatter

---

### Phase 2: Turn Handler Logic (core 2-phase loop)

**2.1 Modify collection flow in `turn_handler.py`**
- File: `backend/turn_handler.py`

The key changes in `resolve_turn()`:

**Section 4 (photo validation, ~line 368-376):** After `_record_correct_collection_pick`, set `collection_phase = "detail"`. This signals that the AI should ask a detail question instead of advancing.

**New branch before section 7c (~line 465):** Handle Phase B (detail response):
```
If current_step is STEP_3_COLLECT_* AND collection_phase == "detail" AND (text input or silence):
  1. Record detail in state.collected_details
  2. Reset collection_phase = "photo"
  3. Generate response (AI processes detail, names character or acknowledges observation)
  4. If remaining_count > 0: advance to next STEP_3_COLLECT_N
  5. If remaining_count == 0: advance past collection to synthesis
```

**Section 7c existing logic (~line 525-527):** When `stay_on_step=false` after a correct photo in Phase A, DON'T advance step. The LLM should set `stay_on_step=true` because step instructions tell it to ask the detail question. But add a guardrail: if collection_phase just became "detail", force `stay_on_step=true`.

**Override logic (~line 517-523):** The "force advancement when collection complete" override should only trigger in Phase B, not Phase A. After the last correct photo, AI still needs to ask the detail question first.

---

### Phase 3: Step Instruction Updates

**3.1 `cat5_step3_collect.md` — Major rewrite**
- File: `backend/skills/step_instructions/cat5_step3_collect.md`
- Remove: "Do NOT ask questions needing text answers" prohibition
- Add: 2-phase loop documentation with `{collection_phase}` variable
- Phase A rules: validate photo, celebrate, ask `{detail_question_template}`, set `stay_on_step: true`
- Phase B rules: process child's verbal detail, naming/observation, decide advancement

**3.2 `cat5_step3_collect__naming_story.md` — Rewrite**
- File: `backend/skills/step_instructions/cat5_step3_collect__naming_story.md`
- Remove: "Do NOT ask child to name item now"
- Add: Phase A asks "What does it remind you of?" after correct photo
- Add: Phase B generates character name from child's detail (detail -> name formula)
- Add: 3 response branches (ideal/unexpected/no response) for detail question

**3.3 `cat5_step3_collect__comparison_chart.md` — Rewrite**
- File: `backend/skills/step_instructions/cat5_step3_collect__comparison_chart.md`
- Remove: "Do NOT ask child to describe or name item now"
- Add: Phase A asks about observation_angle differences after correct photo
- Add: Phase B acknowledges observation, connects to previous finds
- Add: 3 response branches

**3.4 `cat5_step4_synthesis__naming_story.md` — Update**
- File: `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md`
- Update: Characters already named during collection (available via `{collected_names}`)
- Change: Synthesis is now story co-creation using existing named characters, not fresh naming

**3.5 `cat5_step4_synthesis__comparison_chart.md` — Update**
- File: `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md`
- Add: Sorting by `{sorting_criterion}` as the synthesis activity
- Update: Observations already captured during collection (available via `{collected_details}`)

**3.6 `cat5_step1_hook.md` — Minor update**
- File: `backend/skills/step_instructions/cat5_step1_hook.md`
- Add: Warm start vs Cold start terminology (aligned with new design docs)

**3.7 `cat5_step2_mission.md` — Minor update**
- File: `backend/skills/step_instructions/cat5_step2_mission.md`
- Add: 3-part mission statement pattern (Find -> Name/Compare -> Synthesis)
- Add: Metaphorical role assignment emphasis

**3.8 `cat5_step5_celebrate.md` — Minor update**
- File: `backend/skills/step_instructions/cat5_step5_celebrate.md`
- Add: Reflective "WHY" question connecting findings to IB concepts

---

### Phase 4: Template Variable Injection

**4.1 Update script_agent.py template variables**
- File: `backend/agents/script_agent.py`
- Add to Cat5 replacements dict:
  - `{collection_phase}` -> `state.collection_phase`
  - `{detail_question_template}` -> `slots.detail_question_template`
  - `{sorting_criterion}` -> `slots.sorting_criterion`
  - `{collected_names}` -> comma-separated list from `state.collected_names`
  - `{collected_details}` -> semicolon-separated list from `state.collected_details`

---

### Phase 5: Agent Prompt Fix

**5.1 Fix concept count in `script_system.md`**
- File: `backend/prompts/script_system.md`
- Change T0 closing from "DO NOT name IB concepts" to "Name exactly 1 concept"
- Change T1 closing from "Name exactly 1 concept" to "Name exactly 2 concepts"
- Align with `tier_rules.yaml` (T0=1, T1=2, T2=3)

---

### Phase 6: Frontend Updates

**6.1 Gate photo gallery on collection_phase**
- File: `frontend/src/App.jsx`
- Change `showPhotoGallery` condition to include `&& sessionState?.collection_phase !== 'detail'`
- During Phase B, show the DeviceScreen widget (progress tracker or photo display) instead of photo picker

**6.2 Expose new state fields in API response**
- File: `backend/server.py`
- In `_session_state_dict()`, add:
  - `collection_phase`
  - `collected_names`
  - `collected_details`

---

### Phase 7: Screen Frame Updates

**7.1 Update `state_machine.py` for Phase B display**
- File: `backend/state_machine.py`
- For `STEP_3_COLLECT_*` + `collection_phase == "detail"`: return `photo_display` widget showing the just-collected photo instead of `progress_tracker`
- Update `_state_context` to pass `collection_phase`

---

## Files to Modify (ordered by implementation sequence)

1. `backend/schemas/session_state.py` — add 3 new fields
2. `backend/schemas/creative_slots.py` — add 2 new fields
3. `backend/games/polka_dot_patrol.md` — add creative slot values
4. `backend/games/fluffy_expedition_dandelion.md` — add creative slot values
5. `backend/turn_handler.py` — 2-phase collection logic (core change)
6. `backend/agents/script_agent.py` — template variable injection
7. `backend/skills/step_instructions/cat5_step3_collect.md` — major rewrite
8. `backend/skills/step_instructions/cat5_step3_collect__naming_story.md` — rewrite
9. `backend/skills/step_instructions/cat5_step3_collect__comparison_chart.md` — rewrite
10. `backend/skills/step_instructions/cat5_step4_synthesis.md` — update
11. `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — update
12. `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md` — update
13. `backend/skills/step_instructions/cat5_step1_hook.md` — minor update
14. `backend/skills/step_instructions/cat5_step2_mission.md` — minor update
15. `backend/skills/step_instructions/cat5_step5_celebrate.md` — minor update
16. `backend/prompts/script_system.md` — concept count fix
17. `backend/server.py` — expose new state fields
18. `backend/state_machine.py` — Phase B screen frame
19. `frontend/src/App.jsx` — photo gallery phase gating

## Verification

1. **Lint/format**: `cd backend && uv run ruff check . && uv run ruff format . && uv run mypy .`
2. **Unit tests**: `cd backend && uv run pytest` — existing tests should still pass
3. **Manual test (naming_story)**: Start `fluffy_expedition_dandelion` session, verify:
   - After correct photo: AI asks "What does it remind you of?" and photo gallery hides
   - After verbal response: AI generates character name, photo gallery reappears for next round
   - At synthesis: AI references named characters, invites story co-creation
4. **Manual test (comparison_chart)**: Start `polka_dot_patrol` session, verify:
   - After correct photo: AI asks about pattern differences and photo gallery hides
   - After verbal response: AI acknowledges observation, photo gallery reappears
   - At synthesis: AI references collected observations, guides sorting
5. **Edge cases**: Test silence during Phase B, wrong photo during Phase A, consecutive silence exit
