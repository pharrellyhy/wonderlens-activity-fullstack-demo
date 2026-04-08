---
activity_type: shimmer_spotter_safari_goldfish
entity_name: goldfish
category: category_5
display_label: Goldfish
tier: T1
ib_theme: How We Express Ourselves
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [goldfish, fish, pond, aquarium, water]
feature_keywords: [shimmer, shiny, scales, fins, sparkle]
photo_features: [orange scales, fan-shaped tail, floaty fins, shiny surface]
plain_description: "Go outside and find 3 water creatures or shimmery things nearby, then compare each one to the goldfish and sort them by how they shimmer."
steps_summary:
  - "Find 3 water creatures or shimmery things nearby"
  - "Describe each find — does it have fins, scales, or a shiny surface like the goldfish?"
  - "Sort the collection into 'shimmers like the goldfish' and 'different from the goldfish'"
  - "Earn the Shimmer Spotter badge!"
creative_slots:
  observation_angle: form
  collection_criterion: Water creatures or shimmery things nearby
  collection_count: 3
  mission_metaphor: You are a Shimmer Spotter on a safari!
  role_title: Shimmer Spotter
  synthesis_type: comparison_chart
  stuck_hint: Would you like to check the water surface for sparkles, or peek at wet leaves and puddles nearby?
  naming_prompt: Does this have fins, scales, or a shiny surface like the goldfish?
  detail_question_template: "How does the shimmer on this one look different from the others you found?"
  sorting_criterion: "shininess (most sparkly to least sparkly)"
collection_catalog:
  correct:
  - id: shiny_wet_rock
    label: Shiny wet rock
    image: /icons/shiny_wet_rock.png
  - id: swimming_duck
    label: Swimming duck
    image: /icons/swimming_duck.png
  - id: green_frog
    label: Green frog
    image: /icons/green_frog.png
  - id: sparkly_dragonfly
    label: Sparkly dragonfly
    image: /icons/sparkly_dragonfly.png
  distractors:
  - id: dry_twig
    label: Dry twig
    image: /icons/dry_twig.png
  - id: plain_dirt
    label: Plain dirt
    image: /icons/plain_dirt.png
  - id: matte_leaf
    label: Matte leaf
    image: /icons/matte_leaf.png
  - id: pinecone
    label: Pinecone
    image: /icons/pinecone.png
  - id: rough_bark
    label: Rough bark
    image: /icons/rough_bark.png
  - id: dull_pebble
    label: Dull pebble
    image: /icons/dull_pebble.png
  - id: dry_grass
    label: Dry grass
    image: /icons/dry_grass.png
  - id: acorn_cap
    label: Acorn cap
    image: /icons/acorn_cap.png
step_instructions:
  hook:
    goal: React with wonder to the goldfish's shiny scales and floaty fins, then ask the child an imaginative question about
      what they like best about it.
    constraint: T1 max 3 sentences, experience/preference hook, MUST end with an imaginative question.
    emotion_tag: excited
  transition:
    goal: 'Build on the child''s response to introduce the Shimmer Spotter mission. Frame the collection as a safari to find
      3 more water creatures or shimmery things. End with an invitation: Would you like to be a Shimmer Spotter?'
    constraint: T1 max 3 sentences, invitational phrasing, end with Would you like to be a Shimmer Spotter?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: Spark curiosity about finding the first shimmery or watery item. Suggest looking near the water's edge as an invitation,
      then ask the child to describe if it has scales or is smooth.
    scenario: first collection find — shiny wet rock or similar
    constraint: T1 max 3 sentences, invitational phrasing, encourage description
    emotion_tag: encouraging
    acceptable_themes: [rock, shiny, wet, smooth, water, shimmer, sparkle]
    escalation_note: easy first find — accessible items near water
  - round_number: 2
    goal: Celebrate the previous find, then prompt for a water creature. Ask the child to compare this find to the goldfish
      (does it have fins or feathers/legs?).
    scenario: second collection find — water creature like a duck or frog
    constraint: T1 max 3 sentences, invitational phrasing, encourage comparison
    emotion_tag: curious
    acceptable_themes: [duck, frog, bug, feathers, legs, wings, swim, water]
    escalation_note: moderate — requires spotting a living creature or distinct object
  - round_number: 3
    goal: Guide the child to find one last sparkly surprise. Build excitement for the final treasure and ask them what makes
      it sparkly.
    scenario: third collection find — sparkly surprise like a dragonfly or reflection
    constraint: T1 max 3 sentences, invitational phrasing, prompt child to go find it
    emotion_tag: excited
    acceptable_themes: [dragonfly, reflection, leaf, sparkle, shiny, light, water]
    escalation_note: peak energy — final item to complete the collection
  celebrate:
    goal: Award the child the title 'Shimmer Spotter' with ceremony. Recap their discoveries of shiny things and water creatures.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific finds
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: they noticed the Form of different treasures (scales, shapes, shimmer) and found a Connection
      between things near the water. Plant a curiosity seed for next time.'
    constraint: T1 max 3 sentences, name Form and Connection naturally, warm goodbye
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye — great spotting work, the shimmery treasures will be waiting next time.
    constraint: T1 max 3 sentences, no pressure to continue
    emotion_tag: gentle
  synthesis:
    goal: Look at all the finds together and guide a comparison chart activity. Ask the child to sort which ones shimmer like
      the goldfish and which ones are different.
    constraint: T1 max 3 sentences, comparison and sorting, frame as invitation
    emotion_tag: amazed
screen_frames:
- widget: photo_display
  widget_params:
    description: Goldfish photo centered with a soft aqua-blue glow and tiny sparkle animations highlighting its shiny scales
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Shimmery Goldfish
  animation_label: Sparkle highlight
- widget: progress_tracker
  widget_params:
    filled: 1
    total: 4
  animation: card_slide_in
  trigger: on_round_1
  sfx_cue: photo_shutter_click
  widget_label: 'Find 1: First Shimmer'
  animation_label: Card slide in
- widget: progress_tracker
  widget_params:
    filled: 2
    total: 4
  animation: celebration_burst
  trigger: on_round_2
  sfx_cue: photo_shutter_click
  widget_label: 'Find 2: Water Creature'
  animation_label: Collection burst
- widget: progress_tracker
  widget_params:
    filled: 3
    total: 4
  animation: celebration_burst
  trigger: on_round_3
  sfx_cue: mission_complete_fanfare
  widget_label: 'Find 3: Sparkly Surprise'
  animation_label: Collection burst
celebration_frame:
  widget: badge_award
  widget_params:
    title: Shimmer Spotter
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## The Shimmer Spotter Safari

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Shimmer Spotter Safari |
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Form, Connection |
| Related Concepts | Habitat, Adaptation, Discovery, Pattern |
| ATL Skills Focus | Research Skills (observation, data collection), Thinking Skills (critical thinking, transfer), Communication Skills (expressing) |
| Game Style | comparison_chart |

### B. Activity Overview

**① Brief Description**

The child spots a goldfish in a pond or aquarium tank and becomes a "Shimmer Spotter" on a mission to find other water creatures and shimmery things nearby. They photograph 3 finds, compare each one to the goldfish — does it have fins, scales, or a shiny surface? — and sort their collection into a simple chart of "like the goldfish" and "different from the goldfish."

**② Educational Purpose (KUD)**

- **K (Know):** Goldfish have floaty fins, fan-shaped tails, and tiny overlapping scales; other water creatures move and look different from goldfish; shiny or shimmery surfaces appear on many things in nature and around ponds; scales protect a fish like a jacket protects you
- **U (Understand):** Living things that share a habitat can look very different from each other — their Form tells us how they survive; objects that seem unrelated can share surprising features like shimmer, shape, or movement (Connection)
- **D (Do):** Observe and describe visible features of water creatures and shimmery objects; compare and sort finds by shared and different properties; explain why a find is similar to or different from the goldfish

**③ Design Highlight**

The collection criterion is "water creatures and shimmery things" — a two-pronged hunt that lets the child find both living things (frogs, ducks, bugs on water) and non-living shimmery objects (wet rocks, reflections, water surface itself). The comparison chart asks the child to sort each find: "Does it have fins? Scales? Shimmer?" — turning physical observation into a simple classification exercise grounded in the goldfish's real body features.

**④ Typical Scenario**

A child at a park pond or aquarium photographs a goldfish, then hunts for 3 more water creatures or shimmery things nearby, comparing each find's features to the goldfish's fins, scales, and shimmer.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted wonder) "Wow, a goldfish! Look at those shiny scales. It sparkles like a tiny treasure in the water. What do you like best about it?"

**Child responses:**

1. (Ideal) "It's so shiny!" / "I like its tail!"
2. (Unexpected) "It's orange!" / "Can I touch it?"
3. (No response) Child watches the goldfish swim.

**AI follow-up:**

1. (impressed) "So shiny, like little mirrors on its body! This goldfish is a real shimmer star. I wonder what else around here shimmers like that."
2. (warm, playful) "It IS orange — bright orange with sparkly scales! It looks like a little jewel swimming around. I bet more shimmery things are hiding near this water."
3. (wait 2s) (playful, coaxing) "Look at it glide! Those fins wave like tiny flags. This goldfish is full of shimmer. Want to find more shimmery things nearby?"

**Screen:** Goldfish photo centered with a soft aqua-blue glow and tiny sparkle animations highlighting its shiny scales.


#### Step 2: Rule Introduction + Demo

**AI says:** (adventurous, rallying) "You are now a Shimmer Spotter! Your mission has three parts. First, find three water creatures or shimmery things nearby. Second, take a photo of each one. Third, we will sort them — like the goldfish or different. Ready, spotter?"

**Child responses:**

1. (Ideal) "Ready!" / "Let's go!"
2. (Unexpected) "What is a shimmery thing?"
3. (No response) Child looks around uncertainly.

**AI follow-up:**

1. (pumped up) "Let's go! I bet something shimmery is hiding near the water — would you like to start looking?"
2. (warm, explaining) "Shimmery means shiny and sparkly — like the goldfish's scales! I wonder if there are wet rocks, water sparkles, or shiny bugs nearby. Would you like to check?"
3. (wait 2s) (encouraging) "I bet something sparkly is waiting near the water's edge! Would you like to peek over there?"

**Screen:** Mission card with "Shimmer Spotter" badge (magnifying glass with sparkles), four collection slots (first filled with goldfish photo), and a numbered checklist.


#### Step 3: Multi-Round Interaction

**Round 1:**

*(Child takes a photo of a shiny wet rock near the water)*

**AI says:** (excited discovery) "Ooh, a shiny rock! It gleams near the water. Does this rock have scales like the goldfish, or is it smooth?"

**Child responses:**

1. (Ideal) "It's smooth!" / "No scales, just shiny."
2. (Unexpected) "It's just a rock." / "I don't know."
3. (No response) Child waits silently.

**AI follow-up:**

1. (delighted) "Smooth and shiny — no scales, but it shimmers just like the goldfish! Great eye, spotter. Two more finds to go!"
2. (warm, extending) "A rock is a great find! It is shiny like the goldfish but has no fins or tail. Same shimmer, different shape! Two more to go!"
3. (playful) "I see something shiny and wet! This rock gleams like the goldfish's scales, but it cannot swim. Nice spotting! Two more to find!"

**Screen:** Rock photo slides into second collection slot with sparkle animation; counter shows "1 of 3 found."

**Round 2 — "Water Creature":** Child photographs a duck, bug, or frog near the water; AI asks if it has fins or scales like the goldfish. Child notices feathers/legs/wings instead. AI highlights: same water, different body.

**Round 3 — "Sparkly Surprise":** Child photographs a dragonfly, water reflection, or shiny leaf; AI asks what makes it sparkly. Includes stuck branch — AI suggests looking at the water surface for sparkles, wet leaves on the ground, or puddles nearby.


#### Step 4: Celebration

**AI says:** (proud, curious) "Look at all your finds together! The goldfish, and three new treasures. Now let's sort them. Which ones shimmer like the goldfish? And which ones are really different? Tell me!"

**Child responses:**

1. (Ideal) Child groups finds: "The rock shimmers like the fish, but the duck is different because it has feathers."
2. (Unexpected) Child picks one without sorting: "I like the rock best." / Child is unsure how to sort.
3. (No response) Child stares at the collection display.

**AI follow-up:**

1. (impressed, extending) "The rock shimmers but has no fins. The duck swims but has feathers, not scales. Great sorting, spotter! You found what is the same and what is different."
2. (scaffolding warmly) "Good pick! Now think — does the rock have fins like the goldfish? No! But does it shimmer? Yes! That is one way to sort them. What about your other finds?"
3. (wait 2s) (gently guiding) "Which one do you think is shiny like the goldfish? And which one looks really different? You decide!"

**AI says:** (warm celebration) "Wow, Shimmer Spotter! You found four things near the water. Some shimmer, some swim, some have scales and some do not. Which one is your favorite find? And why?"

**Child responses:**

1. (Ideal) "The rock because it's super shiny!" / "The duck because it quacks!"
2. (Unexpected) "The goldfish is still my favorite."

**AI follow-up:**

1. (awed) "Great choice! Every find has its own special look. That is what makes exploring so fun — everything near the water is different!"
2. (warm, affirming) "The goldfish started it all! It showed you what shimmer looks like. And then you found so many other treasures. That is amazing!"

**Screen:** All four photos in a grid with sorting zones ("Shimmers like goldfish" / "Different from goldfish"), golden star on favorite, animated water ripple effects, and banner "4 treasures found near the water!"


#### Step 5: Closing + IB Concepts

**AI says:** (proud, warm celebration) "You are an amazing Shimmer Spotter! You found shiny things and water creatures and compared every one to the goldfish. You discovered Form — every treasure has its own shape, scales, or shimmer. And you found Connection — things near the water share surprises, like shimmer and movement, even when they look totally different. You earned your Shimmer Spotter badge!"

**Screen:** "Shimmer Spotter" badge — golden magnifying glass with goldfish silhouette inside and three treasure icons orbiting it. "Form" and "Connection" in artistic aqua-blue and gold lettering with wave and chain-link icons. Four collection photos as insets around the badge.
