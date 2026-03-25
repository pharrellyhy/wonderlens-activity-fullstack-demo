---
activity_type: polka_dot_patrol
entity_name: ladybug
category: category_5
display_label: Ladybug
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [ladybug, ladybird, beetle]
feature_keywords: [spot, dot, polka]
photo_features: [red shell, black polka dots, tiny legs, small antennae]
plain_description: "Go outside and find 3 things that have dots, spots, or circles on them, then compare how the dots look different on each one."
steps_summary:
  - "Find 3 things nearby with dots, spots, or circles"
  - "Describe and name each spotted find"
  - "Compare the dots across all finds — big splotches vs tiny speckles vs perfect circles"
  - "Earn the Polka-Dot Patrol Officer badge!"

creative_slots:
  observation_angle: pattern
  collection_criterion: "Find things with dots, spots, or circles"
  collection_count: 3
  mission_metaphor: "You are a Polka-Dot Patrol Officer!"
  role_title: Polka-Dot Patrol Officer
  synthesis_type: comparison_chart
  stuck_hint: "Try looking at flowers up close, or at the ground near your feet"
  naming_prompt: "What kind of dots or spots do you see on this?"
  detail_question_template: "How are the dots on this one different from the ones you found before?"
  sorting_criterion: "dot size (big splotches vs tiny speckles vs perfect circles)"

collection_catalog:
  correct:
    - id: spotted_mushroom
      label: Spotted mushroom
      image: /icons/spotted_mushroom.png
    - id: dotted_pebble
      label: Dotted pebble
      image: /icons/dotted_pebble.png
    - id: speckled_leaf
      label: Speckled leaf
      image: /icons/speckled_leaf.png
    - id: circle_flower
      label: Flower with circles
      image: /icons/circle_flower.png
  distractors:
    - id: straight_stick
      label: Straight stick
      image: /icons/straight_stick.png
    - id: plain_bark
      label: Plain bark
      image: /icons/plain_bark.png
    - id: long_grass
      label: Long grass blade
      image: /icons/long_grass.png
    - id: smooth_stone
      label: Smooth stone
      image: /icons/smooth_stone.png
    - id: pine_needle
      label: Pine needles
      image: /icons/pine_needle.png
    - id: plain_leaf
      label: Plain leaf
      image: /icons/plain_leaf.png
    - id: forked_twig
      label: Forked twig
      image: /icons/forked_twig.png
    - id: acorn_cap
      label: Acorn cap
      image: /icons/acorn_cap.png

step_instructions:
  hook:
    goal: "React with wonder to the ladybug's spots — notice its red coat with black polka dots, then ask the child an IMAGINATIVE question about what the dots look like or remind them of (e.g. 'Do you think those dots are like little buttons, or maybe tiny windows?')"
    constraint: "T1 max 3 sentences, experience/preference hook, MUST end with an imaginative question about the dots"
    emotion_tag: excited
  transition:
    goal: "Build on the child's response to NATURALLY introduce the Polka-Dot Patrol Officer mission — the ladybug isn't the only spotty thing around! Frame the collection as a detective adventure: find 3 more things with dots/spots/circles nearby. Use a narrative metaphor (patrol, detective, treasure hunt). End with a genuine invitation."
    constraint: "T1 max 3 sentences, build mission from child's response (not a sudden topic switch), frame as invitation not command, end with Would you like to be the Patrol Officer?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Spark curiosity about finding the first spotted item — suggest WHERE to look (flowers up close, ground near feet) as an invitation, then ask the child to NAME or describe what they find"
      scenario: "first collection find — spots or dots"
      constraint: "T1 max 3 sentences, invitational phrasing, encourage the child to describe or name the find"
      emotion_tag: encouraging
      acceptable_themes: [flower, dots, spots, petals, pattern, circles]
      escalation_note: "easy first find — accessible items"
    - round_number: 2
      goal: "Celebrate the previous find, then spark curiosity for the next — ask child to COMPARE this find to the first one (bigger dots? tinier speckles?), suggest a new place to look"
      scenario: "second collection find — speckles or spots"
      constraint: "T1 max 3 sentences, invitational phrasing, encourage comparison between finds"
      emotion_tag: curious
      acceptable_themes: [rock, spots, speckles, stone, bark, dots, pattern]
      escalation_note: "moderate — requires more looking"
    - round_number: 3
      goal: "Guide child to find one more spotted item — the third and last one. Build excitement but remind them they still need to FIND it. Ask them to name this final treasure."
      scenario: "third collection find"
      constraint: "T1 max 3 sentences, invitational phrasing, prompt child to go find it"
      emotion_tag: excited
      acceptable_themes: [tree, bark, butterfly, dots, spots, leaf, pattern, bug]
      escalation_note: "peak energy — but child still needs to find this item"
  celebrate:
    goal: "Award the child the title 'Polka-Dot Patrol Officer' with ceremony — recap their spotted discoveries. Celebrate the PROCESS of looking closely and finding patterns everywhere."
    constraint: "T1 max 3 sentences, announce role title ceremonially, reference specific finds from the patrol"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concepts: they noticed the beautiful Form of spots/patterns everywhere, and found a surprising Connection between all these different spotted things. Plant a curiosity seed for next time."
    constraint: "T1 max 3 sentences, name Form and Connection naturally connected to what they discovered, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: "Look at all spotted treasures together — guide a comparison: how is the SAME pattern (dots/spots) DIFFERENT on each item? Big dots vs tiny speckles vs round circles. Invite child to give each find a fun name (e.g. 'freckle stone', 'polka petal')."
    constraint: "T1 max 3 sentences, comparison + creative naming, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: "Gentle goodbye — great patrol work, the polka dots will be waiting next time"
    constraint: "T1 max 3 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Ladybug photo centered with spots gently highlighted"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Spotted Friend"
    animation_label: "Sparkle highlight"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 4
    animation: card_slide_in
    trigger: on_round_1
    sfx_cue: photo_shutter_click
    widget_label: "Find 1: First Spots"
    animation_label: "Card slide in"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 4
    animation: celebration_burst
    trigger: on_round_2
    sfx_cue: photo_shutter_click
    widget_label: "Find 2: More Spots"
    animation_label: "Collection burst"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 4
    animation: celebration_burst
    trigger: on_round_3
    sfx_cue: mission_complete_fanfare
    widget_label: "Find 3: Final Spots"
    animation_label: "Collection burst"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Polka-Dot Patrol Officer"
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## The Polka-Dot Patrol

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Polka-Dot Patrol |
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Form, Connection |
| Related Concepts | Pattern, Discovery, Observation, Similarities and Differences |
| ATL Skills Focus | Research Skills (observation, data collection), Thinking Skills (analysis, comparison) |
| Game Style | comparison_chart |

### B. Activity Overview

**① Brief Description**

After the child photographs a ladybug, the AI gasps at its beautiful polka-dotted shell and wonders whether those tiny black dots are like buttons, windows, or something else entirely. The child becomes a "Polka-Dot Patrol Officer" — heading out on a detective adventure to find 3 things nearby that also have dots, spots, or circles. Each round, the child photographs a spotted find and describes its pattern. After all three are collected, the comparison_chart synthesis guides the child to examine how the same basic pattern — dots — looks completely different on each item: big splotches vs. tiny speckles vs. perfect round circles. The child gives each find a creative name (like "Freckle Stone" or "Polka Petal"), turning observation into imagination.

**② Educational Purpose (KUD)**

- **K (Know):** Learn that ladybugs have a red shell covered in black polka dots. Learn that spots and dots appear on many different things in nature. Learn that dots come in different sizes — big, tiny, and in-between. Learn the words "spots," "speckles," and "circles" as ways to describe dotted patterns.
- **U (Understand):** Understand that the Form of a pattern — its shape, size, and arrangement — can look very different even when the basic idea (dots) stays the same. Understand that finding the same pattern on different objects creates a Connection between things that might seem unrelated at first.
- **D (Do):** Practice searching the environment for a specific visual pattern. Practice comparing items by describing how their dots differ. Practice giving creative names to found objects based on their appearance.

**③ Design Highlight**

The comparison_chart synthesis transforms a scavenger hunt into genuine analysis. Instead of simply collecting spotted things, the child places all three finds side by side and examines how the "same" pattern is actually different every time — big blotchy spots on a mushroom, tiny speckles on a pebble, perfect round circles on a flower petal. This concrete, visual comparison makes abstract ideas like "same but different" tangible for a 4-year-old. The creative naming layer ("Freckle Stone," "Polka Petal") lets the child own their discoveries, turning scientific observation into personal expression.

**④ Typical Scenario**

Child photographs a ladybug → AI admires its polka dots and sparks imagination → child becomes a Polka-Dot Patrol Officer → finds and photographs 3 things with dots, spots, or circles → compares how the dots differ across all finds → gives each a creative name → celebrates with the Polka-Dot Patrol Officer badge and reflects on Form and Connection.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Wow, look at those amazing polka dots! That ladybug has a bright red coat covered in little black dots. Do you think those dots look like tiny buttons, or maybe little windows?"

**Child responses:**

1. (Ideal) "Buttons!" / "Windows!" / "They look like eyes!" / child offers an imaginative comparison
2. (Unexpected) "It's red!" / "I like ladybugs!" / "It's cute!" / child focuses on the ladybug itself
3. (No response) Child looks at the ladybug photo quietly.

**AI follow-up:**

1. (thrilled) "Tiny buttons — I love that! A coat with little dot buttons. I bet this ladybug isn't the only spotty thing around here!"
2. (warm, building) "It IS a cute little ladybug! And look at all those spots. I wonder if anything else nearby has dots like that?"
3. (wait 2s) (soft, playful) "Those polka dots are so pretty. Little black circles on a red shell. I bet there are more dots hiding around here!"

**Screen:** Ladybug photo centered with spots gently highlighted by a sparkle animation; warm wonder chime plays as dots subtly pulse.

#### Step 2: Rule Introduction + Demo

**AI says:** (excited, adventurous) "You are a Polka-Dot Patrol Officer! Your mission: find 3 things out here that have dots, spots, or circles on them. Would you like to start the patrol?"

**Child responses:**

1. (Ideal) "Yes!" / "Let's go!" / "I want to find spots!" / child is eager
2. (Unexpected) "What's a patrol?" / "Where do I look?" / "Like what?"
3. (No response) Child looks around slowly.

**AI follow-up:**

1. (cheering) "Officer on the case! Keep your eyes peeled for dots and spots. Snap a photo when you find one!"
2. (helpful, warm) "A patrol means you go looking, like a detective! Try looking at flowers up close, or at the ground near your feet. Spots love to hide!"
3. (wait 2s) (encouraging) "Try peeking at things up close. Flowers, rocks, leaves — dots could be anywhere! Would you like to start with something nearby?"

**Screen:** Mission card with "Polka-Dot Patrol Officer" badge (ladybug icon with magnifying glass), 4 slots (first filled with ladybug photo, 3 empty with dotted-circle placeholders), and a "Find 3!" counter.

#### Step 3: Multi-Round Interaction

**Round 1 — First Spotted Find:**

*(Child takes a photo of something with dots, spots, or circles — e.g., a spotted mushroom, a speckled pebble, a flower with circular markings)*

**AI says:** (excited discovery) "Ooh, you found something! Does it have dots or spots on it?"

**Child responses:**

1. (Ideal) "It has spots!" / "Look at the dots!" / "Little circles!" / child describes the pattern
2. (Unexpected) "It's pretty!" / "I found it!" / child doesn't describe the pattern
3. (No response) Child is quiet after taking the photo.

**AI follow-up:**

1. (delighted) "Spots! Just like the ladybug! Are these spots big or tiny? What do they look like to you?"
2. (warm, scaffolding) "Great find, Officer! I can see something on it. Would you like to look really close — do you see any dots or little circles?"
3. (wait 2s) (warm) "Nice work, Officer! I think I see some spots on that. Let me add it to your patrol collection!"

**Screen:** Photo slides into slot 2 with a card-slide-in animation; counter updates to "1 of 3 found"; a camera shutter click plays.

**Round 2 — Second Spotted Find:**

*(Child takes a photo of another spotted item — e.g., a dotted pebble, speckled bark, a patterned leaf)*

**AI says:** (curious) "Another one! Ooh, how are the dots on this one different from your first find?"

**Child responses:**

1. (Ideal) "These are bigger!" / "Tinier spots!" / "Different color!" / child compares
2. (Unexpected) "I like this one!" / "It's cool!" / child doesn't compare
3. (No response) Child looks at the new photo.

**AI follow-up:**

1. (impressed) "Bigger dots — great detective eyes! So the first one had tiny spots and this one has big ones. I wonder what the last one will look like?"
2. (warm, guiding) "It IS cool! Take a peek — are these dots bigger or smaller than the ones on your first find? Every spotted thing is a little different!"
3. (wait 2s) (encouraging) "Two spotted treasures! Look at them both — one kind of dots, then another. One more to go, Officer!"

**Screen:** Photo slides into slot 3 with a celebration-burst animation; counter updates to "2 of 3 found"; a camera shutter click plays.

**Round 3 — Third Spotted Find:**

*(Child photographs a final dotted item — e.g., speckled leaf, spotted bark, a butterfly wing with circles)*

**AI says:** (excited) "The last one! Your final spotted treasure. What kind of dots do you see on this?"

**Child responses:**

1. (Ideal) "Round circles!" / "Tiny speckles!" / "Big polka dots!" / child describes the pattern
2. (Unexpected) "Done!" / "I found them all!" / child focuses on completion
3. (No response) Child is quiet.

**AI follow-up:**

1. (amazed) "Round circles — beautiful! Every find has its own special kind of dots. Your patrol collection is complete!"
2. (celebrating) "You DID find them all! Three spotted treasures. What an amazing Polka-Dot Patrol Officer you are!"
3. (wait 2s) (warm, proud) "Three spotted finds! Your collection is complete, Officer. Time to look at them all together!"

**Screen:** Photo slides into slot 4 with a celebration-burst animation; counter updates to "3 of 3 found"; a mission-complete fanfare plays.

**STUCK BRANCH:**

**AI says:** (gentle, helpful) "Hmm, spots like to hide! Would you like to try looking at flowers up close, or at the ground near your feet? Sometimes rocks and petals have tiny dots you don't notice until you peek really closely."

If still stuck: "What about leaves? Turn one over — sometimes the back has little speckles! Or look at the bark on a tree. Dots are sneaky!"

#### Step 4: Celebration (Synthesis)

**AI says:** (amazed, building) "Look at all your spotted treasures together! Now here's the detective question — how are the dots DIFFERENT on each one? Are some big and some tiny?"

**Child responses:**

1. (Ideal) "This one has big dots and that one has little ones!" / "These are circles and those are speckles!" / child compares
2. (Unexpected) "They all have dots!" / "I like this one best!" / child doesn't compare directly
3. (No response) Child looks at the comparison display.

**AI follow-up:**

1. (impressed) "Yes! Big dots here, tiny speckles there, and round circles on that one. The same pattern looks SO different every time! Would you like to give each one a fun name? Like 'Freckle Stone' or 'Polka Petal'?"
2. (warm, scaffolding) "They DO all have dots! But look closely — are these dots the same size as those dots? Some are big splotches and some are teensy speckles! What should we call each one?"
3. (wait 2s) (gentle, guiding) "Look at the dots on each one. This one has big spots. That one has tiny speckles. And this one has perfect circles! Would you like to give each treasure a special name?"

**Child names the finds** (or AI suggests): "Freckle Stone! / Polka Petal! / Speckle Leaf!"

**AI response to naming:** (celebrating) "I love those names! [Name 1], [Name 2], and [Name 3] — your very own Polka-Dot collection!"

**Screen:** All 4 photos (ladybug + 3 finds) displayed side by side with comparison labels highlighting dot size (big, medium, tiny); animated dotted lines connect similar patterns; creative name tags appear beneath each photo.

**AI says:** (warm, ceremonial) "Polka-Dot Patrol Officer — you did it! You found dots, spots, and circles hiding everywhere. You are officially a Polka-Dot Patrol Officer!"

**Child responses:**

1. (Engaged) "Yay!" / "I'm a Patrol Officer!" / "I found so many!"
2. (Quiet) Child smiles at the badge.

**AI follow-up:**

1. (proud) "The best Patrol Officer! You found spots that nobody else even noticed. Those detective eyes are amazing!"
2. (warm) "Look at that badge — you earned it! Every dot you found was a clue, and you solved them all."

**Screen:** Badge spinning into center labeled "Polka-Dot Patrol Officer" with ladybug and magnifying glass motif; collection photos as small insets; "Form" and "Connection" in bright spotted lettering; confetti with polka-dot patterns drifts down.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You noticed the beautiful Form of spots and patterns — big dots, tiny speckles, perfect circles — each one shaped differently! And you found a surprising Connection between all these things. A ladybug, a stone, a flower — they all share dots! Next time you're outside, I wonder what other patterns you'll spot. Bye, Officer!"

**Child responses:**

1. (Engaged) "Bye!" / "I'll find more dots!" / "Dots are everywhere!"
2. (Quiet) Child waves or smiles.

**AI follow-up:**

1. (celebration) "Dots ARE everywhere! Keep those detective eyes open. Bye, Polka-Dot Patrol Officer!"
2. (gentle) "Great patrol today. The dots will be waiting for you next time. Bye bye, Officer!"

**Screen:** Badge centered with "Polka-Dot Patrol Officer" title; collection photos as small insets around the badge; "Form" and "Connection" in bright polka-dot-patterned lettering; spotted confetti and a gentle sparkle animation.
