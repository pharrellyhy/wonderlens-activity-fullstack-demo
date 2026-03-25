# Example-Driven Prompt Architecture

## Problem

The current prompt system uses 26 step instruction files with 20+ rules each. The LLM can't follow all rules simultaneously — more rules means worse compliance per rule. We've been in a cycle: AI violates rule → add more rules → prompt gets longer → AI violates different rule. This won't converge.

Real-world child interactions also produce infinite combinations of responses that no ruleset can fully cover. The system needs to handle novel situations gracefully, not just the ones we've pre-defined.

## Root Cause

We're treating the LLM as a rule-following machine when it's actually a pattern-matching conversation engine. Rules are abstract and competing. Examples are concrete and composable. LLMs are much better at imitating examples than following abstract rules.

## Proposed Architecture

Replace rule-heavy step instructions with **few-shot example transcripts** + **minimal context** + **one key constraint per step**. Use code for structural guarantees. Use post-processing validation for hard constraints.

### Principles

1. **Examples over rules.** Show 2-3 ideal conversation turns per step, per tier. The LLM imitates the tone, length, and scaffolding pattern naturally.
2. **5-line step prompts.** Each step gets: GOAL (1 sentence), CONTEXT (dynamic data), CONSTRAINT (1 hard rule), EXAMPLES (2-3 turns).
3. **Code handles structure.** State machine handles flow. Code injects progress counts, collected names, round items. Post-processing catches hard violations.
4. **LLM handles conversation.** Creative dialogue, naming, storytelling, responding to unexpected input — the LLM's actual strength.

## Per-Step Design

### STEP 1: Hook

**Current:** 25+ lines of rules about emotional reactions, no questions, tier-specific language, etc.

**Proposed:**
```
GOAL: React with excitement to the {entity_name} the child just photographed.
CONTEXT: Entity={entity_name}, Tier={tier}, Photo features={photo_features}
CONSTRAINT: None — just be genuine and brief.

EXAMPLES (T0):
AI: "[excited] Wow! A ladybug! Look at those spots!"
AI: "[amazed] Ooh, fluffy white seeds! So soft!"
AI: "[delighted] A big dinosaur! ROAR!"

EXAMPLES (T1):
AI: "[excited] Wow, look at those little black spots on the red shell! I wonder how many there are!"
AI: "[amazed] Those fluffy white seeds look like tiny parachutes flying away!"
```

### STEP 2: Mission / Rules

**Current:** 60+ lines with 7 "You MUST" items, demo instructions, invitation rules, re-invitation rules.

**Proposed:**
```
GOAL: Explain the game simply and invite the child to play.
CONTEXT: Game={activity_name}, Find {collection_count} things with {collection_criterion}, Role={role_title}, Tier={tier}
CONSTRAINT: End with an invitation question ("Would you like to...?"), not a command.

EXAMPLES (T0 Cat5):
Child: "mars"
AI: "[adventurous] Mars! Fun! Let's find 3 soft things. See this dandelion? So fluffy! Would you like to find more?"

Child: "no"
AI: "[gentle] That's okay! What if we just look around together? Would you like to try?"

EXAMPLES (T0 Cat1):
Child: "wow"
AI: "[playful] I know! Let's play a voice game. If the doggy was happy, it would say 'YAY!' Would you like to try?"
```

### STEP 3: Collection Round (Cat5)

**Current:** 110+ lines covering Phase A, Phase B, correct/wrong/silence branches, progressive narrative, variation rules, avoid lists.

**Proposed:**
```
GOAL: Celebrate the find, ask about it (model first for T0), build the character cast.
CONTEXT: Found={collected_count}/{total_rounds}, Item={item_label}, Previous characters={collected_names}, Previous details={collected_details}, Tier={tier}
CONSTRAINT: For T0, always model your idea first before asking. Never suggest specific items.

EXAMPLES (T0, correct photo, 1st find):
AI: "[excited] Fuzzy moss! 1 out of 3! I think it looks like a cloud. Cloud or pillow?"
Child: "cloud"
AI: "[celebrating] Cloud Puff! Want to find another soft friend?"

EXAMPLES (T0, correct photo, 2nd find):
AI: "[excited] Woolly caterpillar! 2 out of 3! Cloud Puff has a friend! I think it looks like a fuzzy worm. Fuzzy Worm or Tickle Bug?"
Child: "tickle bug"
AI: "[celebrating] Tickle Bug! Cloud Puff and Tickle Bug together! One more?"

EXAMPLES (T0, wrong photo):
AI: "[gentle] That pinecone is spiky! Something soft might be nearby."

EXAMPLES (T0, silence):
AI: "[gentle] I wonder if something fluffy is near you. Want to look around?"
```

### STEP 3: Round (Cat1)

**Current:** 35+ lines covering presenting scenario, responding to answers, scaffolding, escalation.

**Proposed:**
```
GOAL: Present the round's scene, ask the child to respond in character.
CONTEXT: Round={round_number}/{total_rounds}, Scenario={round_scenario}, Game={game_mechanic}, Tier={tier}
CONSTRAINT: For T0, model a short answer (2-4 words) first, then ask "or something different?"

EXAMPLES (T0, voice_acting, presenting):
AI: "[adventurous] The doggy found a big puddle! I think it would say 'SPLASH!' What do you think — SPLASH or something else?"

EXAMPLES (T0, voice_acting, responding to good answer):
AI: "[celebrating] WOOF WOOF! That's so funny!"

EXAMPLES (T0, voice_acting, child stuck):
AI: "[gentle] Maybe it would say 'WOW!' or 'UH OH!' Which one?"
```

### STEP 4: Synthesis (Naming Story)

**Current:** 75+ lines covering tier-based flow, 4-beat structure, response branches, story rules.

**Proposed:**
```
GOAL: Create a short story using the collected characters. T0: you tell it with one choice for the child. T1: set up, child contributes. T2: invite child to try first.
CONTEXT: Characters={collected_names}, Details={collected_details}, Tier={tier}
CONSTRAINT: Maximum 2 turns. If child is stuck even once, finish the story yourself. Never make the child fail twice.

EXAMPLES (T0):
AI: "[dreamy] Cloud Puff was floating along when BUMP — Tickle Bug appeared! Did Tickle Bug tickle or hug?"
Child: "tickle"
AI: "[celebrating] Tickle Bug tickled Cloud Puff! They both giggled and rolled down a fluffy hill together!"

EXAMPLES (T0, child silent):
AI: "[dreamy] Cloud Puff was floating along when BUMP — Tickle Bug appeared! Did Tickle Bug tickle or hug?"
[silence]
AI: "[gentle] Tickle Bug gave Cloud Puff a big hug! They snuggled together on the softest leaf!"

EXAMPLES (T2):
AI: "[curious] All your characters are together now. Can you tell me what happens when Cloud Puff meets Tickle Bug?"
Child: "they play tag"
AI: "[excited] They play tag! Cloud Puff floats away and Tickle Bug wiggles after! Great story!"
```

### STEP 5: Celebrate

**Current:** 20+ lines.

**Proposed:**
```
GOAL: Celebrate the child's effort, award the role title, mention the observation focus.
CONTEXT: Role={role_title}, Characters={collected_names}, Observation={observation_angle}
CONSTRAINT: Keep to 2-3 sentences. This is 1 turn.

EXAMPLES (T0):
AI: "[proud] You found so many soft things! Mission accomplished, Fluffy Expedition Explorer!"

EXAMPLES (T1):
AI: "[proud] You discovered that fluffy things come in so many shapes! Cloud Puff, Tickle Bug, and Pillow Petal — what an amazing team. You are now a Fluffy Expedition Explorer!"
```

### STEP 6: Closing

**Current:** 25+ lines about IB concepts, forward hooks, tier-specific concept counts.

**Proposed:**
```
GOAL: Celebrate, name 1-2 IB concepts naturally, end with a forward hook.
CONTEXT: Concepts={concepts_earned}, Role={role_title}, Entity={entity_name}
CONSTRAINT: T0: name 1 concept. T1: 2 concepts. T2: up to 3. Weave naturally, don't list.

EXAMPLES (T0):
AI: "[warm] Your fluffy friends are all connected! That's called Connection. See you next time, explorer!"

EXAMPLES (T1):
AI: "[warm] You noticed the beautiful Form of soft things everywhere, and found a Connection between all your fluffy friends! Next time you're outside, keep those explorer eyes open!"
```

## System Prompt Changes

The `script_system.md` system prompt would also be radically simplified:

**Current:** 100+ lines of rules, tables, forbidden patterns, multimedia directives.

**Proposed (~30 lines):**
```
You are WonderLens AI, a friendly companion for young children exploring objects they photograph.

Tier: {tier}
- T0 (ages 2-4): Very short sentences (~6 words). Simple words. Always model your idea first before asking.
- T1 (ages 4-6): Short sentences (~10 words). Can ask lighter questions.
- T2 (ages 6-8): Slightly longer sentences (~15 words). Can invite child to try first.

General style:
- Warm and encouraging. Never criticize.
- One idea per sentence. One metaphor max per turn.
- When modeling a phrase the child might repeat, keep it to 2-4 words.

Before responding, silently check:
- Is this short enough for a {age} year old?
- Did I model first before asking (if T0)?
- Would a {age} year old understand every word?

Every response must end with [SCREEN] and [AUDIO] directives.
```

Then the per-step examples carry the rest of the weight.

## How Examples Are Loaded

Two options:

### Option A: Examples in game MD files
Add an `example_transcript` section to each game's frontmatter. Examples are game-specific (ladybug examples reference spots, dandelion examples reference fluff). The script agent template system injects them.

**Pro:** Examples are perfectly tailored to each game.
**Con:** 18 game files × 6 steps × 3 tiers = lots of examples to write. But most can share templates with entity-specific substitution.

### Option B: Examples in step instruction files (per tier)
Replace current rule-heavy step instructions with example-heavy ones. Each step file has T0/T1/T2 example sections. The examples use generic placeholders that the template system fills with actual entity/character names.

**Pro:** Fewer files to maintain. Examples are reusable across games.
**Con:** Less game-specific. But the template variables ({entity_name}, {collected_names}, etc.) handle most of the specificity.

**Recommendation: Option B.** Rewrite the existing step instruction files to be example-driven instead of rule-driven. Use template variables for game-specific content. This is the minimal-change path — same files, same template system, different content strategy.

## What Code Handles (Unchanged)

| Concern | Current | Proposed |
|---------|---------|----------|
| Step flow | State machine | State machine (unchanged) |
| Progress tracking | Turn handler | Turn handler (unchanged) |
| Phase transitions | Turn handler | Turn handler (unchanged) |
| Screen frame selection | State machine | State machine (unchanged) |
| Template variable injection | Script agent | Script agent (unchanged) |

## What Post-Processing Validates (Unchanged)

| Rule | Check |
|------|-------|
| T0 open question without scaffold | `_ends_with_open_question() and not _has_model_phrase()` |
| T0 synthesis without choices | Same + `" or " not in dialogue` |
| T0 Cat1 round without scaffold | Same |

## Migration Plan

### Phase 1: Prototype one game
- Pick `fluffy_expedition_dandelion` (Cat5, T0) as the test case
- Rewrite its 6 step instruction files to example-driven format
- Simplify the system prompt for this game
- Run the AI quality test suite to compare

### Phase 2: Measure
- Run the same test 5 times each for rule-based vs example-based
- Compare: compliance rate, response length, response quality (manual review)
- If example-based wins, proceed. If not, analyze why.

### Phase 3: Roll out to all games
- Rewrite all step instruction files to example-driven format
- Generate game-specific examples using template variable substitution
- Simplify the system prompt globally

### Phase 4: Add T1/T2 examples
- Phase 1-3 focus on T0 (our biggest quality gap)
- Add T1 and T2 example sets
- Re-run quality tests across all tiers

## Expected Outcomes

- **Shorter prompts** — ~60% reduction in prompt token count per step
- **Better T0 compliance** — examples naturally enforce brevity, scaffolding, and tone
- **More graceful handling of unexpected input** — the LLM can improvise within the demonstrated style
- **Easier to tune** — changing one example is faster than debugging a 20-rule interaction
- **Still reliable on hard constraints** — post-processing validation catches the rest

## Risks

- **Example quality matters a lot** — bad examples produce bad output. Need careful curation.
- **May need more examples for edge cases** — wrong photo, silence, decline, off-topic. Current rules explicitly handle these; examples need to cover them too.
- **Tier differentiation** — rules explicitly state "T0 max 6 words." Examples show it implicitly. The LLM might not maintain the distinction as sharply. Mitigation: the system prompt still states the tier constraint explicitly.

## Verification

- AI quality test suite (`tests/test_ai_quality.py`) — must pass at same or better rate
- Manual play-through of each game at T0 — compare response quality side-by-side
- Prompt token count comparison — measure reduction
