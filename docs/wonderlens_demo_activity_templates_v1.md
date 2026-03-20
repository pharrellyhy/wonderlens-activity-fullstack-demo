# WonderLens Demo Activity Templates

**Entity-Agnostic Templates for Category 1 & Category 5**

> For the interactive web demo, these templates allow any user-uploaded image to drive a full activity flow. The LLM fills entity-specific content at runtime while the template enforces pedagogical structure, IB compliance, and age-tier rules.

Version 1.0 | March 2026 | Algorithm + Frontend Teams

---

## 1. Why Templates? The Entity-Agnostic Problem

In the design document (WonderLens_activity_design_0307.docx), each activity is written around a **specific entity** — "毛绒狗狗" for Cat 1, "有花纹的石头" for Cat 5. In the web demo, the user uploads an **arbitrary image** (could be a banana, a shoe, a parrot). The entity is unknown until vision runs.

> **⚠️ The Problem**
>
> Hardcoded scripts break when the entity changes. "你的狗狗今天看起来怎么样" makes no sense if the child photographed a pineapple.
>
> But the pedagogical STRUCTURE is entity-agnostic: emotional hook → game mechanic → multi-round dialogue → IB closing.
>
> **Solution**: Extract structure as a template. LLM fills entity-specific content at runtime.

This document defines two complete templates — one for Category 1 (in-device verbal dialogue) and one for Category 5 (out-of-device collection/exploration) — with every slot, constraint, and LLM instruction specified for the demo frontend and backend to consume.

---

## 2. Template Architecture Overview

Each template has three layers:

| Layer | What It Contains | Who Owns It |
|---|---|---|
| **Fixed Structure** | Step sequence, phase purposes, round counts, exit rules | Template (hardcoded) |
| **Slot Definitions** | Entity-dependent variables the LLM must fill (e.g., `{entity_name}`, `{observation_angle}`) | Template defines; LLM fills at runtime |
| **Tier Overrides** | Per-tier adjustments to language complexity, round count, question style | Template defines; system prompt enforces |

### 2.1 Runtime Flow

The demo backend orchestrates this sequence:

1. User uploads image →
2. Vision API identifies entity + attributes →
3. Backend selects template (Cat 1 or Cat 5) →
4. Backend injects template + vision result + tier rules into LLM system prompt →
5. LLM generates each turn following the template structure

> **💡 Key Insight**
>
> The template is NOT a rigid script. It is a structural constraint that the LLM must follow while generating creative, entity-specific content.
>
> Think of it as: the template is the lesson plan; the LLM is the teacher improvising within the plan.

---

## 3. Shared Infrastructure: Slot System & Tier Rules

### 3.1 Universal Slots (Both Templates)

These slots exist in every template and are filled by the vision result or tier configuration:

| Slot Name | Type | Source | Example |
|---|---|---|---|
| `{entity_name}` | string | Vision API label | "pineapple", "toy car", "cat" |
| `{entity_category}` | string | Vision API or mapping | "fruit", "vehicle", "animal" |
| `{entity_attributes}` | list[string] | Vision API description | ["yellow", "spiky top", "tropical"] |
| `{tier}` | T0 \| T1 \| T2 | User selection in demo | "T1" |
| `{ib_theme}` | string | Mapped from entity | "How the world works" |
| `{ib_key_concepts}` | list[string] | Mapped from entity + activity | ["Form", "Connection"] |
| `{ib_related_concepts}` | list[string] | Mapped from entity | ["Pattern", "Structure"] |

### 3.2 Tier Rules (Injected into System Prompt)

These constraints are enforced at the system prompt level, not inside the template JSON:

| Parameter | T0 (2–4) | T1 (4–6) | T2 (6–8) |
|---|---|---|---|
| Words per sentence | 5–10 | 10–15 | 15–20 |
| Max sentences per turn | 2 | 3 | 4 |
| Hook style | Personal feeling | Experience / preference | Opinion / connection |
| Question complexity | Binary / simple choice | Open guided | Fully open |
| Dialogue rounds | 2–3 | 3–4 | 4–5 |
| Closing concepts named | 1 | 2 | Up to 3 |
| Silent timeout | 10s | 8s | 6s |
| Response style | Simple, playful | Curious, encouraging | Conversational, peer |

### 3.3 The Hook Rule (Non-Negotiable)

> **🚫 Hook Rule**
>
> The FIRST conversational turn must use EMOTIONAL RESONANCE. Never knowledge testing.
>
> ✅ "Wow, look at that spiky crown on top! It looks like a little king!"
>
> ❌ "Do you know what this fruit is called?"
>
> This applies to ALL tiers, ALL entities, ALL templates.

### 3.4 Consecutive Silence Exit Rule

Both templates share this exit logic:

- **1st silence**: AI gently re-engages with a simpler, lower-stakes prompt.
- **2nd consecutive silence**: Graceful exit — celebrate what was accomplished, warm goodbye, tomorrow hook. Do NOT name IB concepts during early exit.

---

## 4. Template A: Category 1 — In-Device Verbal Dialogue

> **🎭 Category 1 at a Glance**
>
> - **Type**: 持续言语互动 (sustained verbal interaction). No camera needed after initial photo.
> - **Core mechanic**: Voice-only dialogue game that grows out of what the child photographed.
> - **Duration**: 3–8 minutes depending on tier and engagement.
> - **Hardware**: Microphone + speaker only. No additional photos required.

### 4.1 Template-Specific Slots

In addition to the universal slots, Cat 1 requires these LLM-filled variables:

| Slot Name | Type | LLM Instruction | Example (entity = pineapple) |
|---|---|---|---|
| `{game_mechanic}` | enum | Choose ONE from: `mood_guessing`, `true_or_silly`, `voice_acting`, `storytelling_chain`, `riddle_game`, `sound_imitation` | "true_or_silly" |
| `{metaphor}` | string | A playful imaginative frame for the entity | "This pineapple is a little warrior with a spiky helmet!" |
| `{role_title}` | string | A fun title awarded to the child at the end | "Tropical Truth Detective" |
| `{round_scenarios}` | list[string] | One scenario per dialogue round, escalating in complexity | ["Pineapples grow on trees", "Pineapples can swim", "Pineapple juice is made from the leaves"] |
| `{escalation_axis}` | string | How rounds increase in difficulty | "fact plausibility becomes more ambiguous" |
| `{observation_detail}` | string | One specific visual detail from the photo to anchor the hook | "the spiky green crown on top" |

### 4.2 Step-by-Step Flow

The following defines the fixed structural skeleton. Each step's content is generated by the LLM using the slots above.

---

#### Step 1: Transition Bridge (Emotional Hook)

| Aspect | Specification |
|---|---|
| **Purpose** | Create emotional resonance with the photographed entity. Bridge from "photo taken" to "game about to start." |
| **LLM must do** | 1. Reference `{observation_detail}` from the actual photo. 2. Use `{metaphor}` to create wonder. 3. End with an EMOTIONAL question (never knowledge-testing). 4. Follow tier word/sentence limits. |
| **Screen widget** | `photo_display`: Show the uploaded photo with a soft glow `animation_overlay`. |
| **Child response branches** | **Ideal**: Child engages with the metaphor → AI affirms and pivots to game intro. **Off-topic**: Child says something unrelated → AI gently incorporates and redirects. **Silence**: Wait `{silent_timeout}`, then offer a simpler binary prompt. |
| **Example (pineapple, T1)** | AI: *(excited)* "Wow, look at that spiky green crown! This must be the king of all fruits! If this pineapple king could talk, what do you think it would say first?" |
| **"过渡感" requirement** | The game must feel like it "grows out of" this conversation, not like a sudden task assignment. The last sentence of this step must contain a natural bridge word: "I have an idea...", "That gives me a fun thought...", "You know what we should do?" |

---

#### Step 2: Game Mechanic Introduction + Demo Round

| Aspect | Specification |
|---|---|
| **Purpose** | Explain the game rules clearly. Run one demonstration round so the child understands. |
| **LLM must do** | 1. Name the game using a fun, child-friendly title (not the enum value). 2. Explain rules in ≤ 2 sentences (T0) or ≤ 3 sentences (T1/T2). 3. Run one demo round with the answer included, so the child sees how it works. 4. End with enthusiasm: "Now it's your turn!" |
| **Screen widget** | `character_display`: Show Zigzag avatar with speech bubble. Optional: animated game icon. |
| **Game mechanics reference** | `true_or_silly`: AI states facts about `{entity_name}`, child judges true/silly. `mood_guessing`: AI describes scenarios, child guesses `{entity_name}`'s feeling. `voice_acting`: AI sets a scene, child voices what `{entity_name}` would say. `storytelling_chain`: AI starts a story about `{entity_name}`, child adds the next part. `riddle_game`: AI gives clues about things related to `{entity_name}`, child guesses. `sound_imitation`: AI describes how `{entity_name}` might sound in scenarios, child performs. |
| **Mechanic selection logic** | LLM should choose based on entity category: Animals → `mood_guessing`, `sound_imitation`, `voice_acting`. Food/Plants → `true_or_silly`, `riddle_game`. Vehicles/Objects → `voice_acting`, `storytelling_chain`. Imaginary → `storytelling_chain`, `mood_guessing`. |
| **Example (pineapple, T1, true_or_silly)** | AI: "I'm going to say things about our pineapple king, and you tell me — TRUE or SILLY? Here's a practice one: Pineapples are sweet inside. Is that... true or silly? ... That's TRUE! Great, you've got it. Ready for the real ones?" |

---

#### Step 3: Multi-Round Dialogue (Core Gameplay)

| Aspect | Specification |
|---|---|
| **Purpose** | The main interactive phase. Multiple rounds following the chosen game mechanic. |
| **Round count** | T0: 2–3 rounds \| T1: 3–4 rounds \| T2: 4–5 rounds |
| **LLM must do per round** | 1. Present the round's scenario/question using `{round_scenarios[i]}`. 2. Wait for child response. 3. React to child's answer with: **Correct** → Enthusiastic affirmation + one educational tidbit. **Wrong** → Gentle correction with encouragement + hint. **Silence** → Offer a simpler rephrasing or binary choice. 4. Brief transition to next round ("Next one!", "Ready for a trickier one?"). |
| **Escalation** | Rounds MUST escalate along `{escalation_axis}`. Early rounds are easy/obvious; later rounds require more thought. The LLM must not generate flat difficulty. |
| **Screen widget** | `character_display` with emotion changes (happy on correct, thinking on wrong). Optional: round counter badge overlay. |
| **Tone markers** | Each AI turn must include a tone marker for TTS: `(excited)`, `(mysterious)`, `(encouraging)`, `(impressed)`, `(gentle)`. |
| **Educational insertion rule** | After a correct answer, AI may insert ONE short educational fact. Keep to 1 sentence max. This is knowledge enrichment, not testing. |
| **Example round (pineapple, T1, round 3)** | AI: *(mysterious)* "Okay, this one is tricky! Pineapples take TWO WHOLE YEARS to grow. True... or silly?" Child: "True?" AI: *(impressed)* "TRUE! Can you believe it? Two whole years of growing just to become this delicious! That's very patient. Next one coming up!" |

---

#### Step 4: Celebration + Role Title Award

| Aspect | Specification |
|---|---|
| **Purpose** | Mark the end of gameplay with celebration. Award the child a fun role title. |
| **LLM must do** | 1. Enthusiastic praise referencing specific things the child said or did. 2. Award `{role_title}` with ceremony. 3. Brief recap of what was learned/explored (not a test, a celebration). |
| **Screen widget** | `badge_award`: Display `{role_title}` as an achievement badge with confetti `animation_overlay`. |
| **Duration** | 1 AI turn only. Keep concise — children lose interest during long summaries. |
| **Example (pineapple, T1)** | AI: *(celebrating)* "Ding ding ding! You are now officially a Tropical Truth Detective! You figured out SO many real and silly things about our pineapple king. My favorite was when you said [callback to child's answer]. Amazing job!" |

---

#### Step 5: Closing Speech + IB Concept Badge

| Aspect | Specification |
|---|---|
| **Purpose** | Name the IB key concept(s) explored. Plant a seed for continued curiosity. |
| **LLM must do** | 1. Name `{ib_key_concepts}` naturally in a sentence (not as a vocabulary drill). 2. Connect the concept to what the child experienced. 3. Future hook: "Next time you see a [related thing], think about..." 4. Warm goodbye. |
| **Concept count** | T0: 1 concept \| T1: 2 concepts \| T2: up to 3 concepts |
| **Screen widget** | `badge_award`: Concept name(s) displayed as artistic text, with an icon representing the concept. |
| **Example (pineapple, T1)** | AI: "Today you discovered that things aren't always what they seem — that's called **Form**. And you found surprising connections between a pineapple and the world around it — that's **Connection**! Next time you eat something yummy, think about where it might have traveled from. See you next time, Detective!" |
| **Anti-pattern** | ❌ "The IB key concept we learned today is Form, which means..." — this is too didactic. Name the concept, but embed it in the experience. |

---

## 5. Template B: Category 5 — Out-of-Device Collection/Exploration

> **📸 Category 5 at a Glance**
>
> - **Type**: 收集/跟拍探索类 (collection/tracking exploration). Requires multiple photos.
> - **Core mechanic**: Child goes on a mini-mission to find and photograph related objects.
> - **Duration**: 5–12 minutes depending on tier and environment.
> - **Hardware**: Camera is essential. Child takes 2–4 additional photos during the activity.
> - **Environment**: Designed for outdoor or room-scale exploration.

### 5.1 Template-Specific Slots

| Slot Name | Type | LLM Instruction | Example (entity = leaf) |
|---|---|---|---|
| `{observation_angle}` | enum | Choose ONE visual/sensory feature to anchor the mission: `color`, `shape`, `texture`, `size`, `pattern`, `function`, `habitat` | "shape" |
| `{collection_criterion}` | string | The specific rule for what to collect, derived from `{observation_angle}` | "Find 3 leaves with completely different shapes" |
| `{collection_count}` | int | Number of items to find. T0: 2 \| T1: 3 \| T2: 3–4 | 3 |
| `{mission_metaphor}` | string | A playful frame for the collection mission | "You are a Shape Detective on a secret leaf mission!" |
| `{role_title}` | string | Fun title awarded at the end | "Leaf Shape Specialist" |
| `{synthesis_type}` | enum | What to do with the collection: `naming_story`, `comparison_chart`, `creative_narrative`, `sorting_game` | "naming_story" |
| `{stuck_hint}` | string | Hint for where to look if the child can't find items | "Try looking near the flower bed or under big trees — leaves love to hide there!" |
| `{naming_prompt}` | string | Prompt for child to name/characterize each collected item | "What shape does this leaf remind you of? Give it a fun name!" |

### 5.2 Step-by-Step Flow

---

#### Step 1: Transition Bridge (Observation Hook)

| Aspect | Specification |
|---|---|
| **Purpose** | Draw the child's attention to a specific visual feature of the photographed entity. Create wonder about that feature. |
| **LLM must do** | 1. Point out `{observation_detail}` with genuine curiosity. 2. Ask an IMAGINATIVE question about that feature (not factual). 3. Use `{observation_angle}` to frame what's interesting. 4. The question should naturally lead to "I wonder if there are more like this..." |
| **Screen widget** | `photo_display`: Uploaded photo with the observed feature area highlighted (soft circle overlay). |
| **Difference from Cat 1** | Cat 1 hook leads to a GAME. Cat 5 hook leads to a MISSION. The hook must make the child curious about variety/diversity, not just the single entity. |
| **Example (leaf, T1)** | AI: *(curious)* "Look at this leaf — it's shaped like a little heart! I wonder... do ALL leaves have the same shape? Or does every leaf have its own special shape? What do you think?" |

---

#### Step 2: Mission Briefing

| Aspect | Specification |
|---|---|
| **Purpose** | Assign a clear, exciting collection mission with specific instructions. |
| **LLM must do** | 1. Introduce `{mission_metaphor}` to make it feel like an adventure. 2. State `{collection_criterion}` as a clear 1–2 sentence mission. 3. State `{collection_count}` explicitly. 4. Give step-by-step instructions: find → photograph → come back. 5. Encourage: "Take your time, there's no rush!" |
| **Screen widget** | `notebook_page`: Display a mission card with: mission title (from `{mission_metaphor}`), checklist with `{collection_count}` empty slots, collection rule in simple words. |
| **Critical: mission must be achievable** | The LLM must consider the entity's likely environment. If entity is a leaf → outdoor, find other leaves. If entity is a toy car → indoor, find other toys. The mission must match the probable context. |
| **Example (leaf, T1)** | AI: *(adventurous)* "You are now a Shape Detective! Your mission: explore the area and find 3 leaves that have completely DIFFERENT shapes. Each leaf needs its own special shape. When you find one, take a photo and bring it back to show me! Ready? Go explore!" |

---

#### Step 3: Multi-Round Exploration (Photo Collection)

| Aspect | Specification |
|---|---|
| **Purpose** | The child explores, finds items, and photographs them. Each photo triggers an AI response. |
| **Round count** | Equal to `{collection_count}`. Each photo = one round. |
| **LLM must do per round** | 1. React to the new photo with genuine excitement. 2. Ask `{naming_prompt}` — have the child describe/name this item. 3. Connect it to previous items: "This one is so different from your first one!" 4. Update progress: "That's 2 out of 3!" 5. If NOT the last round, encourage continuing: "One more to go!" |
| **If child is stuck** | After 60s with no photo, AI offers `{stuck_hint}`. After another 60s, AI suggests simplifying the criterion or accepting what they have. |
| **Screen widget** | `progress_tracker`: Visual slots that fill as photos arrive. Each slot shows a thumbnail of the collected photo. |
| **Photo response format** | The AI's response to each photo should follow this structure: 1. Exclamation about the photo (1 sentence). 2. Observation about `{observation_angle}` in this item (1 sentence). 3. Naming prompt (1 question). 4. Progress update (1 sentence). |
| **Example (leaf, T1, round 2 of 3)** | AI: *(delighted)* "Oh, this one is long and thin like a feather! Totally different from your heart-shaped leaf. What would you name this leaf? ... That's 2 out of 3 Shape Detective finds! One more unique shape to discover!" |

---

#### Step 4: Collection Complete — Synthesis

| Aspect | Specification |
|---|---|
| **Purpose** | All items collected. Now make meaning from the collection through creative synthesis. |
| **LLM must do** | 1. Celebrate the complete collection. 2. Depending on `{synthesis_type}`, guide one creative activity: `naming_story` → Child gives each item a character name, AI weaves a micro-story. `comparison_chart` → AI guides child to describe how items are similar/different. `creative_narrative` → AI starts a story starring the collected items, child adds to it. `sorting_game` → AI proposes categories, child sorts their collection. 3. This step should take 1–2 turns max. |
| **Screen widget** | `photo_grid`: Show all collected photos in a grid with their names/labels. Optional: `animation_overlay` (sparkle) on the completed grid. |
| **Synthesis selection logic** | LLM should choose based on entity + tier: T0 → `naming_story` (simplest). T1 → `naming_story` or `comparison_chart`. T2 → `creative_narrative` or `sorting_game`. |
| **Example (leaf, T1, naming_story)** | AI: *(storyteller voice)* "Look at your three shape detective finds all together! Heart Leaf, Feather Leaf, and Star Leaf. If these three leaves went on an adventure together, what would happen? ... I love it! The heart leaf would definitely be the kindest one in the group!" |

---

#### Step 5: Discovery Celebration + Role Title

| Aspect | Specification |
|---|---|
| **Purpose** | Celebrate the exploration. Award role title. |
| **LLM must do** | 1. Praise the exploration process (not just the result). 2. Highlight one specific moment from the journey. 3. Award `{role_title}`. 4. Mention what was discovered about `{observation_angle}`: "You proved that [entity] come in SO many different [observation_angle]s!" |
| **Screen widget** | `badge_award` with confetti `animation_overlay`. |
| **Example (leaf, T1)** | AI: "You are now an official Leaf Shape Specialist! You proved that even on the same street, leaves come in SO many amazing shapes. My favorite moment was when you named that star-shaped one — brilliant!" |

---

#### Step 6: Closing Speech + IB Concept Badge

| Aspect | Specification |
|---|---|
| **Purpose** | Name IB concepts. Plant curiosity seed for next time. |
| **LLM must do** | Same structure as Cat 1 Step 5. Name `{ib_key_concepts}` embedded in experience. Future hook about looking at the world differently. |
| **Typical IB concepts for Cat 5** | Form (observing visual features), Connection (linking different items), Change (noticing variety), Causation (why things look different) |
| **Example (leaf, T1)** | AI: "Today you explored **Form** — the amazing shapes that nature creates. And you found **Connection** between leaves that look totally different but all belong to the same world. Next time you're outside, look at the shapes of clouds, rocks, or even puddles. The world is full of shapes waiting for your detective eye! Bye for now, Shape Specialist!" |

---

## 6. LLM System Prompt Integration Guide

The demo backend injects the template into the Gemini system prompt. Here is the recommended prompt structure:

```
## SECTION 1: Role & Persona
You are Zigzag, WonderLens's AI companion for children. [tier-specific personality rules]

## SECTION 2: Tier Rules
[Inject tier_rules table as constraints]

## SECTION 3: Activity Template
[Inject the chosen template (Cat 1 or Cat 5) with all slot definitions]

## SECTION 4: Vision Context
The child just photographed: {entity_name} ({entity_category}).
Visual attributes: {entity_attributes}.
Probable environment: {inferred_environment}.

## SECTION 5: Output Format
Each response must include:
(tone_marker) Dialogue text

[SCREEN] widget: <type> | description: <what to show> | animation: <optional>
[AUDIO] sfx: <sound_id> | timing: <when>

## SECTION 6: Conversation State
Current step: {current_step} of {total_steps}
Rounds completed: {rounds_done} of {rounds_total}
[Previous conversation history injected here]
```

### 6.1 Slot Population Order

The backend should populate slots in this order:

| Step | Action | Data Source |
|---|---|---|
| 1 | Run vision on uploaded image | Gemini Vision API |
| 2 | Extract `entity_name`, `entity_category`, `entity_attributes` | Vision API response |
| 3 | Map entity to IB theme, key concepts, related concepts | IB mapping table (or LLM inference for unknown entities) |
| 4 | Select template (Cat 1 or Cat 5) based on demo UI selection | User selection |
| 5 | Inject all populated slots into system prompt | Template + vision + mapping |
| 6 | Let LLM fill remaining creative slots (`game_mechanic`, `metaphor`, etc.) in its first response | LLM generation |

### 6.2 Critical: LLM Must Self-Fill Creative Slots

The creative slots (`{game_mechanic}`, `{metaphor}`, `{role_title}`, etc.) are **not pre-filled by the backend**. The system prompt instructs the LLM to choose them in its first turn based on the entity context. This ensures maximum creativity and entity-appropriateness.

However, the system prompt **constrains the choices** via the enum values listed in the slot definitions. The LLM must pick from the allowed set, not invent new mechanics.

---

## 7. Frontend State Machine Mapping

The frontend state machine tracks which template step is active and what widget to render.

### 7.1 Cat 1 State Machine

| State | Template Step | Primary Widget | Transitions To |
|---|---|---|---|
| `PHOTO_UPLOAD` | — | — | `VISION_RESULT` |
| `VISION_RESULT` | — | `photo_display` | `STEP_1_HOOK` |
| `STEP_1_HOOK` | Step 1: Transition | `photo_display` + `animation_overlay` (glow) | `STEP_2_RULES` |
| `STEP_2_RULES` | Step 2: Game Intro | `character_display` | `STEP_3_ROUND_1` |
| `STEP_3_ROUND_N` | Step 3: Round N | `character_display` (emotion changes) | `STEP_3_ROUND_N+1` or `STEP_4_CELEBRATE` |
| `STEP_4_CELEBRATE` | Step 4: Celebration | `badge_award` + `animation_overlay` (confetti) | `STEP_5_CLOSING` |
| `STEP_5_CLOSING` | Step 5: IB Closing | `badge_award` (concept text) | `ENDED` |
| `EARLY_EXIT` | Silence exit | `badge_award` (partial) | `ENDED` |

### 7.2 Cat 5 State Machine

| State | Template Step | Primary Widget | Transitions To |
|---|---|---|---|
| `PHOTO_UPLOAD` | — | — | `VISION_RESULT` |
| `VISION_RESULT` | — | `photo_display` | `STEP_1_HOOK` |
| `STEP_1_HOOK` | Step 1: Observation | `photo_display` + highlight overlay | `STEP_2_MISSION` |
| `STEP_2_MISSION` | Step 2: Mission Brief | `notebook_page` (mission card) | `STEP_3_COLLECT_1` |
| `STEP_3_COLLECT_N` | Step 3: Photo N | `progress_tracker` (N of `{collection_count}`) | `STEP_3_COLLECT_N+1` or `STEP_4_SYNTHESIS` |
| `STEP_4_SYNTHESIS` | Step 4: Synthesis | `photo_grid` (all collected) | `STEP_5_CELEBRATE` |
| `STEP_5_CELEBRATE` | Step 5: Celebration | `badge_award` + confetti | `STEP_6_CLOSING` |
| `STEP_6_CLOSING` | Step 6: IB Closing | `badge_award` (concept text) | `ENDED` |
| `EARLY_EXIT` | Silence or stuck exit | `badge_award` (partial) | `ENDED` |

### 7.3 Widget Priority for Demo

For the demo, implement these widgets first (covers both templates):

| Widget | Used In | Priority |
|---|---|---|
| `photo_display` | Both templates (hook step, vision result) | P0 |
| `character_display` | Cat 1 (Steps 2–3) | P0 |
| `progress_tracker` | Cat 5 (Step 3 collection rounds) | P0 |
| `badge_award` | Both templates (Steps 4–5/6) | P0 |
| `animation_overlay` | Both templates (celebrations, glow) | P1 |
| `notebook_page` | Cat 5 (Step 2 mission card) | P1 |
| `photo_grid` | Cat 5 (Step 4 synthesis) | P1 |

---

## 8. Example: Full Walkthrough with Arbitrary Entity

To demonstrate the templates in action, here are complete walkthroughs for entities NOT in the original design document.

### 8.1 Cat 1 Example: User uploads a photo of a red sneaker

**Vision Result:**
- `entity_name`: sneaker / running shoe
- `entity_category`: clothing_accessory
- `entity_attributes`: [red, white sole, laces, worn, outdoor]
- Selected tier: T1

**LLM-Filled Slots:**

| Slot | Value |
|---|---|
| `{game_mechanic}` | `voice_acting` |
| `{metaphor}` | "This sneaker has been on SO many adventures — look how well-loved it is!" |
| `{role_title}` | "Sneaker Whisperer" |
| `{observation_detail}` | "the red color and those laces tied in a bow" |
| `{escalation_axis}` | "scenarios go from everyday to fantastical" |
| `{round_scenarios}` | ["walking in rain puddles", "running a race against a bicycle", "landing on the moon"] |
| `{ib_key_concepts}` | ["Perspective", "Connection"] |

**Conversation Flow:**

**Step 1 (Hook):** AI: *(excited)* "Whoa, check out this sneaker! It's SO red — like a racing car for your foot! And look at those laces tied up in a perfect bow. If this sneaker could talk, what do you think it would tell us about its day?"

**Step 2 (Rules):** AI: "I bet this sneaker has LOTS of stories. Here's our game: I'll describe a scene, and you tell me what the sneaker would SAY. Like this — if the sneaker was sitting in a closet all day, it might say: 'Is it adventure time yet? I'm SO bored!' Now your turn!"

**Step 3, Round 1:** AI: *(playful)* "Okay! The sneaker just jumped into a big rain puddle — SPLASH! What does it say?" Child: "Brr, that's cold!" AI: "Haha, 'Brr, that's cold!' I bet it's wiggling its laces trying to shake off the water! Great one!"

**Step 3, Round 3:** AI: *(mysterious)* "This time... the sneaker has just landed on the MOON. There's no gravity. It's floating! What does the moon-sneaker say?"

**Step 4:** AI: "You are now the official Sneaker Whisperer! You heard everything from puddle splashes to moon landings. Amazing imagination!"

**Step 5:** AI: "Today you explored **Perspective** — seeing the world through a sneaker's eyes! And you found **Connection** between a shoe and rain, races, and even the moon. Keep your sneaker-whispering powers ready!"

---

### 8.2 Cat 5 Example: User uploads a photo of a park bench

**Vision Result:**
- `entity_name`: park bench / wooden bench
- `entity_category`: furniture_outdoor
- `entity_attributes`: [wooden, green paint, metal legs, outdoor, park setting]
- Selected tier: T2

**LLM-Filled Slots:**

| Slot | Value |
|---|---|
| `{observation_angle}` | texture (the materials things are made of) |
| `{collection_criterion}` | "Find 3 things made of completely different materials near this bench" |
| `{collection_count}` | 3 |
| `{mission_metaphor}` | "You are a Material Scientist investigating what the park is made of!" |
| `{role_title}` | "Park Material Scientist" |
| `{synthesis_type}` | `comparison_chart` |
| `{stuck_hint}` | "Look at the ground, the playground, or any structures nearby — each one might be a different material!" |
| `{ib_key_concepts}` | ["Form", "Function", "Connection"] |

**Conversation Flow:**

**Step 1 (Hook):** AI: *(curious)* "This bench is interesting — look, the seat part is made of WOOD and it's painted green, but the legs are shiny METAL. That's two different materials in one bench! I wonder what other materials are hiding around here..."

**Step 2 (Mission):** AI: "You are now a Material Scientist! Your mission: investigate this area and find 3 things made of completely different materials. Your bench has wood and metal already — what else is out there? Photograph each discovery!"

**Step 3, Round 1:** [Child photographs a rubber swing seat] AI: "Excellent find, Scientist! That swing seat is made of rubber — bendy and tough. Totally different from the hard wood of your bench. What does it feel like when you touch it? 1 of 3 discoveries logged!"

**Step 4 (Synthesis):** AI: "Let's compare your 3 discoveries! The bench is wood — natural, hard, can rot. The swing is rubber — bendy, waterproof. The slide is plastic — smooth, light. Why do you think each thing is made of its specific material? Could you make a bench out of rubber?"

**Step 6 (Closing):** AI: "You explored **Form** — what materials look and feel like. You discovered **Function** — why each material is chosen for its job. And you found **Connection** — everything in this park works together! Keep investigating, Material Scientist!"
