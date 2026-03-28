# Plan: Story Synthesis Loop Redesign

## Context

The Cat5 synthesis step (STEP_4_SYNTHESIS) currently produces poor-quality "stories" — typically 1-3 disjointed sentences that lack narrative structure. The step tries to do too much in 2 turns across 3 synthesis types (naming_story, comparison_chart, sorting_game), resulting in rushed, incoherent output like:

> "[dreamy] Mossy, Bunny Fluff, and Woolly found one tiny seed to share. Should they break it into pieces or take turns holding it?"

This redesign replaces all synthesis types with a single **story synthesis loop** that gives the child a chance to create their own story, with AI fallback when needed. The approach uses explicit state-machine sub-phases for predictable flow.

## Design Decisions

- **Approach:** State-machine sub-steps (phases within STEP_4_SYNTHESIS)
- **Scope:** Replaces ALL synthesis types (naming_story, comparison_chart, sorting_game)
- **Story content:** Must use all collected characters/items by name
- **Improvement strategy:** Tier-dependent — T0: AI expands; T1/T2: prompt child once to elaborate
- **Story length:** T0: 7-8 sentences, T1: 9-11 sentences, T2: 12-14 sentences
- **AI story delivery:** Single turn (complete story in one response)
- **Max re-prompts:** 2 (if child gives unrelated responses twice, AI generates)

## Phase Flow

```
INVITE ──child responds──► EVALUATE
                              │
            ┌─────────────────┼──────────────────┐
            ▼                 ▼                  ▼
     (a) Story attempt   (b) Decline/        (c) Not a story
            │              "you tell it"          │
            ▼                 │            prompt_count < 2?
    Quality check             │           ┌──yes──┤──no──┐
     ┌──good──┤──weak──┐      │           ▼       │      ▼
     ▼        ▼        ▼      │      Re-INVITE    │  GENERATE
   Done    T0: GEN   T1/T2:  │                    │
  (advance) (expand)  IMPROVE ▼                   │
                        │   GENERATE ◄─────────────┘
                   child adds?
                    ┌yes──┤──no/weak┐
                    ▼              ▼
                  Done          GENERATE
                (advance)     (AI completes)
```

After GENERATE or Done, advance to STEP_5_CELEBRATE.

## Implementation Steps

### Step 1: Add session state fields

**File:** `backend/schemas/session_state.py`

Add three fields to `SessionStateModel`:
```python
synthesis_phase: str = Field(default="invite", description="Story loop phase: invite, evaluate, improve, generate")
synthesis_prompt_count: int = Field(default=0, description="Times child has been asked to try making a story (max 2)")
synthesis_child_story: str = Field(default="", description="Child's story attempt, stored for improvement/expansion")
```

### Step 2: Write new synthesis step instructions

**Delete:**
- `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md`
- `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md`
- `backend/skills/step_instructions/cat5_step4_synthesis__sorting_game.md`

**Rewrite:** `backend/skills/step_instructions/cat5_step4_synthesis.md`
- Phase-aware instructions: invite, improve, generate
- Each phase has its own goal, constraints, and output format
- Invite phase: ask child to make up a story about their collected characters using invitational language ("Would you like to...?")
- Improve phase (T1/T2): ask one guiding question to help child elaborate ("What happened next?" / "How did [character] feel?")
- Generate phase: produce a complete story using collected characters, a random theme from _SYNTHESIS_HINTS, with tier-appropriate length

**New:** `backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md`
- Detailed story generation prompt adapted from edu team reference (`tmp/story_gen_refer.py`)
- Story framework: Setup → Problem → Resolution
- Must use all collected character names and sensory details from `collected_details`
- Sensory/emotional richness: colors, textures, feelings
- Warm positive ending
- Length constraints by tier (T0: 7-8, T1: 9-11, T2: 12-14 sentences)
- Variety via theme injection (existing `_SYNTHESIS_HINTS`)
- No vulgar language, age-appropriate, invitational tone

### Step 3: Add response classification function

**File:** `backend/turn_handler.py`

Add `_classify_story_response()` function:
- Takes child's text + session state (collected names, activity context)
- Makes a lightweight LLM call with structured JSON output schema:
  ```python
  class StoryClassification(BaseModel):
      classification: Literal["story_attempt", "decline", "ask_ai", "unrelated"]
      is_related_to_collection: bool
      story_quality: Literal["good", "weak"] | None
  ```
- Classification rules:
  - `story_attempt`: Any narrative content about collected items
  - `decline`: "no", "I don't want to", negative response
  - `ask_ai`: "you tell me", "can you make one up?"
  - `unrelated`: Not story-like or not about collected items
- Quality: `good` = 2+ story elements (character+action, action+outcome); `weak` = single sentence, no progression
- Reuse existing LLM client setup from script_agent

### Step 4: Rewrite synthesis routing in turn_handler

**File:** `backend/turn_handler.py` (lines ~1024-1095)

Replace the current synthesis logic with phase-based routing:

```python
if state.current_step == "STEP_4_SYNTHESIS":
    phase = state.synthesis_phase

    if phase == "invite":
        # First visit: generate invitation prompt
        turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=True)
        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count += 1
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(...)  # auto_advance=False

    elif phase == "evaluate":
        classification = await _classify_story_response(state, child_text)

        if classification.classification == "story_attempt":
            state.synthesis_child_story = child_text
            if classification.story_quality == "good":
                # Celebrate the child's story, advance
                turn_response = await _generate_with_retry(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                _advance_state(state)  # → STEP_5_CELEBRATE
                return TurnResult(...)  # auto_advance=True
            elif state.tier == "T0":
                # T0: AI expands child's story seed
                state.synthesis_phase = "generate"
                turn_response = await _generate_with_retry(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                _advance_state(state)
                return TurnResult(...)
            else:
                # T1/T2: ask child to elaborate
                state.synthesis_phase = "improve"
                turn_response = await _generate_with_retry(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                return TurnResult(...)  # auto_advance=False

        elif classification.classification in ("decline", "ask_ai"):
            # AI generates full story
            state.synthesis_phase = "generate"
            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            _advance_state(state)
            return TurnResult(...)

        else:  # unrelated
            if state.synthesis_prompt_count < 2:
                # Re-invite
                turn_response = await _generate_with_retry(script_agent, state)
                state.synthesis_prompt_count += 1
                _append_ai_turn(state, turn_response.dialogue)
                return TurnResult(...)
            else:
                # Max prompts reached, AI generates
                state.synthesis_phase = "generate"
                turn_response = await _generate_with_retry(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                _advance_state(state)
                return TurnResult(...)

    elif phase == "improve":
        # Child's elaboration arrived — evaluate quality
        combined_story = f"{state.synthesis_child_story} {child_text}"
        classification = await _classify_story_response(state, combined_story)
        if classification.story_quality == "good":
            # Celebrate combined story
            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            _advance_state(state)
            return TurnResult(...)
        else:
            # AI completes the story based on child's seed
            state.synthesis_phase = "generate"
            state.synthesis_child_story = combined_story
            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            _advance_state(state)
            return TurnResult(...)

    elif phase == "generate":
        # Direct generation (shouldn't normally reach here as generate is handled inline)
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        _advance_state(state)
        return TurnResult(...)
```

### Step 5: Update script agent step instruction loading

**File:** `backend/agents/script_agent.py`

- Update `_load_step_instruction()` to handle the new synthesis phases:
  - When `synthesis_phase == "invite"`: load `cat5_step4_synthesis.md` with invite section
  - When `synthesis_phase == "improve"`: load `cat5_step4_synthesis.md` with improve section + child's story attempt
  - When `synthesis_phase == "generate"`: load `cat5_step4_synthesis__story_generation.md` with collected characters, details, and theme
- Remove `synthesis_type` branching logic (no more naming_story/comparison_chart/sorting_game)
- Keep `_SYNTHESIS_HINTS` for story theme variety
- Add new template variables: `{synthesis_phase}`, `{child_story_attempt}`, `{story_sentence_count}`

### Step 6: Update creative_slots schema

**File:** `backend/schemas/creative_slots.py`

- Remove `synthesis_type` from `Cat5CreativeSlots` (or mark as deprecated)
- This field is no longer needed since all synthesis is now story-based

### Step 7: Update game/scenario files

**Files:** `backend/games/*.md` that reference synthesis_type

- Remove or update `synthesis_type` references in game definitions
- Update synthesis goal descriptions to align with the new story loop

### Step 8: Add classification schema

**File:** `backend/schemas/story_classification.py` (new)

```python
class StoryClassification(BaseModel):
    classification: Literal["story_attempt", "decline", "ask_ai", "unrelated"]
    is_related_to_collection: bool
    story_quality: Literal["good", "weak"] | None = None
```

### Step 9: Update tests

**Files:** `backend/tests/test_turn_handler.py`, `backend/tests/test_ai_quality.py`

- Update synthesis-related tests for new phase-based flow
- Add tests for response classification
- Add tests for each phase transition
- Test tier-dependent behavior (T0 expand vs T1/T2 improve)
- Test max re-prompt limit (2 unrelated → AI generates)

## Files Summary

| File | Action |
|------|--------|
| `backend/schemas/session_state.py` | Add 3 fields |
| `backend/schemas/story_classification.py` | New schema |
| `backend/schemas/creative_slots.py` | Remove `synthesis_type` |
| `backend/turn_handler.py` | Rewrite synthesis routing + add `_classify_story_response()` |
| `backend/agents/script_agent.py` | Update step instruction loading, remove synthesis_type branching |
| `backend/skills/step_instructions/cat5_step4_synthesis.md` | Rewrite for phase-based instructions |
| `backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md` | New story generation prompt |
| `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` | Delete |
| `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md` | Delete |
| `backend/skills/step_instructions/cat5_step4_synthesis__sorting_game.md` | Delete |
| `backend/games/*.md` | Update synthesis_type references |
| `backend/tests/test_turn_handler.py` | Update synthesis tests |
| `backend/tests/test_ai_quality.py` | Update synthesis quality tests |

## Verification

1. **Unit tests:** `uv run pytest backend/tests/test_turn_handler.py -v` — verify phase transitions
2. **Lint/type check:** `uv run ruff check . && uv run mypy .`
3. **Manual E2E test:** Run the full Cat5 fluffy_expedition_dandelion flow through all synthesis scenarios:
   - Child tells a good story → accepted, advance
   - Child tells a weak story (T0) → AI expands
   - Child tells a weak story (T1) → AI asks to elaborate → child adds → accepted
   - Child declines → AI generates full story
   - Child gives unrelated response twice → AI generates
4. **Story quality check:** Verify AI-generated stories are 7-14 sentences, use collected names, have setup→problem→resolution structure
