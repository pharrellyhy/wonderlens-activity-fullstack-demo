# Two-Pass Generation (Planner + Speaker) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single Script Agent LLM call with two sequential calls — a Planner that outputs structured JSON (what to say, what to reference, what to avoid) and a Speaker that generates natural dialogue from the plan — so structural decisions and creative language are handled by separate, focused calls.

**Architecture:** The Planner LLM sees full context (conversation history, state, child's words, collected characters) and outputs a structured `TurnPlan` JSON describing what the response should contain (items to celebrate, question type, characters to reference, things to avoid). The Speaker LLM sees only the plan + tier info and generates warm, natural dialogue. Both use the same Qwen 3.5+ model via DashScope. Post-processing validation runs on the Speaker's output as before.

**Tech Stack:** Python 3.12+, Pydantic v2, AsyncOpenAI (DashScope), Qwen 3.5+, JSON mode

---

## Why Two Passes

The current single-call approach asks the LLM to simultaneously:
1. Understand the child's input and emotional state
2. Make structural decisions (what type of question, whether to suggest items)
3. Track progress and reference previous characters
4. Generate warm, age-appropriate language
5. Avoid forbidden patterns
6. Output valid JSON with screen/audio directives

This produces responses where the LLM gets the language right but the structure wrong (suggesting specific items, asking wrong question types, repeating patterns). Splitting into Planner + Speaker means:
- **Planner** focuses on decisions 1-3 and 5 — outputs a structured intent
- **Speaker** focuses on decision 4 — just makes the plan sound natural
- Decision 6 (JSON format) is handled by both (planner outputs plan JSON, speaker outputs turn JSON)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/schemas/turn_plan.py` | Create | `TurnPlan` Pydantic schema — planner output |
| `backend/agents/planner.py` | Create | Planner agent — builds plan from state + context |
| `backend/skills/planner_system.md` | Create | Planner system prompt template |
| `backend/skills/speaker_system.md` | Create | Speaker system prompt (simple — just "say this warmly") |
| `backend/agents/script_agent.py` | Modify | `generate_turn()` calls planner then speaker sequentially |
| `backend/turn_handler.py` | Modify | Pass plan to validation for better error messages |
| `backend/config.py` | Modify | Add planner-specific settings (max_tokens, temperature) |
| `tests/test_turn_plan.py` | Create | Unit tests for TurnPlan schema |
| `tests/test_planner.py` | Create | Unit tests for planner prompt building |

## TurnPlan Schema

The Planner outputs this structured JSON:

```python
class TurnPlan(BaseModel):
    """Structured plan for what the AI response should contain."""

    # What to respond to
    child_said: str = Field(description="Summary of what the child said/did this turn")
    child_emotion: str = Field(description="Detected emotion: excited, confused, silent, disengaged, neutral")

    # Content decisions
    celebrate_item: str | None = Field(default=None, description="Item name to celebrate (if correct photo)")
    progress_note: str | None = Field(default=None, description="How to mention progress — varies each round")
    sensory_observation: str | None = Field(default=None, description="What YOU notice about the item (how it feels/looks/sounds)")
    name_choices: list[str] = Field(default_factory=list, description="2 character name suggestions based on sensory_observation")
    characters_to_reference: list[str] = Field(default_factory=list, description="Previous character names to mention")
    question_type: str | None = Field(default=None, description="tactile, visual, comparison, binary_choice, open_guided, none")
    story_beat: str | None = Field(default=None, description="For synthesis: the story content to deliver")

    # Constraints
    must_model_first: bool = Field(default=False, description="T0: must demonstrate before asking")
    offer_binary_choice: bool = Field(default=False, description="T0: offer A or B, not open question")
    do_not_suggest_items: bool = Field(default=True, description="Never name specific items child should find")
    do_not_ask_question: bool = Field(default=False, description="Final find or closing — end with statement")
    stay_on_step: bool = Field(default=False, description="Whether to stay on current step")

    # Tone and format
    emotion_tag: str = Field(default="excited", description="Emotion tag for the response")
    tone_guidance: str = Field(default="", description="Brief tone direction: warm, gentle, celebrating, etc.")
    max_sentences: int = Field(default=2, description="Maximum sentences for the response")

    # Screen/audio (pass-through to TurnResponse)
    screen_widget: str = Field(default="photo_display")
    screen_widget_params: dict = Field(default_factory=dict)
    screen_animation: str | None = Field(default=None)
    sfx_cue: str | None = Field(default=None)
    child_intent: str | None = Field(default=None)
```

## Planner System Prompt

The Planner sees full context and outputs TurnPlan. Its prompt is focused on **decisions**, not language:

```markdown
You are a dialogue planner for a children's exploration app. You decide WHAT the AI should say, not HOW.

Given the child's input, conversation history, and game state, output a structured plan.

## Key Rules
- NEVER include specific item suggestions (blanket, sock, teddy). You cannot see the child's environment.
- For T0 (ages 2-4): always set must_model_first=true and offer_binary_choice=true.
- For the final find (remaining=0): set do_not_ask_question=true.
- sensory_observation must describe THIS SPECIFIC item (from the child's message), not a generic comparison.
- name_choices must derive from the sensory_observation, not random words.
- Vary progress_note each round — don't always use "X out of Y".
- characters_to_reference must include ALL previously named characters.

## Current State
{state_context}

## Conversation History
{conversation_history}

Output valid JSON matching the TurnPlan schema.
```

## Speaker System Prompt

The Speaker sees only the plan and tier. Its prompt is minimal:

```markdown
You are Zigzag, a warm AI companion for young children. Generate a single dialogue response based on the plan below.

Tier: {tier} ({tier_label}, ages {tier_ages})
Sentences: max {max_sentences}, ~{words_per_sentence} words each.

## Plan
{turn_plan_json}

## Rules
- Start with [{emotion_tag}] emotion tag.
- Follow the plan exactly — do not add content that isn't in the plan.
- If do_not_suggest_items is true: never name specific objects the child should find.
- If do_not_ask_question is true: end with a statement, not a question.
- If must_model_first is true: say what YOU think first, then offer the choice.
- If offer_binary_choice is true and name_choices has 2 items: offer "{name_choices[0]} or {name_choices[1]}?"
- Use warm, playful language appropriate for the tier.

Output valid JSON: {"dialogue": "[emotion_tag] Your text here", "tone_marker": "..."}
```

## Integration: How generate_turn() Changes

```python
async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
    # Step 1: Planner call
    plan = await self._plan_turn(state)

    # Step 2: Speaker call
    turn = await self._speak_turn(state, plan)

    # Merge plan's screen/audio decisions into turn response
    turn.screen_widget = plan.screen_widget
    turn.screen_widget_params = plan.screen_widget_params
    turn.screen_animation = plan.screen_animation
    turn.sfx_cue = plan.sfx_cue
    turn.child_intent = plan.child_intent
    turn.stay_on_step = plan.stay_on_step

    return turn
```

---

## Tasks

### Task 1: Create TurnPlan schema

**Files:**
- Create: `backend/schemas/turn_plan.py`
- Test: `tests/test_turn_plan.py`

- [ ] **Step 1: Create the TurnPlan Pydantic model**

The schema as defined above. Keep it in its own file for clarity.

- [ ] **Step 2: Write basic validation tests**

Test that TurnPlan can be constructed with defaults, with full data, and validates field constraints.

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_turn_plan.py -v`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(schemas): add TurnPlan schema for planner output"
```

---

### Task 2: Create Planner agent

**Files:**
- Create: `backend/agents/planner.py`
- Create: `backend/skills/planner_system.md`
- Test: `tests/test_planner.py`

- [ ] **Step 1: Write the planner system prompt template**

Save to `backend/skills/planner_system.md`. The prompt focuses on decision-making, not language. Include:
- State context injection points ({state_context}, {conversation_history})
- The key rules (no specific items, T0 scaffolding, progress variation)
- The TurnPlan JSON schema for output

- [ ] **Step 2: Write the Planner class**

```python
class Planner:
    async def plan_turn(self, state: SessionStateModel) -> TurnPlan:
        system_prompt = self._build_planner_prompt(state)
        user_prompt = self._build_planner_user_prompt(state)
        # Call LLM with JSON mode
        # Parse response to TurnPlan
        return plan
```

The planner prompt injects:
- Current step, phase, round, tier
- Collected characters and details
- Remaining count
- Conversation history (last 6 turns)
- Child's latest input
- Game-specific context (observation_angle, collection_criterion, entity_name)

- [ ] **Step 3: Write unit tests**

Test `_build_planner_prompt()` produces valid prompt with all state variables filled. Test plan parsing from mock JSON.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_planner.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(agents): add Planner agent for structured turn planning"
```

---

### Task 3: Create Speaker prompt

**Files:**
- Create: `backend/skills/speaker_system.md`

- [ ] **Step 1: Write the speaker system prompt**

Minimal prompt — the Speaker's only job is generating warm, natural dialogue from the plan. It does NOT see step instructions, structural rules, or game examples. It sees:
- The TurnPlan JSON
- Tier info (label, ages, max sentences, words per sentence)
- Output format (JSON with dialogue and tone_marker)

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(skills): add speaker system prompt for plan-to-dialogue"
```

---

### Task 4: Integrate Planner + Speaker into ScriptAgent

**Files:**
- Modify: `backend/agents/script_agent.py`
- Modify: `backend/config.py`

- [ ] **Step 1: Add planner config settings**

Add to `Settings` in config.py:
```python
planner_max_tokens: int = 400
planner_temperature: float = 0.3  # Lower temperature for more consistent decisions
speaker_temperature: float = 0.7  # Higher for natural language variety
```

- [ ] **Step 2: Add `_plan_turn()` method to ScriptAgent**

Calls the Planner with full state context, returns TurnPlan.

- [ ] **Step 3: Add `_speak_turn()` method to ScriptAgent**

Takes state + TurnPlan, builds a minimal speaker prompt, calls LLM, returns TurnResponse with just `dialogue` and `tone_marker`.

- [ ] **Step 4: Modify `generate_turn()` to use both**

```python
async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
    plan = await self._plan_turn(state)
    turn = await self._speak_turn(state, plan)
    # Merge plan's screen/audio/state decisions
    turn.screen_widget = plan.screen_widget
    turn.screen_widget_params = plan.screen_widget_params
    turn.screen_animation = plan.screen_animation
    turn.sfx_cue = plan.sfx_cue
    turn.child_intent = plan.child_intent
    turn.stay_on_step = plan.stay_on_step
    return turn
```

- [ ] **Step 5: Keep old single-call path as fallback**

If planner call fails, fall back to the existing single-call `generate_turn()` path. This ensures the system doesn't break during rollout.

- [ ] **Step 6: Run existing tests**

Run: `uv run pytest tests/test_turn_handler.py -q`

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(script-agent): integrate planner + speaker two-pass generation"
```

---

### Task 5: Update validation for plan-aware checking

**Files:**
- Modify: `backend/turn_handler.py`

- [ ] **Step 1: Log the TurnPlan alongside the TurnResponse**

When validation fails, log both the plan and the response so we can see whether the planner or speaker is at fault.

- [ ] **Step 2: Add plan-based validation**

Before running existing post-processing validation on the Speaker's output, validate the plan itself:
- If `do_not_suggest_items` is true but the dialogue mentions specific items → planner was right, speaker violated → retry speaker only
- If plan has empty `sensory_observation` for a correct-photo step → planner failed → retry both

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_turn_handler.py -q`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(validation): plan-aware validation and retry logic"
```

---

### Task 6: Update streaming path

**Files:**
- Modify: `backend/agents/script_agent.py`

- [ ] **Step 1: Update `generate_turn_streaming()`**

The streaming path needs to:
1. Call planner (non-streaming — it's a small JSON output)
2. Call speaker with streaming enabled
3. Extract dialogue tokens for early TTS delivery

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(script-agent): two-pass generation for streaming path"
```

---

### Task 7: End-to-end testing and HANDOFF.md

**Files:**
- Modify: `HANDOFF.md`

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py`

- [ ] **Step 2: Start backend and test manually**

Run: `uv run python scripts/run_dandelion_scenarios.py`
Verify: all scenarios pass, responses are themed correctly, no specific item suggestions.

- [ ] **Step 3: Check latency**

Compare turn latency before/after. Expected: +100-200ms for planner call, similar or lower for speaker (simpler prompt).

- [ ] **Step 4: Update HANDOFF.md**

- [ ] **Step 5: Commit**

```bash
git commit -m "docs: update HANDOFF.md for two-pass generation"
```

---

## Verification

1. `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py` — all pass
2. `uv run ruff check . && uv run ruff format --check .` — clean
3. Start backend, run `uv run python scripts/run_dandelion_scenarios.py` — all 6 dandelion scenarios pass
4. Manual test: start fluffy_expedition_dandelion session
   - Verify: no specific item suggestions in collection prompts
   - Verify: detail questions connect to the actual item found
   - Verify: progress phrasing varies between rounds
   - Verify: synthesis has problem→resolution arc
   - Verify: celebrate and closing are distinct
5. Latency check: compare `/api/turn` response times before/after (~500ms → ~700ms expected)
6. Check server logs for both planner and speaker call durations
