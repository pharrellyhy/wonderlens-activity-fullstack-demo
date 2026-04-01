# Turn Director + Story Scaffold Redesign

**Date:** 2026-03-31
**Status:** In Progress

## Problem

The current turn pipeline has three interconnected issues:

1. **Content-type intent classification** — The classifier outputs what the child *said* (confirm/decline/substantive/off_topic), then ~300 lines of if/elif routing in `resolve_turn()` translates that into what to *do*. This is brittle and hard to extend.

2. **Fixed response templates** — `_ACCEPTANCE_CELEBRATIONS`, `_PHOTO_FIND_PROMPTS`, `_SYNTHESIS_INVITE_TEMPLATES` produce repetitive, robotic responses that don't adapt to context.

3. **Collection-synthesis disconnect** — Cat5 collection rounds ask the same detail question every round ("Touch it — how does it feel?") and the gathered details are ignored when generating the synthesis story.

## Solution

### Turn Director (replaces classifier + planner)

Merge the intent classifier and planner into a single **Turn Director** LLM call that outputs action-based intents:

| Action | Meaning |
|--------|---------|
| `advance` | Child completed phase objective — move forward |
| `stay` | Engaged but objective not met — stay in current phase |
| `need_help` | Stuck/confused/silent — scaffold |
| `redirect` | Off-topic but animated — acknowledge, steer back |
| `exit` | Consistently disengaged — graceful goodbye |

Plus `reasoning` (1-3 sentences for debuggability) and `response_direction` (strategy for the speaker — replaces fixed templates and 19-field TurnPlan).

**Pipeline:** 3 LLM calls (classifier → planner → speaker) becomes 2 (turn director → speaker).

### Story Scaffold (replaces synthesis_type + detail_question_template)

Game definitions gain a `story_scaffold` section that tells the Turn Director what story ingredients to harvest each round:

```yaml
story_scaffold:
  premise: "Each fluffy find becomes a character with a special talent based on how it feels"
  harvest_per_round: character_talent
  harvest_question_strategy: "R1: texture → talent; R2: compare talents; R3: group role"
  synthesis_goal: "Characters combine their talents on a shared adventure"
  synthesis_format: collaborative_story
```

Collection rounds build toward synthesis instead of gathering disconnected sensory facts.

## Key Design Decisions

- **Feature-flagged:** `turn_director_enabled` in config — legacy path runs unchanged when disabled
- **Word-list fast-path stays:** Common phrases (yes/no/ok) still bypass LLM, but map to actions context-dependently
- **Speaker barely changes:** Receives `response_direction` string instead of 19-field TurnPlan JSON
- **Backward compat:** `collected_details` and `collected_names` dual-written alongside new `story_elements`
- **Step instruction variants slimmed:** `cat5_step3_collect__*.md` files become thin constraint sheets for the speaker; decision logic moves to Turn Director prompt

## Implementation Phases

1. **Schemas** — `TurnDirective`, `StoryElement`, `StoryScaffold`, session state additions
2. **Turn Director Agent** — new agent + prompt, feature flag in config
3. **Routing** — `_fast_path_directive()`, `_resolve_turn_with_directive()`, feature flag branch
4. **Speaker** — `generate_turn_from_directive()`, new speaker prompt template
5. **Story Scaffold** — game definition updates, step instruction slimming
6. **Testing** — unit tests, integration tests, manual playtesting

## Files Changed

| File | Change |
|------|--------|
| `backend/schemas/turn_directive.py` | NEW |
| `backend/schemas/creative_slots.py` | Add StoryScaffold |
| `backend/schemas/session_state.py` | Add story_elements |
| `backend/agents/turn_director.py` | NEW |
| `backend/skills/turn_director_system.md` | NEW |
| `backend/skills/speaker_directive_system.md` | NEW |
| `backend/turn_handler.py` | Add directive routing |
| `backend/agents/script_agent.py` | Add directive speaker method |
| `backend/config.py` | Add feature flag |
| `backend/games/*.md` | Add story_scaffold |
| `backend/skills/step_instructions/cat5_step3_collect__*.md` | Slim down |
