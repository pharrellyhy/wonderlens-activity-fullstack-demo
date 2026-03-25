---
activity_type: apple_what_happens_next_green_apple
entity_name: green_apple
category: category_1
display_label: Green Apple
tier: T1
ib_theme: Sharing the Planet
ib_key_concept: Connection
concepts_earned: [Connection, Perspective]
keywords: [green apple, apple, fruit, food, healthy, sour, sweet, crunch]
feature_keywords: [smooth, shiny, green, stem, round]
photo_features: [smooth skin, shiny surface, green color, round shape]
plain_description: "Predict what happens to a green apple in different situations, like biting it, leaving it out for a week, and slicing it open."
steps_summary:
  - "Learn the prediction game with a quick demo round"
  - "Predict what you hear and taste when you bite the apple, what happens if you leave it on the counter for a week, and what is hiding inside when you slice it in half"
  - "Talk about how the apple connects to many parts of life and how people can feel differently about the same thing"
  - "Earn the Apple Prediction Scientist badge!"

creative_slots:
  game_mechanic: prediction_game
  metaphor: The child becomes an 'Apple Prediction Scientist' who guesses what happens to a green apple in different situations.
  role_title: Apple Prediction Scientist
  round_scenarios: [Taking a big bite out of the apple, Leaving the apple on the counter for a week, Slicing the apple in
      half to see inside]
  escalation_axis: Immediate sensory reaction to long-term changes and hidden internal structures
  observation_detail: smooth and shiny skin, like a little green ball
step_instructions:
  hook:
    goal: React with wonder to the green apple — notice its smooth, shiny skin, then ask the child a prediction question about
      what happens if you bite it.
    constraint: T1 max 3 sentences, sensory hook, MUST end with a prediction question.
    emotion_tag: curious
  transition:
    goal: Introduce the prediction_game — explain that they are now an Apple Prediction Scientist. Give a quick demo about
      an apple floating in water, then invite them to play. Would you like to try?
    constraint: T1 max 3 sentences, demo round WITH answer included, end with Would you like to try?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: 'Set the scene: taking a BIG bite out of the green apple. Ask the child what happens, what they hear, see, and taste.'
    scenario: Prediction number one! You open your mouth really wide and take a BIG bite of the apple. What happens? What
      do you hear, see, and taste?
    constraint: T1 max 3 sentences, emphasize sensory details, ask for a prediction.
    emotion_tag: excited
    acceptable_themes: [crunch, loud, white, sour, sweet, juicy, yummy]
    escalation_note: Immediate sensory reaction — easiest round
  - round_number: 2
    goal: 'Set the scene: leaving the apple on the counter for a whole week. Ask the child to predict what happens to it over
      time.'
    scenario: Prediction number two! What if we leave this apple sitting on the counter for a whole week? What do you think
      happens to it?
    constraint: T1 max 3 sentences, focus on time and physical changes, ask for a prediction.
    emotion_tag: curious
    acceptable_themes: [soft, wrinkly, brown, bad, mushy, old, rot]
    escalation_note: Long-term physical change — moderate reasoning
  - round_number: 3
    goal: 'Set the scene: someone slices the apple right in half. Ask the child to predict what is hiding in the middle.'
    scenario: Prediction number three! Someone takes a knife and slices the apple right in half. What is hiding in the middle?
    constraint: T1 max 3 sentences, focus on hidden internal structures, ask for a prediction.
    emotion_tag: surprised
    acceptable_themes: [seeds, core, white, brown, pips, star, inside]
    escalation_note: Revealing hidden structures — abstract reasoning
  celebrate:
    goal: Award the child the title 'Apple Prediction Scientist' with fanfare. Recap their successful predictions about the
      crunch, the changes, and the hidden seeds.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific moments.
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: Connection (the apple connects to the tree, store, and us) and Perspective (different people
      feel differently about sour apples). End with a warm goodbye.'
    constraint: T1 max 3 sentences, name Connection and Perspective naturally, warm goodbye.
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye that validates their scientific curiosity. Remind them they can always make predictions later.
    constraint: T1 max 3 sentences, no pressure to continue.
    emotion_tag: gentle
screen_frames:
- widget: photo_display
  widget_params:
    description: Photo of the green apple on the kitchen counter with a gentle sparkle on its shiny skin
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Shiny Green Apple
  animation_label: Sparkle highlight
- widget: character_display
  widget_params:
    description: Illustration of an apple with a cartoon bite taken out, showing pale flesh and crunch-wave sound lines
  animation: card_slide_in
  trigger: on_round_1
  sfx_cue: scene_woosh
  widget_label: 'Round 1: The Big Bite'
  animation_label: Card slide in
- widget: character_display
  widget_params:
    description: Illustration of an apple that has been left on the counter, looking a little soft and wrinkly
  animation: scene_transition
  trigger: on_round_2
  sfx_cue: scene_woosh
  widget_label: 'Round 2: The Counter Wait'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of an apple sliced in half, revealing the core and little brown seeds
  animation: gentle_pulse
  trigger: on_round_3
  sfx_cue: celebration_fanfare
  widget_label: 'Round 3: The Slice Surprise'
  animation_label: Gentle glow
celebration_frame:
  widget: badge_award
  widget_params:
    title: Apple Prediction Scientist
    concepts: [Connection, Perspective]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## Apple What-Happens-Next

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | Apple What-Happens-Next |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Connection, Perspective |
| Related Concepts | Nutrition, Wellbeing, Resources, Discovery |
| ATL Skills Focus | Thinking Skills (critical thinking, cause-and-effect), Communication Skills (expressing, listening), Research Skills (observation) |
| Game Style | prediction_game |

### B. Activity Overview

**① Brief Description**: The child becomes an "Apple Prediction Scientist" who guesses what happens to a green apple in different situations. AI presents cause-and-effect scenarios — what happens when you bite it, what happens if you leave it on the counter for a week, what happens if you drop it — and the child predicts the outcome. Each round reveals how the apple responds to the world around it, building an intuition for cause-and-effect with a familiar food item.

**② Educational Purpose (KUD)**:
- **K (Know)**: (1) Green apples have smooth, shiny skin, (2) the inside is pale and creamy white, (3) biting an apple makes a crunchy sound, (4) green apples taste a little sour and a little sweet, (5) the apple has a brownish stem like a little twig handle
- **U (Understand)**: (1) An apple connects to many parts of a child's life — nature, food, health, and daily routines (Connection); (2) different people feel differently about the same apple — some love sour, some don't — and that's okay (Perspective)
- **D (Do)**: (1) Predict outcomes based on everyday observation, (2) describe sensory experiences using specific words, (3) reason about cause and effect with a familiar object

**③ Design Highlight**: The "Apple Prediction Scientist" metaphor transforms a simple green apple into a science experiment. Instead of teaching apple facts, the AI poses "what happens when..." scenarios that let the child discover the answers through their own reasoning. The child feels like they're running experiments — but it's actually a guessing game grounded in real sensory experience. The sour-vs-sweet debate becomes a natural entry point for Perspective.

**④ Typical Scenario**: A 4–6-year-old photographs a green apple sitting on the kitchen counter. AI marvels at its shiny skin and crunchy promise, then invites the child to become a scientist who predicts what happens to the apple in different situations.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted surprise) "Ooooh, a green apple! Look how smooth and shiny it is — like a little green ball sitting right there on the counter! I wonder what would happen if we did something to it. What do you think happens if you bite it?"

**Child responses:**

1. (Ideal) "It crunches!" / "You eat it!" / "It's sour!"
2. (Unexpected) "I don't like apples." / "My mom cut it."
3. (No response) Child looks at the screen quietly.

**AI follow-up:**

1. (impressed) "CRUNCH — yes! That big crunchy sound! And maybe a little sour taste too. You know a lot about this apple! Want to make more predictions — like a scientist?"
2. (warm, accepting) "That's okay! Not everyone loves the same food — some people love sour, some love sweet. But this apple has some cool secrets. Want to guess what happens to it in different situations?"
3. (wait 2s) (playful) "I think if you bit it — CRUNCH! Big sound, little sour taste, and you'd see the white part inside. Pretty cool, right? Want to guess more?"

**Screen:** Green apple photo centered with gentle sparkle on the shiny skin and soft kitchen-counter ambiance.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful, scientist voice) "Okay — you are now an Apple Prediction Scientist! Here's how it works. I tell you something that happens to the apple, and YOU guess what the apple does. Like this..."

(dramatic demo) "What happens if I put the apple in a bowl of water? Does it sink to the bottom or float on top? Hmm... I predict it FLOATS! Because apples have lots of air inside. See? Easy! Now YOUR turn, Scientist. Ready?"

**Child responses:**

1. (Ideal) "Ready!" / "Yeah!" / "Let's do it!"
2. (Unexpected) "Apples float?" / "That's cool!" / repeats "float"
3. (No response) Child is processing.

**AI follow-up:**

1. (excited) "Great! First prediction coming right up, Scientist!"
2. (delighted) "Yes, they really do float! Apples are sneaky like that. Now let's see what YOU can predict. First one coming!"
3. (wait 2s) (encouraging) "It's easy — I say what happens, and you guess what the apple does. Any guess is a great guess! Here goes..."

**Screen:** Apple photo on the left; on the right, an "Apple Prediction Scientist" lab coat badge with a magnifying glass icon and a quick demo animation of an apple bobbing in water.

#### Step 3: Multi-Round Interaction

**Round 1 — "The Big Bite":**

**AI says:** (curious scientist narrator) "Prediction number one! You pick up the green apple. You open your mouth really wide. You take a BIG bite. Scientist — what happens? What do you hear, see, and taste?"

**Child responses:**

1. (Ideal) "CRUNCH! It's white inside! And sour!" / "It's crunchy and juicy!"
2. (Unexpected) "Yummy!" / "I want a bite!" / "It's green."
3. (No response) Child is quiet.

**AI follow-up:**

1. (amazed) "CRUNCH! Prediction confirmed! You hear that big crunchy sound because the firm insides snap when you bite. And the pale creamy part inside is so juicy! Some people think it tastes sour, and some think it's sweet. What do YOU think — sour or sweet?"
2. (warm, building) "Yummy — that's a good prediction! But let me ask you more: when you bite it, is it loud or quiet? I think it goes CRUNCH — a big sound! And the inside is a surprise — it's white, not green! Did you know that?"
3. (wait 2s) (helpful) "Here are some clues — think about the SOUND. Is it quiet like bread, or loud like a cracker? And what color do you think is INSIDE the green skin? Take your best guess!"

**Screen:** Apple with a cartoon bite taken out, crunch-wave sound lines, cross-section showing pale flesh, and a "PREDICTION 1" stamp with golden star.

**Round 2 — "The Counter Wait":** The child predicts what happens to the apple if left on the counter for a whole week. AI reveals the apple slowly softens, loses its shine, and gets wrinkly — time is the cause and the soft apple is the effect.

**Round 3 — "The Slice Surprise":** Someone slices the apple in half revealing seeds in the core and the pale white flesh. The child predicts what's hiding in the middle and what happens when the white part is left out in the air. AI celebrates the double prediction of seeds and browning.

**Rounds 4–5 (if child is engaged):** Round 4 is "The Taste Test Challenge" — predicting how someone who only eats sweet things reacts to a sour green apple, opening a natural Perspective conversation. Round 5 is "The Apple Seed Experiment" — predicting the chain from seed to tree to new apples.

#### Step 4: Celebration

**AI says:** (proud, warm) "WOW! You predicted the crunch, the changes, the hidden seeds, and even the brown trick! You are officially an... Apple Prediction Scientist! You watched, you guessed, and you figured it all out. That's some seriously smart science!"

**Child responses:**

1. (Ideal) "Yay! I'm a scientist!" / giggles or cheers
2. (Unexpected) "Can I eat the apple now?" / "More predictions!"

**AI follow-up:**

1. (beaming) "The best Apple Prediction Scientist! This apple is lucky to have someone so smart studying it."
2. (delighted) "Go for it — you earned that apple, Scientist! And every time you eat one, you'll know all its secrets now."

**Screen:** Animated "Apple Prediction Scientist" badge with a magnifying glass and apple icon, the child's apple photo inset, golden stars instead of confetti, and a celebration chime; all prediction stamps visible.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what I love about what you did today? You figured out that this little green apple is connected to SO many things — the tree it grew on, the store where your family found it, the crunch when you bite it, the seeds that could grow a whole new tree. One apple, connected to the whole world around you. That's the power of Connection!"

(building) "And here's something else you discovered — not everyone tastes this apple the same way. Some people love the sour, some want it sweeter. The same apple, but different feelings about it. That's Perspective — everyone experiences things in their own way. Scientist, you didn't just predict what happens to an apple — you discovered how it connects to everything and everyone!"

**Child responses:**

1. (Ideal) "Apples are connected to everything!" / "I like the sour part!" / smiles
2. (Unexpected) "What's perspective?" / "Can I do it with a banana?"

**AI follow-up:**

1. (celebrating) "They really are! And now you'll see those connections everywhere. See you next time, Scientist!"
2. (warm, clear) "Perspective means everyone sees things in their own way — like how you and your friend might feel differently about sour taste! And yes, you can be a prediction scientist with ANY food. See you next time!"

**Screen:** "Connection" and "Perspective" in colorful apple-themed lettering; "Connection" with dotted lines linking tree, apple, store, kitchen, and child; "Perspective" with two cartoon faces — one smiling at sour, one scrunching — both happy in their own way; scientist badge in the corner with apple photo glowing behind.
