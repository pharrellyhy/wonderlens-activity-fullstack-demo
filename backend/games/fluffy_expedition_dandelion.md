---
activity_type: fluffy_expedition_dandelion
entity_name: dandelion
category: category_5
display_label: Dandelion
tier: T0
ib_theme: "Sharing the Planet"
ib_key_concept: Connection
concepts_earned: [Connection]
keywords: [dandelion, flower]
feature_keywords: [fluffy, dandelion, soft, fuzzy]
photo_features: [white fluffy seeds, round seed head, thin stem, delicate structure]

creative_slots:
  observation_angle: texture
  collection_criterion: "Find things that are fluffy, fuzzy, or soft"
  collection_count: 3
  mission_metaphor: "You are a Fluffy Expedition Explorer!"
  role_title: Fluffy Expedition Explorer
  synthesis_type: naming_story
  stuck_hint: "Try touching things around you — look for anything soft or fuzzy"
  naming_prompt: "What would you name this fluffy friend?"
  detail_question_template: "What does this fluffy thing remind you of?"
  sorting_criterion: ""

collection_catalog:
  correct:
    - id: fuzzy_moss
      label: Fuzzy moss
      image: /icons/fuzzy_moss.png
    - id: fluffy_seed
      label: Fluffy seed head
      image: /icons/fluffy_seed.png
    - id: soft_petal
      label: Soft petal
      image: /icons/soft_petal.png
    - id: woolly_caterpillar
      label: Woolly caterpillar
      image: /icons/woolly_caterpillar.png
  distractors:
    - id: hard_rock
      label: Hard rock
      image: /icons/hard_rock.png
    - id: spiky_pinecone
      label: Spiky pinecone
      image: /icons/spiky_pinecone.png
    - id: rough_bark
      label: Rough bark
      image: /icons/rough_bark.png
    - id: sharp_thorn
      label: Sharp thorn
      image: /icons/sharp_thorn.png
    - id: dry_leaf
      label: Dry crunchy leaf
      image: /icons/dry_leaf.png
    - id: smooth_pebble
      label: Smooth pebble
      image: /icons/smooth_pebble.png
    - id: stiff_branch
      label: Stiff branch
      image: /icons/stiff_branch.png
    - id: brittle_shell
      label: Brittle shell
      image: /icons/brittle_shell.png

step_instructions:
  hook:
    goal: "React with wonder to the dandelion's fluffiness — notice its white seeds like tiny parachutes, then ask the child an IMAGINATIVE question about what the seeds look like or what they might do (e.g. 'Where do you think all those tiny parachutes are going to fly to?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an imaginative question about the fluffiness"
    emotion_tag: excited
  transition:
    goal: "Build on the child's response to NATURALLY introduce the Fluffy Expedition Explorer mission — the dandelion isn't the only soft thing around! Frame the collection as an explorer adventure. Invite the child to find 3 more fluffy/fuzzy/soft things nearby. End with a genuine invitation."
    constraint: "T0 max 2 sentences, build mission from child's response (not a sudden topic switch), frame as invitation not command, end with Would you like to be the explorer?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Spark curiosity about finding the first fluffy item — suggest WHERE to look or WHAT to touch as an invitation, then ask the child to describe HOW it feels (fuzzy? silky? puffy?)"
      scenario: "first fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, encourage the child to describe the texture"
      emotion_tag: encouraging
      acceptable_themes: [cloud, cotton, fur, feather, wool, moss, grass, blanket, fluffy, soft, fuzzy]
      escalation_note: "easy first find — common soft items"
    - round_number: 2
      goal: "Celebrate the previous find, then spark curiosity for the next — ask child to COMPARE how this one feels different from the first (softer? fuzzier? more like a cloud?), suggest a new place to look"
      scenario: "second fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, encourage comparison between textures"
      emotion_tag: curious
      acceptable_themes: [pet, pillow, carpet, sweater, plush, stuffed, teddy, hair, soft, fuzzy, fluffy]
      escalation_note: "moderate — requires more exploration"
    - round_number: 3
      goal: "Guide child to find one more fluffy or soft item — the third and last one. Build excitement but remind them they still need to FIND it. Ask them to give this treasure a fun name."
      scenario: "third fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, prompt child to go find it"
      emotion_tag: excited
      acceptable_themes: [cloud, cotton, feather, moss, flower, seed, fluffy, soft, fuzzy, fur, wool]
      escalation_note: "peak energy — but child still needs to find this item"
  celebrate:
    goal: "Award the child the title 'Fluffy Expedition Explorer' with ceremony — recap their soft discoveries. Celebrate the PROCESS of touching and feeling different textures."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific finds from the expedition"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: they found soft treasures all connected by fluffiness — that's the beauty of Connection (finding how different things are linked together). Plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Connection naturally connected to what they discovered, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: "Look at all fluffy treasures together — guide a comparison: how does softness come in DIFFERENT forms? Fuzzy vs silky vs puffy. Invite child to give each find a fun texture name (e.g. 'cloud puff', 'fuzzy friend')."
    constraint: "T0 max 2 sentences, comparison + creative naming, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: "Gentle goodbye — wonderful fluffy expedition, soft treasures will be waiting for their next adventure"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Dandelion photo centered with seeds gently floating"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Fluffy Dandelion"
    animation_label: "Seeds floating"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 4
    animation: card_slide_in
    trigger: on_round_1
    sfx_cue: photo_shutter_click
    widget_label: "Find 1: First Fluffy"
    animation_label: "Card slide in"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 4
    animation: celebration_burst
    trigger: on_round_2
    sfx_cue: photo_shutter_click
    widget_label: "Find 2: More Fluff"
    animation_label: "Collection burst"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 4
    animation: celebration_burst
    trigger: on_round_3
    sfx_cue: mission_complete_fanfare
    widget_label: "Find 3: Final Fluff"
    animation_label: "Collection burst"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Fluffy Expedition Explorer"
    concepts: [Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## The Fluffy Expedition

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Fluffy Expedition |
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | T0 (ages 2–4) |
| Core IB Key Concepts | Connection |
| Related Concepts | Discovery, Sensory Awareness, Nature, Texture |
| ATL Skills Focus | Research Skills (observation, data collection), Communication Skills (describing, naming) |
| Game Style | naming_story |

### B. Activity Overview

**① Brief Description**

After the child photographs a dandelion, the AI gasps at all those tiny white parachutes and wonders where they might fly. The child becomes a "Fluffy Expedition Explorer" — venturing out to find 3 things nearby that feel fluffy, fuzzy, or soft. Each discovery invites touch: how does it feel? Is it silky? Puffy? Fuzzy like a cloud? After collecting all three, the child gives each find a character name (like "Cloud Puff" or "Fuzzy Friend") and tells a tiny story about the fluffy friends meeting each other. Softness connects everything!

**② Educational Purpose (KUD)**

- **K (Know):** Learn that dandelion seeds are fluffy and float away like tiny parachutes. Learn that "soft" comes in many forms — fuzzy, silky, puffy, woolly. Learn that touching things tells you about their texture. Learn the names for different kinds of softness.
- **U (Understand):** Understand that many different things share the quality of softness — a dandelion seed, moss, a petal, and a caterpillar can all feel fluffy even though they look nothing alike. That is Connection — finding how different things are linked together through something they share.
- **D (Do):** Practice exploring textures through touch — feeling for softness in the environment. Practice comparing how different things feel (fuzzier vs. silkier vs. puffier). Practice giving creative names to found objects and building a simple story from them.

**③ Design Highlight**

The naming_story synthesis transforms a texture scavenger hunt into character creation and storytelling. Each fluffy find earns a texture-inspired name the child invents — "Cloud Puff," "Fuzzy Friend," "Silky Petal." The final story moment — "What do your fluffy friends do when they meet?" — lets even a 2-year-old become a storyteller, weaving their three named characters into a tiny narrative. The dandelion itself is the first fluffy friend, anchoring the expedition in something the child already touched and wondered about.

**④ Typical Scenario**

Child photographs a dandelion → AI marvels at the fluffy seeds → child becomes a "Fluffy Expedition Explorer" → finds and touches 3 fluffy/fuzzy/soft things → names each one as a character → tells a tiny story about the fluffy friends meeting → celebrates with a Fluffy Expedition Explorer badge.

### C. Interaction Flow

> Recommended Tier: T0 (ages 2–4)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Ooh! Look at all those tiny fluffy parachutes! Where do you think they're going to fly to?"

**Child responses:**

1. (Ideal) "Up!" / "To the sky!" / "Far away!" / child blows on the dandelion
2. (Unexpected) "It's a flower!" / "White!" / "I want to pick it!"
3. (No response) Child looks at the dandelion photo quietly.

**AI follow-up:**

1. (amazed) "Up to the sky! Tiny fluffy flyers! I wonder — is the dandelion the only soft thing here?"
2. (warm, accepting) "It IS a flower! A fluffy one! All those soft little seeds. Would you like to find more fluffy things?"
3. (wait 2s) (soft, playful) "So fluffy! Like tiny clouds. Touch the screen — can you feel how soft it looks?"

**Screen:** Dandelion photo centered with seeds gently floating upward in a slow drift animation; warm sparkle highlights on the seed head and a soft wonder chime.

#### Step 2: Rule Introduction + Demo

**AI says:** (excited, playful) "You are a Fluffy Expedition Explorer! Would you like to find 3 soft, fluffy things? Touch them and tell me how they feel!"

**Child responses:**

1. (Ideal) "Yeah!" / "I want to find fluffy!" / child starts looking around
2. (Unexpected) "What's fluffy?" / "Like what?"
3. (No response) Child looks around slowly.

**AI follow-up:**

1. (cheering) "Go go, Explorer! Find something soft and fluffy!"
2. (helpful, warm) "Fluffy means soft! Like clouds. Like the dandelion. Would you like to touch things and feel for softness?"
3. (wait 2s) (encouraging) "Look around! Maybe a leaf? Or some grass? Would you like to touch something and see if it feels soft?"

**Screen:** Mission card with "Fluffy Expedition Explorer" badge (dandelion icon with floating seeds), 4 slots (first filled with dandelion photo, 3 empty with cloud-puff placeholders), and a "Find 3!" counter.

#### Step 3: Multi-Round Interaction

**Round 1 — First Fluffy Find:**

*(Child touches/finds something soft nearby — e.g., moss, a fuzzy leaf, soft grass, a feather)*

**AI says:** (excited discovery) "Ooh! You found something! How does it feel?"

**Child responses:**

1. (Ideal) "Soft!" / "Fuzzy!" / "Like a cloud!" / child describes the texture
2. (Unexpected) "It's green!" / "I found it!" / doesn't describe texture
3. (No response) Child holds the soft thing quietly.

**AI follow-up:**

1. (delighted) "So soft! Like the dandelion! Your first fluffy treasure! 2 more to find!"
2. (warm, scaffolding) "You found it! Now touch it gently. Is it fuzzy? Or silky? Or puffy like a cloud?"
3. (wait 2s) (warm) "Touch it softly. How does it feel on your fingers? Fuzzy? Smooth? That's your first fluffy treasure!"

**Screen:** Photo slides into slot 2 with a card-slide-in animation and a shutter click sound; progress tracker updates to "1 of 3 found."

**Round 2 — Second Fluffy Find:**

*(Child finds another soft/fuzzy/fluffy thing — e.g., a soft petal, woolly caterpillar, plush toy left outside)*

**AI says:** (curious) "Another one! Does this one feel the same as the first?"

**Child responses:**

1. (Ideal) "Softer!" / "This one is fuzzier!" / "It's different!" / child compares
2. (Unexpected) "It's pretty!" / "I like this one!" / doesn't compare
3. (No response) Child touches the new find silently.

**AI follow-up:**

1. (amazed) "Fuzzier! So soft comes in different ways! 1 more fluffy treasure to find!"
2. (warm, guiding) "So pretty! Now feel both — is this one softer? Or fuzzier? Softness can feel different!"
3. (wait 2s) (gentle) "Touch it and then touch your first find. Which one is fuzzier? Every soft thing feels a little different!"

**Screen:** Photo slides into slot 3 with a celebration-burst animation and a shutter click; progress tracker updates to "2 of 3 found."

**Round 3 — Third Fluffy Find:**

*(Child finds the last fluffy/soft thing — e.g., a fluffy seed head, soft moss, a downy feather)*

**AI says:** (thrilled) "The last fluffy treasure! Would you like to give this one a fun name?"

**Child responses:**

1. (Ideal) "Cloud Puff!" / "Fuzzy!" / "Softie!" / child invents a name
2. (Unexpected) "It's soft!" / "I found it!" / doesn't name it
3. (No response) Child holds the find with a smile.

**AI follow-up:**

1. (celebrating) "[Name]! I love that! All 3 fluffy treasures found! You did it!"
2. (warm, scaffolding) "So soft! What would you call this fluffy friend? Maybe Puffy? Or Cloudy? What name do you like?"
3. (wait 2s) (playful) "This fluffy friend needs a name! Something soft and fun. What about Cloud Puff? Or you pick!"

**Screen:** Photo slides into slot 4 with a celebration-burst animation and a mission-complete fanfare; progress tracker shows "3 of 3 found!"

**STUCK BRANCH:** "Try touching things around you — look for anything soft or fuzzy! Maybe some grass? Or a flower petal? Would you like to feel that?"

#### Step 4: Celebration (Synthesis)

**AI says:** (amazed, storytelling voice) "Look at all your fluffy treasures! Each one feels different — fuzzy, silky, puffy! Would you like to give each one a texture name?"

**Child responses:**

1. (Ideal) "Cloud Puff!" / "Fuzzy Friend!" / child names the finds
2. (Unexpected) "They're all soft!" / "I like them!" / doesn't name
3. (No response) Child looks at the collection quietly.

**AI follow-up:**

1. (delighted, narrating) "Cloud Puff, Fuzzy Friend, and [Name 3]! Three fluffy friends! What happens when they all meet?"
2. (warm, scaffolding) "All soft! Maybe this fuzzy one is Fuzzy Friend? And this silky one is Silky Star? Would you like to pick names?"
3. (wait 2s) (gentle, playful) "How about Cloud Puff for the puffy one? And Fuzzy Friend for the fuzzy one? Now — what do they do when they meet?"

**Child tells a tiny story** (or AI scaffolds): "They play!" / "They have a soft party!" / "They cuddle!"

**AI response to story:** (celebrating) "A fluffy party! Cloud Puff and Fuzzy Friend and [Name 3] all cuddle together. The softest story ever!"

**Screen:** All 4 photos displayed in a circle (dandelion in center) with soft wispy lines connecting them; character name tags beneath each find; a storybook frame with floating seed animations and a "Fluffy Friends" banner.

**AI says:** (proud, ceremonial) "You are officially a Fluffy Expedition Explorer! You found softness in so many places!"

**Child responses:**

1. (Engaged) "Yay!" / "I'm an explorer!" / "More fluffy!"
2. (Quiet) Child smiles or claps.

**AI follow-up:**

1. (celebration) "The best Fluffy Expedition Explorer! You found softness everywhere!"
2. (gentle) "What a wonderful expedition. You touched so many soft treasures!"

**Screen:** Badge spinning into center labeled "Fluffy Expedition Explorer" with dandelion and floating-seed motif; collection photos as small insets; "Connection" in soft pastel lettering; seed-puff confetti drifting down.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, proud) "Fluffy Expedition Explorer, you did something amazing! You found soft treasures all connected by fluffiness — a dandelion, and all your fluffy friends. That's Connection — finding how different things are linked together! Softness connects them all!"

**Child responses:**

1. (Engaged) "Soft is everywhere!" / "I want more!" / "Fluffy!"
2. (Quiet) Child waves or smiles at the screen.

**AI follow-up:**

1. (warm) "Softness IS everywhere! Next time, feel for more. Bye bye, Fluffy Explorer!"
2. (gentle) "You were a wonderful explorer today. Bye bye, Fluffy Explorer!"

**Screen:** Badge centered with "Fluffy Expedition Explorer" title and dandelion motif; collection photos as small insets around the badge; "Connection" in soft cloud-colored lettering; dandelion seeds float gently across the screen as a closing animation.
