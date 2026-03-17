# Plan: Instruction-Based Recipe System

## Context

The current recipe system has two problems:
1. **Static dialogue** — Pre-generated recipes contain exact sentences. If a child says something unexpected, they get a canned response that doesn't acknowledge what they said.
2. **Directive tone** — Prompts say "Tell me!" / "Go find!" instead of inviting the child gently. Different tiers should use different invitational expressions.

This plan converts recipes from fixed dialogue scripts to **instruction documents** (goal + constraints per step). Every turn calls the Script Agent LLM, which generates contextual, invitational, emotion-tagged responses guided by the recipe instructions.

## Requirements Summary

1. **Instruction-based recipes** — Steps contain goals + constraints, not exact sentences
2. **Invitational language** — "Would you like to...?" not "Go find!" — tier-appropriate
3. **Feature validation** — Only ask about features visible in the photo (Cat1) or present in collection items (Cat5)
4. **Inline emotion tags** — `[exciting] You found it!` sent directly to Gemini TTS
5. **Age-tier appropriate** — Follow tier_rules.yaml guidance per tier
6. **Real invitation at STEP_2** — Wait for child's response; decline → re-invite once → decline again → graceful exit
7. **LLM judges decline intent** — No keyword matching; Script Agent determines if child accepted/declined

## Architecture Changes

### 1. New Schema: `StepInstruction` (new file)

**File:** `backend/schemas/step_instruction.py`

```python
class RoundInstruction(BaseModel):
    round_number: int
    goal: str              # "explore how the dog feels about warm sunshine"
    scenario: str          # "warm sunshine on belly"
    constraint: str        # "T0 max 2 sentences, invitational tone"
    emotion_tag: str       # "warm"
    acceptable_themes: list[str]  # ["happy", "cozy", "warm"] — loose validation
    escalation_note: str   # "comfortable, familiar scenario"

class StepInstruction(BaseModel):
    hook: StepGoal         # goal, constraint, emotion_tag
    transition: StepGoal   # invitation to play
    rounds: list[RoundInstruction]
    celebrate: StepGoal
    closing: StepGoal
    synthesis: StepGoal | None = None  # Cat5 only
    early_exit: StepGoal

class StepGoal(BaseModel):
    goal: str
    constraint: str
    emotion_tag: str
```

### 2. New Recipe Format: `InstructionRecipe`

**File:** `backend/schemas/recipe.py` (modify)

Add `InstructionRecipe` model:
```python
class InstructionRecipe(BaseModel):
    activity_type: str
    step_instructions: StepInstruction
    screen_frames: list[ScreenFrame]
    celebration_frame: ScreenFrame | None = None
    metadata: RecipeMetadata
    photo_features: list[str] = []      # Cat1 feature anchors
    collection_items: dict = {}          # Cat5 item metadata
```

### 3. Convert Recipe JSON Files

**Files:** `backend/recipes/*.json` (all 5)

Convert from exact dialogue to instructions. Example `mood_changer_dog.json` round:
```json
{
  "round_number": 1,
  "goal": "Explore how the dog feels about warm sunshine on its belly",
  "scenario": "warm sunshine on belly",
  "constraint": "T0 max 2 sentences, invitational phrasing",
  "emotion_tag": "warm",
  "acceptable_themes": ["happy", "cozy", "warm", "comfy", "nice"],
  "escalation_note": "comfortable, familiar — easiest round"
}
```

Keep `screen_frames`, `celebration_frame`, `metadata` unchanged.

### 4. TurnResponse: Add `child_intent` Field

**File:** `backend/schemas/turn_response.py` (modify)

Add optional field for STEP_2 invitation handling:
```python
child_intent: str | None = None  # "accepted" | "declined" | "off_topic" | None
```

The Script Agent outputs this at STEP_2 to tell the server whether the child accepted the invitation. Server logic:
- `accepted` or `off_topic` → advance to STEP_3_ROUND_1
- `declined` + first decline → stay at STEP_2, set `invitation_decline_count += 1`
- `declined` + second decline → EARLY_EXIT

### 5. SessionStateModel Changes

**File:** `backend/schemas/session_state.py` (modify)

- Remove: `is_pregenerated: bool`, `recipe: ActivityRecipe | None`
- Add: `instruction_recipe: InstructionRecipe | None`, `invitation_decline_count: int = 0`

### 6. Script Agent: Merge Recipe Instructions into Prompt

**File:** `backend/agents/script_agent.py` (modify)

Modify `_load_step_instructions()`:
- After loading the generic step template from `.md`, append activity-specific overlay from `state.instruction_recipe.step_instructions`
- Map current step to the right `StepGoal` or `RoundInstruction`
- Format as:
  ```
  ### Activity-Specific Instructions:
  Goal: {goal}
  Constraint: {constraint}
  Suggested emotion tag: [{emotion_tag}]
  Acceptable themes: {themes}  (for rounds only)
  ```

Modify `_build_system_prompt()`:
- Inject `photo_features` as a new Section 5.5: "Feature Anchors"

### 7. System Prompt Updates

**File:** `backend/skills/script_turn.md` (modify)

**Section 6 (Output Rules)** — Change emotion format:
```
- `dialogue`: MUST start with emotion tag in brackets, e.g. "[excited] Wow!".
  Valid: [exciting], [gentle], [curious], [warm], [proud], [playful],
  [mysterious], [encouraging], [impressed], [celebrating], [adventurous], [surprised]
- `child_intent`: (STEP_2 only) One of: "accepted", "declined", "off_topic", or null
```

**New Section 5.5** — Feature Anchors:
```
### Photo Feature Anchors:
Only reference these visible features: {photo_features}
Do NOT invent features not in this list.
```

**Add invitational rules** to Section 2 (injected via tier constraints):
```
Invitational patterns: "Would you like to...?", "I wonder...?", "What do you think...?"
FORBIDDEN directives: "Go find!", "Now let's...", "Look for...", "Tell me!"
```

### 8. Step Instruction Files: Add Invitation Handling

**File:** `backend/skills/step_instructions/cat1_step2_rules.md` (modify)

Add invitation-and-wait behavior:
```
### Invitation (NON-NEGOTIABLE):
- End with a genuine invitation: "Would you like to try?" — then WAIT.
- Do NOT auto-start the game. The child must accept first.
- If the child previously declined (check conversation history), gently re-invite
  with different wording. Do NOT repeat the same invitation.
- Set `child_intent` in your response to indicate what the child said.
```

Same change for `cat5_step2_mission.md`.

### 9. Tier Rules: Add Invitational Patterns

**File:** `backend/tier_rules.yaml` (modify)

Add per-tier:
```yaml
invitational_patterns:
  - "Would you like to imagine...?"  # T0
  - "I wonder what would happen if...?"  # T1
  - "What do you think about...?"  # T2
forbidden_directives:
  - "Go find!"
  - "Now let's..."
  - "Look for..."
  - "Tell me!"
```

Update `_load_tier_constraints()` in `script_agent.py` to format these new fields.

### 10. Server: Unify Turn Handling

**File:** `backend/server.py` (modify)

**`/api/turn` endpoint:**
- Remove all `if state.is_pregenerated:` branching
- Always call `_generate_turn_with_retry(script_agent, state)`
- After Script Agent response, check `child_intent`:
  - If step is STEP_2 and `child_intent == "declined"`:
    - Increment `state.invitation_decline_count`
    - If count >= 2 → set step to EARLY_EXIT
    - Else → stay at STEP_2 (don't advance)
  - Otherwise → normal state machine advancement

**`/api/start` endpoint (demo entities):**
- Load `InstructionRecipe` instead of `ActivityRecipe`
- Store in `state.instruction_recipe`
- Call Script Agent for hook turn (adds ~200-400ms to demo start)
- Keep visual frames from recipe

### 11. Recipe Loader: Simplify

**File:** `backend/recipe_loader.py` (major rewrite)

Remove:
- `resolve_turn_from_recipe()` (~140 lines)
- `resolve_wrong_photo_turn()` (~35 lines)
- `_select_acknowledgment()` (~15 lines)
- `_select_round_transition_ack()` (~5 lines)

Keep and modify:
- `is_demo_entity()` — unchanged
- `load_demo_recipe()` → rename to `load_instruction_recipe()`, return `InstructionRecipe`
- `recipe_to_session_state()` → simplify: build state with instruction_recipe, no first turn generation

### 12. Emotion Tag Fallback

**File:** `backend/agents/script_agent.py` (modify `generate_turn`)

After parsing LLM response, validate emotion tag:
```python
import re
if not re.match(r'^\[.+?\] ', turn.dialogue):
    # Prepend suggested tag from recipe instructions
    suggested = _get_suggested_emotion_tag(state)
    turn.dialogue = f"[{suggested}] {turn.dialogue}"
```

### 13. TTS: Pass-Through

**File:** `backend/tts.py` — No changes needed.

Gemini TTS receives `[excited] You found it!` directly. The bracket tag acts as a speech directive.

## Implementation Order

### Phase 1: Schema + Recipe Conversion (no behavior change)
1. Create `backend/schemas/step_instruction.py`
2. Add `InstructionRecipe` to `backend/schemas/recipe.py`
3. Add `child_intent` to `TurnResponse`
4. Add `instruction_recipe`, `invitation_decline_count` to `SessionStateModel`; remove `is_pregenerated`, `recipe`
5. Add invitational patterns to `backend/tier_rules.yaml`
6. Convert all 5 recipe JSONs to instruction format

### Phase 2: Script Agent + Prompt Updates
7. Update `backend/skills/script_turn.md` — emotion tags, feature anchors, invitational rules
8. Update step instruction `.md` files — invitation handling at STEP_2
9. Modify `_load_step_instructions()` — overlay recipe-specific instructions
10. Modify `_build_system_prompt()` — inject photo_features
11. Modify `_load_tier_constraints()` — format invitational patterns
12. Add emotion tag fallback in `generate_turn()`

### Phase 3: Server Unification
13. Modify `recipe_loader.py` — remove dialogue lookup, rename to instruction loading
14. Modify `/api/start` — demo entities use instruction recipe + Script Agent for hook
15. Modify `/api/turn` — remove `is_pregenerated` branching, add invitation decline logic
16. Modify `/api/turn-speak` — same unification

### Phase 4: Validation
17. Test all 5 demo entities end-to-end
18. Test custom photo upload (should still work via live pipeline)
19. Test invitation decline flow (decline once → re-invite → decline again → exit)
20. Verify emotion tags in TTS output
21. Verify invitational language (no directives)
22. Run `uv run ruff check .` and `uv run ruff format .`
23. Run `uv run mypy .`

## Critical Files

| File | Action |
|------|--------|
| `backend/schemas/step_instruction.py` | CREATE |
| `backend/schemas/recipe.py` | MODIFY — add InstructionRecipe |
| `backend/schemas/turn_response.py` | MODIFY — add child_intent |
| `backend/schemas/session_state.py` | MODIFY — swap recipe fields |
| `backend/recipes/*.json` (5 files) | REWRITE — dialogue → instructions |
| `backend/agents/script_agent.py` | MODIFY — instruction overlay, emotion fallback |
| `backend/skills/script_turn.md` | MODIFY — emotion tags, feature anchors, invitational |
| `backend/skills/step_instructions/cat1_step2_rules.md` | MODIFY — invitation handling |
| `backend/skills/step_instructions/cat5_step2_mission.md` | MODIFY — invitation handling |
| `backend/tier_rules.yaml` | MODIFY — invitational patterns |
| `backend/recipe_loader.py` | MAJOR REWRITE — remove dialogue lookup |
| `backend/server.py` | MODIFY — unify turn handling, invitation logic |

## Verification

1. Start backend: `cd backend && uv run uvicorn server:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173`
4. Test each demo entity (dog, cat, dinosaur, ladybug, dandelion):
   - Verify emotion tags appear in dialogue: `[excited] Oh wow...`
   - Verify invitational language at STEP_2: "Would you like to...?"
   - Verify contextual responses to child input
   - Verify feature anchors respected (no invented features)
5. Test invitation decline: at STEP_2, say "no" → should re-invite; say "no" again → graceful exit
6. Test custom photo: upload a non-demo photo → should use same unified pipeline
7. Verify TTS plays with emotion (listen for prosody changes)
8. Code quality: `uv run ruff check . && uv run ruff format . && uv run mypy .`
