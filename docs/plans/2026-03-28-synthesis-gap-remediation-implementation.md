# Story Synthesis Gap Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the remaining causes of weak Cat5 synthesis stories and binary/question-led synthesis prompts, and make future sessions debuggable from the active database.

**Architecture:** Keep the current phase-based `STEP_4_SYNTHESIS` state machine, but harden the layers around it. The work is split into four code paths: phase-aware validation, generate-phase prompt cleanup, synthesis-aware best-of-N scoring, and database-path/logging consistency. The implementation stays incremental and test-first so each behavior change is verified in isolation before moving on.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLite, pytest, Ruff

---

### Task 1: Lock In Regressions For The Live Synthesis Gaps

**Files:**
- Create: `tests/test_script_agent.py`
- Modify: `tests/test_scoring.py`
- Modify: `tests/test_entity_registry.py`
- Modify: `tests/test_turn_handler.py`

**Step 1: Write the failing tests**

Add these tests before touching implementation:

```python
def test_generate_prompt_excludes_invite_examples() -> None:
    state = _build_state("fluffy_expedition_dandelion", "STEP_4_SYNTHESIS", collected_photos=["a", "b", "c"])
    state.synthesis_phase = "generate"
    text = _load_step_instructions(state)
    assert "What kind of adventure should we send them on?" not in text
    assert "Would you like to make up a story" not in text


def test_generate_prompt_has_single_story_theme_prefix() -> None:
    state = _build_state("fluffy_expedition_dandelion", "STEP_4_SYNTHESIS", collected_photos=["a", "b", "c"])
    state.synthesis_phase = "generate"
    text = _load_step_instructions(state)
    assert "Theme: Theme:" not in text


def test_synthesis_generate_prefers_complete_story_over_short_question() -> None:
    score_question = agent._score_candidate(short_question_turn, state)
    score_story = agent._score_candidate(long_story_turn, state)
    assert score_story > score_question


def test_t0_synthesis_invite_open_prompt_passes() -> None:
    result = score_validation_pass(
        dialogue="[gentle] Would you like to tell a little story about Mossy and Woolly?",
        step="STEP_4_SYNTHESIS",
        tier="T0",
        synthesis_phase="invite",
        is_first_on_step=True,
    )
    assert result == 1.0


def test_t0_synthesis_generate_question_fails() -> None:
    result = score_validation_pass(
        dialogue="[gentle] Mossy found one berry. What should they do?",
        step="STEP_4_SYNTHESIS",
        tier="T0",
        synthesis_phase="generate",
        is_first_on_step=False,
    )
    assert result == 0.0
```

Also add a turn-handler regression that proves a `generate`-phase synthesis response ending in a question gets rejected by `_validate_response()`.

**Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py -q
```

Expected:
- new tests fail because prompt assembly still includes question-led examples
- new synthesis scoring test fails because short question currently outscores long story
- new T0 synthesis validation expectations fail because current code still expects binary choice at synthesis invite

**Step 3: Keep failures focused**

If unrelated tests fail, trim the new tests until each failure maps to exactly one missing behavior:
- prompt contamination
- duplicated `Theme:` prefix
- bad best-of-N ranking
- stale synthesis validation rules

Do not implement fixes in this step.

**Step 4: Re-run the same narrow suite**

Run:

```bash
uv run pytest tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py -q
```

Expected:
- same targeted failures only

**Step 5: Commit**

```bash
git add tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py
git commit -m "test: capture synthesis quality regressions"
```

### Task 2: Replace Legacy T0 Binary Synthesis Validation With Phase-Aware Rules

**Files:**
- Modify: `backend/turn_handler.py`
- Modify: `scripts/scoring.py`
- Modify: `tests/test_scoring.py`
- Modify: `tests/test_turn_handler.py`

**Step 1: Write the failing test**

Add focused validation tests for all three synthesis modes:

```python
def test_validate_t0_synthesis_invite_allows_open_invitation() -> None:
    ...

def test_validate_synthesis_generate_requires_complete_non_question_story() -> None:
    ...

def test_validate_t0_collect_detail_still_requires_scaffold() -> None:
    ...
```

The third test is a guardrail so the Cat5 detail-phase behavior does not regress while changing synthesis validation.

**Step 2: Run the validation tests**

Run:

```bash
uv run pytest tests/test_scoring.py tests/test_turn_handler.py -q
```

Expected:
- invite test fails under the current binary-choice rule
- generate-phase question rejection test fails if `_validate_response()` does not inspect `state.synthesis_phase`

**Step 3: Write minimal implementation**

In `backend/turn_handler.py`:
- add a small synthesis helper, for example `_validate_synthesis_response(state, dialogue, is_first_on_step)`
- remove the old branch at `STEP_4_SYNTHESIS` that says T0 synthesis must contain `" or "`
- replace it with phase-aware rules:
  - `invite`: allow a single invitational question, including T0
  - `improve`: allow exactly one guiding question
  - `generate`: reject questions, require statement-style completion, and optionally require a minimum sentence floor per tier

In `scripts/scoring.py`:
- add a `synthesis_phase: str | None = None` parameter to `score_validation_pass()`
- mirror the same phase-aware logic used in `_validate_response()`

Keep the Cat5 detail-phase and Cat1 round-phase checks unchanged.

**Step 4: Run the narrow suite**

Run:

```bash
uv run pytest tests/test_scoring.py tests/test_turn_handler.py -q
uv run ruff check backend/turn_handler.py scripts/scoring.py tests/test_scoring.py tests/test_turn_handler.py
```

Expected:
- PASS for the new synthesis validation tests
- no regressions in existing T0 detail/round validation tests

**Step 5: Commit**

```bash
git add backend/turn_handler.py scripts/scoring.py tests/test_scoring.py tests/test_turn_handler.py
git commit -m "fix: make synthesis validation phase-aware"
```

### Task 3: Remove Generate-Phase Prompt Contamination And Theme Formatting Noise

**Files:**
- Modify: `backend/agents/script_agent.py`
- Modify: `backend/skills/examples/cat5_synthesis.yaml`
- Modify: `tests/test_script_agent.py`
- Modify: `tests/test_entity_registry.py`

**Step 1: Write the failing test**

Add tests that assert:
- `generate` prompt text does not include invite/opening examples
- `generate` prompt contains only full-story examples, or no sampled examples at all
- assembled prompt has `Theme: ...` only once

Example:

```python
def test_generate_prompt_uses_story_generation_examples_only() -> None:
    text = _load_step_instructions(state)
    assert "Story opening" not in text
    assert "What kind of adventure should we send them on?" not in text
    assert "One afternoon" in text or "### Story Generation" in text
```

**Step 2: Run the prompt tests**

Run:

```bash
uv run pytest tests/test_script_agent.py tests/test_entity_registry.py -q
```

Expected:
- failures showing legacy question-led examples are still present in `generate`
- failure showing duplicated `Theme: Theme: ...`

**Step 3: Write minimal implementation**

In `backend/agents/script_agent.py`:
- normalize `_SYNTHESIS_HINTS` to plain story concepts without the `"Theme: "` prefix
- keep `"Story theme: {hint}"` in the user prompt
- keep `"Theme: {story_theme}"` in the story-generation instruction file output
- change `_load_step_instructions()` so `STEP_4_SYNTHESIS` in `generate` phase does **not** inject `cat5_synthesis.yaml` examples intended for invite/improve

Recommended implementation:
- for `generate`, skip `{sampled_examples}` injection entirely and replace the placeholder with `""`
- rely on `cat5_step4_synthesis__story_generation.md` examples as the only examples for that phase

Optional alternative:
- split `backend/skills/examples/cat5_synthesis.yaml` into phase-tagged entries and sample only `phase=invite|improve`

Use the simpler skip-first option unless a test proves it materially hurts generation quality.

**Step 4: Run the narrow suite**

Run:

```bash
uv run pytest tests/test_script_agent.py tests/test_entity_registry.py -q
uv run ruff check backend/agents/script_agent.py tests/test_script_agent.py tests/test_entity_registry.py
```

Expected:
- PASS
- assembled `generate` prompt is clean: no invite examples, no duplicate `Theme:`

**Step 5: Commit**

```bash
git add backend/agents/script_agent.py backend/skills/examples/cat5_synthesis.yaml tests/test_script_agent.py tests/test_entity_registry.py
git commit -m "fix: clean synthesis generate prompts"
```

### Task 4: Make Best-Of-N Scoring Synthesis-Aware

**Files:**
- Modify: `backend/agents/script_agent.py`
- Modify: `tests/test_script_agent.py`

**Step 1: Write the failing test**

Add a scoring regression built from the live failure pattern:

```python
def test_generate_synthesis_story_outscores_short_prompt_like_candidate() -> None:
    state = make_synthesis_state(tier="T2", phase="generate", names=["Mossy Velvet", "Petal Puff", "Woolly Caterpillar"])
    short_question = TurnResponse(...)
    complete_story = TurnResponse(...)
    assert agent._score_candidate(complete_story, state) > agent._score_candidate(short_question, state)
```

Also add a T0 or T1 version that verifies a completed story with all names beats a short binary prompt.

**Step 2: Run the scoring test**

Run:

```bash
uv run pytest tests/test_script_agent.py -q
```

Expected:
- FAIL because `_score_candidate()` currently applies the normal 2/3/4 sentence cap even during synthesis generation

**Step 3: Write minimal implementation**

Refactor `_score_candidate()` in `backend/agents/script_agent.py`:
- keep the existing generic path for non-synthesis steps
- add a synthesis-generate branch, for example `_score_synthesis_story_candidate(dialogue, state)`

That synthesis-specific scorer should reward:
- sentence count inside the redesign target window:
  - T0: 7-8
  - T1: 9-11
  - T2: 12-14
- inclusion of all collected character names
- presence of quoted dialogue
- no trailing or mid-story question prompts meant for the child
- warm ending language

That branch should penalize:
- child-directed prompts like `"What should they do?"`
- invite-only fragments
- missing collected names
- very short outputs

Keep novelty as a smaller weight, not the dominant weight, for synthesis generation.

**Step 4: Run the narrow suite**

Run:

```bash
uv run pytest tests/test_script_agent.py -q
uv run ruff check backend/agents/script_agent.py tests/test_script_agent.py
```

Expected:
- PASS
- long valid synthesis stories outrank short prompt-like candidates

**Step 5: Commit**

```bash
git add backend/agents/script_agent.py tests/test_script_agent.py
git commit -m "fix: score synthesis stories by story quality"
```

### Task 5: Make The Active Database Path Deterministic And Logging Useful

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/db.py`
- Modify: `backend/server.py`
- Modify: `tests/test_db.py`
- Modify: `tests/test_api.py`

**Step 1: Write the failing test**

Add a config/database-path regression that proves `data/demo.db` resolves to one deterministic location regardless of whether the server starts from repo root or `backend/`.

Example:

```python
def test_db_path_is_resolved_from_repo_root(tmp_path: Path) -> None:
    settings = get_settings()
    resolved = resolve_db_path("data/demo.db", project_root=tmp_path)
    assert resolved == str(tmp_path / "data" / "demo.db")
```

Also add an API logging regression that verifies a fresh session writes `step` and `state_snapshot` columns to the active DB file.

**Step 2: Run the DB/logging tests**

Run:

```bash
uv run pytest tests/test_db.py tests/test_api.py -q
```

Expected:
- FAIL if path resolution is still cwd-dependent
- FAIL if migrations or logging helpers still point at different DB files in different working directories

**Step 3: Write minimal implementation**

In `backend/config.py`:
- add a helper that resolves relative `db_path` values against the repo root or config file root, not current working directory

In `backend/db.py` and `backend/server.py`:
- use the resolved absolute path everywhere
- log the resolved DB path once at startup
- keep existing migrations, but ensure they run against the same active DB file every time

Do **not** attempt to mutate or backfill the historical `backend/data/demo.db` rows in this task. The goal is reliable future diagnostics.

**Step 4: Run the narrow suite**

Run:

```bash
uv run pytest tests/test_db.py tests/test_api.py -q
uv run ruff check backend/config.py backend/db.py backend/server.py tests/test_db.py tests/test_api.py
```

Expected:
- PASS
- new sessions always log into the same DB file with the expanded `turns` schema

**Step 5: Commit**

```bash
git add backend/config.py backend/db.py backend/server.py tests/test_db.py tests/test_api.py
git commit -m "fix: stabilize db path and logging diagnostics"
```

### Task 6: Update End-To-End Quality Checks To Match The Redesigned Synthesis Contract

**Files:**
- Modify: `backend/tests/test_ai_quality.py`
- Modify: `tests/test_scoring.py`
- Modify: `HANDOFF.md`

**Step 1: Write the failing test**

Replace the outdated T0 synthesis expectation:

Current behavior under test:

```python
if has_open_question(synthesis) and " or " not in synthesis.lower():
    issues.append(...)
```

New expectation:

```python
if state.get("current_step") == "STEP_4_SYNTHESIS":
    assert "story" in synthesis.lower() or "characters" in synthesis.lower()

if state.get("current_step") == "STEP_5_CELEBRATE":
    assert "?" not in previous_synthesis_dialogue
    assert count_sentences(previous_synthesis_dialogue) >= expected_min_sentences
```

Track the synthesis dialogue explicitly so the test can validate the generated story, not just the invite.

**Step 2: Run the quality suite**

Run:

```bash
uv run pytest tests/test_scoring.py -q
```

If the local server is available, also run:

```bash
uv run pytest backend/tests/test_ai_quality.py -q
```

Expected:
- unit suite fails until assertions are updated
- integration suite may require a running server; if unavailable, document that and stop after the unit suite

**Step 3: Write minimal implementation**

In `backend/tests/test_ai_quality.py`:
- stop treating binary synthesis choice as the correct T0 contract
- validate:
  - invite phase can be open but short
  - generate phase produces a complete non-question story
  - sentence floor matches tier target band

In `HANDOFF.md`:
- record that synthesis quality diagnostics now rely on one deterministic DB path and phase-aware synthesis validation/scoring

**Step 4: Run the final targeted verification**

Run:

```bash
uv run pytest tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py tests/test_db.py tests/test_api.py -q
uv run ruff check backend/config.py backend/db.py backend/server.py backend/agents/script_agent.py backend/turn_handler.py scripts/scoring.py tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py tests/test_db.py tests/test_api.py
uv run ruff format --check backend/config.py backend/db.py backend/server.py backend/agents/script_agent.py backend/turn_handler.py scripts/scoring.py tests/test_script_agent.py tests/test_scoring.py tests/test_entity_registry.py tests/test_turn_handler.py tests/test_db.py tests/test_api.py
```

If the server is running:

```bash
uv run pytest backend/tests/test_ai_quality.py -q
```

Expected:
- all targeted unit suites PASS
- integration suite PASS if the server is running; otherwise record that it was not executed

**Step 5: Commit**

```bash
git add backend/tests/test_ai_quality.py tests/test_scoring.py HANDOFF.md
git commit -m "test: align synthesis quality checks with story loop"
```

### Notes For Execution

- Do not remove `synthesis_type` from `Cat5CreativeSlots` in this plan. It is now legacy, but removing it expands scope into parser, registry, and recipe fixtures that are not causing the live quality issue.
- Do not enable two-pass generation in this plan. `two_pass_enabled` is currently false, so the quality win should come from the single-pass + best-of-N path first.
- Keep changes incremental. After every task, run only the smallest relevant verification listed above.
- Use the captured session `a6425e09-9057-4715-9876-8f610c7e28a5` only as a regression reference. Do not try to “repair” that historical DB row set.

