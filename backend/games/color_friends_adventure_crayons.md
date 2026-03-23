---
activity_type: color_friends_adventure_crayons
entity_name: crayons
category: category_5
display_label: Crayons
tier: T0
ib_theme: Sharing the Planet
ib_key_concept: Connection
concepts_earned: [Connection, Perspective]
keywords: [crayons, colors, drawing, art]
feature_keywords: [color, bright, smooth, waxy]
photo_features: [bright colors, waxy texture, paper wrapper, pointed tip]
creative_slots:
  observation_angle: color
  collection_criterion: Find things that match your favorite crayon color
  collection_count: 2
  mission_metaphor: You are a Color Scout!
  role_title: Color Scout
  synthesis_type: naming_story
  stuck_hint: Look at flowers or leaves, colors love to hide there!
  naming_prompt: What should we name this color friend?
collection_catalog:
  correct:
  - id: red_flower
    label: Red flower
    image: /icons/red_flower.png
  - id: green_leaf
    label: Green leaf
    image: /icons/green_leaf.png
  - id: yellow_dandelion
    label: Yellow dandelion
    image: /icons/yellow_dandelion.png
  - id: blue_berry
    label: Blue berry
    image: /icons/blue_berry.png
  distractors:
  - id: clear_puddle
    label: Clear puddle
    image: /icons/clear_puddle.png
  - id: brown_dirt
    label: Brown dirt
    image: /icons/brown_dirt.png
  - id: gray_gravel
    label: Gray gravel
    image: /icons/gray_gravel.png
  - id: dry_twig
    label: Dry twig
    image: /icons/dry_twig.png
  - id: dead_leaf
    label: Dead leaf
    image: /icons/dead_leaf.png
  - id: plain_sand
    label: Plain sand
    image: /icons/plain_sand.png
  - id: white_cloud
    label: White cloud
    image: /icons/white_cloud.png
  - id: shadow
    label: Shadow
    image: /icons/shadow.png
step_instructions:
  hook:
    goal: React with delight to the bright crayons and ask the child which color is their favorite.
    constraint: T0 max 2 sentences, simple vocabulary, end with a choice.
    emotion_tag: excited
  transition:
    goal: Invite the child to become a Color Scout and find 2 things outside that match their favorite color.
    constraint: T0 max 2 sentences, frame as an invitation, use the Color Scout metaphor.
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: Celebrate the first color match and invite the child to give this new color friend a name.
    scenario: first color match found
    constraint: T0 max 2 sentences, invitational phrasing, prompt for a name.
    emotion_tag: encouraging
    acceptable_themes: [flower, leaf, color, red, blue, green, yellow, name]
    escalation_note: easy first find
  - round_number: 2
    goal: Celebrate the second color match, ask for its name, and cheer that the collection is complete.
    scenario: second color match found
    constraint: T0 max 2 sentences, invitational phrasing, prompt for a name.
    emotion_tag: excited
    acceptable_themes: [rock, berry, bucket, color, red, blue, green, yellow]
    escalation_note: final find, completes the set
  celebrate:
    goal: Award the Color Scout badge and celebrate how the child found colors hiding in the world.
    constraint: T0 max 2 sentences, announce role title ceremonially.
    emotion_tag: proud
  closing:
    goal: Mention how the crayon and the world share a Connection through color, and say a warm goodbye.
    constraint: T0 max 2 sentences, name Connection naturally, warm goodbye.
    emotion_tag: warm
  early_exit:
    goal: Say a gentle goodbye and remind them their color friends will be waiting.
    constraint: T0 max 2 sentences, no pressure.
    emotion_tag: gentle
  synthesis:
    goal: Look at the named color friends together and invite the child to tell a tiny story about them playing.
    constraint: T0 max 2 sentences, encourage a simple story or action.
    emotion_tag: amazed
screen_frames:
- widget: photo_display
  widget_params:
    description: Crayon photo centered with each crayon gently pulsing in its own color glow
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Colorful Crayons
  animation_label: Sparkle highlight
- widget: progress_tracker
  widget_params:
    filled: 1
    total: 3
  animation: card_slide_in
  trigger: on_round_1
  sfx_cue: photo_shutter_click
  widget_label: 'Find 1: First Color Friend'
  animation_label: Card slide in
- widget: progress_tracker
  widget_params:
    filled: 2
    total: 3
  animation: celebration_burst
  trigger: on_round_2
  sfx_cue: mission_complete_fanfare
  widget_label: 'Find 2: Second Color Friend'
  animation_label: Collection burst
celebration_frame:
  widget: badge_award
  widget_params:
    title: Color Scout
    concepts: [Connection, Perspective]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## The Color Friends Adventure

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Color Friends Adventure |
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | T0 (ages 2–4) |
| Core IB Key Concepts | Connection, Perspective |
| Related Concepts | Creativity, Expression, Discovery, Symbolism |
| ATL Skills Focus | Research Skills (observation, data collection), Communication Skills (expressing) |
| Game Style | naming_story |

### B. Activity Overview

**① Brief Description**

After the child photographs their crayons outside, the AI notices all the bright colors and wonders if those same colors are hiding in the yard. The child becomes a "Color Scout" — picking a favorite crayon color, then searching for 2 things nearby that match it. Each find gets a character name (like "Sunny Leaf" or "Grassy Rock"), and at the end the child tells a tiny story about their color friends meeting each other. Colors connect the crayon to the world!

**② Educational Purpose (KUD)**

- **K (Know):** Learn that crayons come in many bright colors. Learn that crayons feel smooth and waxy. Learn that the same color can appear on many different things. Learn the names of 2–3 colors the child explores.
- **U (Understand):** Understand that colors create Connections between very different things — a red crayon and a red flower share something even though they are not alike. Understand that each child sees colors their own way — that is Perspective, because the child picks their favorite and names things in their own style.
- **D (Do):** Practice matching colors between an object and the environment. Practice giving names to found objects. Practice collecting and photographing color matches.

**③ Design Highlight**

The naming_story synthesis turns simple color-matching into character creation. Each found object becomes a "Color Friend" with a name the child invents. The final story moment — "What do your Color Friends do together?" — transforms a collection into a narrative, letting even a 2-year-old become a storyteller. The crayon itself is the first character, connecting the child's familiar art tool to the outdoor world.

**④ Typical Scenario**

Child photographs crayons outside → AI admires the bright colors → child picks a favorite color → becomes a "Color Scout" → finds 2 things matching that color → names each as a character → tells a tiny story about the Color Friends → celebrates with a Color Scout badge.

### C. Interaction Flow

> Recommended Tier: T0 (ages 2–4)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Ooh! Crayons! So many colors! Which color do you love?"

**Child responses:**

1. (Ideal) "Red!" / "Blue!" / "Yellow!" / child picks up a crayon
2. (Unexpected) "All of them!" / "I want to draw" / "Crayons!"
3. (No response) Child holds the crayons quietly.

**AI follow-up:**

1. (thrilled) "I love red too! Red is so bright. I wonder — is red hiding out here?"
2. (warm, accepting) "All the colors! So pretty! Pick ONE. Which one is your favorite today?"
3. (wait 2s) (soft, playful) "Look at all those colors. Point to your favorite! Which one makes you smile?"

**Screen:** Crayon photo centered with each crayon gently pulsing in its own color glow; warm sparkle animation and playful color dots floating upward like bubbles.

#### Step 2: Rule Introduction + Demo

**AI says:** (excited, playful) "You are a Color Scout! Find 2 things that match your color. Take a photo! Go!"

**Child responses:**

1. (Ideal) "Okay!" / "I see one!" / child starts looking
2. (Unexpected) "What color?" / "Where?"
3. (No response) Child looks around slowly.

**AI follow-up:**

1. (cheering) "Go go, Color Scout! Find your color!"
2. (helpful, warm) "Your favorite color! Look at flowers. Look at leaves. Find that color!"
3. (wait 2s) (encouraging) "Look around! Is something that color? A flower? A leaf? Go find it!"

**Screen:** Mission card with "Color Scout" badge (crayon icon with magnifying glass), 3 slots (first filled with crayon photo, 2 empty with color-splash placeholders), and a "Find 2!" counter.

#### Step 3: Multi-Round Interaction

**Round 1 — First Color Find:**

*(Child takes a photo of something matching their chosen color — e.g., a red flower, a green leaf, a yellow dandelion)*

**AI says:** (excited discovery) "Ooh! Same color! What is it?"

**Child responses:**

1. (Ideal) "A flower!" / "Red leaf!" / "It's green!"
2. (Unexpected) "Pretty!" / "I found it!" / doesn't name it
3. (No response) Child is quiet after taking the photo.

**AI follow-up:**

1. (delighted) "A red flower! Same as your crayon! Let's give it a name. What's its name?"
2. (warm, scaffolding) "So pretty! It matches! What should we call this friend? Maybe... Sunny? Or Rosie?"
3. (wait 2s) (warm) "I see it! Same color as your crayon! It's a new friend. What name should we give it?"

**Child names the find** (or AI suggests): "Rosie! / Sunny! / Leafy!"

**AI response to naming:** (celebrating) "Hello, [name]! You're in the Color Friends club! 1 more to go!"

**Screen:** Photo slides into slot 2 with a color-burst animation; a small name tag appears below the photo; counter updates to "1 of 2 found."

**Round 2 — Second Color Find:** Child photographs another matching item (e.g., a colored bucket, a berry); AI celebrates the find, child names it, and the Color Friends collection is complete.

**STUCK BRANCH:** AI suggests looking at flowers or leaves, noting colors hide there. If still stuck, AI points toward the ground or the sky to find the child's color.

#### Step 4: Celebration

**AI says:** (proud, storytelling voice) "Look! Your Color Friends! [Name 1] and [Name 2] and your crayon. They all match! What do they do together?"

**Child responses:**

1. (Ideal) "They play!" / "They dance!" / "They are friends!" / child makes up a tiny story
2. (Unexpected) "I don't know" / "They're the same color" / "Pretty!"
3. (No response) Child looks at the photos with a smile.

**AI follow-up:**

1. (amazed, narrating) "They play together! [Name 1] and [Name 2] dance with the crayon. The best color party! What a story!"
2. (warm, scaffolding) "Same color! They match! Maybe they have a party? A color party! [Name 1] and [Name 2] and crayon all dance together!"
3. (wait 2s) (gentle, playful) "I think [Name 1] says 'Hi, [Name 2]! We match!' And they have a color party! Do you like that story?"

**Screen:** All 3 photos displayed in a circle with animated color lines connecting them; character name tags beneath each; a story-book frame with sparkle effects and "Color Friends" banner.

**AI says:** (warm, wondering) "Wow! Your crayon's color is everywhere! Why do you think that color is out here too?"

**Child responses:**

1. (Ideal) "Because flowers have color!" / "Nature is pretty!" / "Colors are everywhere!"
2. (Unexpected) "I like it!" / "Crayons are fun!" / unrelated answer
3. (No response) Child smiles at the screen.

**AI follow-up:**

1. (fascinated) "Yes! Colors are everywhere! Flowers, leaves, even rocks. Your crayon matches the whole world!"
2. (warm, connecting) "Crayons ARE fun! And look — the world has the same colors. Crayon and flower — color friends!"
3. (wait 2s) (gentle) "Colors are hiding everywhere! Your crayon and the world share the same bright colors!"

**Screen:** Collection photos with color-match lines radiating outward; the crayon photo glows as the "source" color; animated color dots float between the finds.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, proud) "Color Scout, amazing job! You found Connection — your crayon and the world share colors! And YOUR Perspective made it special — you named them YOUR way! You earned your Color Scout badge!"

**Child responses:**

1. (Engaged) "Yay!" / "I want to find more colors!" / "Color Scout!"
2. (Quiet) Child smiles or claps.

**AI follow-up:**

1. (celebration) "More colors next time! Bye, Color Scout!"
2. (gentle) "Great job today. Bye bye, Color Scout!"

**Screen:** Badge spinning into center labeled "Color Scout" with crayon and magnifying glass motif; collection photos as small insets; "Connection" and "Perspective" in bright crayon-colored lettering; rainbow confetti drifts down.
