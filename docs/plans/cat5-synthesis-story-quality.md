# Cat5 Synthesis Story Quality & Invitation Clarity

## Problem

Two issues with the current naming_story synthesis experience:

### 1. Synthesis invitation too subtle
The progressive storytelling update changed the synthesis prompt from "Would you like to make up a story?" (too daunting) to "What happens when they meet?" (too subtle). The child doesn't realize it's story time. Need something in between that clearly signals "let's tell a story" while staying inviting and light.

**Current (too subtle):**
> "Cloud Puff, Pillow Petal, and Tickle Worm are all together now — what do they do?"

**Desired (story-shaped but light):**
> "Cloud Puff, Pillow Petal, and Tickle Worm are ready for an adventure! Would you like to tell me what adventure they go on — or should I start the story?"

Key differences:
- Uses the word "adventure" or "story" so the child knows what's expected
- Offers a binary choice ("you tell or I start") to reduce blank-page anxiety
- Still builds on the progressive narrative from collection

### 2. AI-generated stories are flat
When the child says "you do it" or "sure", the AI produces 2-3 disconnected sentences, not a real story. Current instruction just says "create a short, fun story (2-3 sentences)" — too vague for the LLM to produce quality output.

**Current output (flat):**
> "Cloud Puff floated up and found Pillow Petal. They played together. Tickle Worm came too and they were happy!"

**Desired output (structured mini-story):**
> "Cloud Puff was floating through the garden when — BUMP — it landed right on Pillow Petal! 'That tickles!' giggled Pillow Petal. Then Tickle Worm wiggled over and said 'Did someone say tickles? That's MY job!' And all three friends rolled down a soft hill together, laughing the whole way!"

The difference is structure: opening → meeting → adventure → punchline/ending.

## Solution

Add a **story structure formula** to the naming_story synthesis instructions. Not a new file or backend skill — just richer guidance within the existing `cat5_step4_synthesis__naming_story.md`.

### Story structure formula

```
When the AI tells/starts a story, follow this 4-beat structure:

1. OPENING — One character doing something related to their original detail
   "[Character 1] was [action from their detail]..."
   Example: "Cloud Puff was floating through the garden..."

2. MEETING — Second character appears, interaction happens
   "Then [Character 2] [appeared/bumped into/called out]..."
   Example: "...when BUMP — it landed right on Pillow Petal!"

3. ADVENTURE — Something fun happens using their traits
   "Together they [activity using observation_angle]..."
   Example: "'That tickles!' giggled Pillow Petal."

4. PUNCHLINE — Third character joins or surprise ending
   "[Character 3] [twist or cozy conclusion]!"
   Example: "Tickle Worm wiggled over: 'Did someone say tickles?'"

Rules:
- Reference each character's ORIGINAL detail from collection
- Use sensory language tied to the observation_angle (texture → soft/fuzzy/fluffy)
- Include at least one line of dialogue (characters talking)
- Include at least one sound effect or action word (BUMP, WHOOSH, giggled)
- 3-5 sentences, not 2
- End with a warm, complete feeling — not a cliffhanger
```

### Updated invitation phrasing

```
For the synthesis opening prompt:
- Frame it as "adventure" or "story" (clear signal)
- Offer a binary choice to reduce blank-page anxiety
- Reference the character names from collection

Good: "[Names] are ready for an adventure! Would you like to tell me what they do — or should I start the story?"
Good: "All your fluffy friends are together! Do you want to tell their story, or should I begin?"
Bad: "What happens when they meet?" (too vague — child doesn't know this is story time)
Bad: "Would you like to make up a story?" (too open-ended — daunting)
```

### comparison_chart — no changes needed
The comparison_chart synthesis ("can you put them in order?") is clear enough and doesn't need a story formula. No changes for this type.

## Implementation

### File to modify

`backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — the only file that needs changes.

### Changes

#### 1. Update the synthesis invitation section

Replace:
```
Ask what happens when the characters meet: "{collected_names} are all together now — what do they do?"
```

With:
```
Signal story time clearly with a binary choice:
- "[collected_names] are ready for an adventure! Would you like to tell me what they do — or should I start the story?"
- Use the word "adventure" or "story" so the child knows what's expected
- Offer "you tell or I start" to reduce blank-page anxiety
```

#### 2. Add story structure formula to the "you do it" section

Replace the vague "create a short, fun story (2-3 sentences)" with the 4-beat structure formula:
1. OPENING — one character doing something from their detail
2. MEETING — second character appears
3. ADVENTURE — something fun using their traits
4. PUNCHLINE — third character or cozy ending

Plus concrete rules: reference original details, use sensory language, include dialogue, include sound effects, 3-5 sentences.

#### 3. Update the "child tells the story" handling

When the child contributes their own story attempt, the AI should build on it using the same structure — extend their contribution toward a satisfying ending rather than just saying "great story!"

### What does NOT change

- No backend logic changes
- No schema changes
- No frontend changes
- No other step instruction files
- `cat5_step4_synthesis.md` (base) — already fine, the naming_story fragment overrides the relevant parts
- `cat5_step4_synthesis__comparison_chart.md` — no story formula needed
- Cat1 flows unaffected

### Verification

1. `uv run pytest tests/ -q` — all tests pass
2. Manual test: Run `fluffy_expedition_dandelion`:
   - Synthesis prompt should say "adventure" or "story" with a binary choice
   - If child says "you do it": AI tells a 4-beat story with dialogue and sound effects
   - If child says "they play together": AI extends it into a fuller mini-story
3. `python scripts/test_all_activities.py` — all 5 activities pass
