---
activity_type: dream_whisperer_cat
entity_name: cat
category: category_1
display_label: Cat
tier: T0
ib_theme: "Who We Are"
ib_key_concept: Reflection
concepts_earned: [Reflection]
keywords: [cat, kitten, stuffed cat]
feature_keywords: [plush, stuffed, toy]
photo_features: [soft paws, fluffy fur, closed eyes, peaceful expression]
plain_description: "Imagine what a sleeping cat is dreaming about and tell a story about what the cat sees in 3 magical dream scenes."
steps_summary:
  - "Describe what the cat sees while floating on a cloud, swimming in a milk ocean, and exploring a magical garden"
  - "Talk about how imagining someone else's dreams is a way of thinking about thinking"
  - "Earn the Dream Whisperer badge!"

creative_slots:
  game_mechanic: storytelling_chain
  metaphor: "This sleepy cat is dreaming the most magical dreams!"
  role_title: Dream Whisperer
  round_scenarios:
    - floating on a cloud in the sky
    - swimming in a milk ocean
    - magical garden of favorites
  escalation_axis: familiar to fantastical
  observation_detail: "those soft little paws and fluffy fur"

step_instructions:
  hook:
    goal: "React with wonder to the sleeping cat — notice its soft paws and peaceful face, then ask the child an EMOTIONAL question about what the cat might be dreaming about (e.g. 'Do you think it's having a sweet dream right now?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an emotional question (never factual)"
    emotion_tag: excited
  transition:
    goal: "Introduce the storytelling_chain game — explain that you will set a dream scene and the child tells what the cat sees or finds. Include ONE demo round with the answer shown (e.g. 'If the cat dreamed about a garden, it might find a yarn tree!'). End with genuine invitation."
    constraint: "T0 max 3 sentences, demo round WITH answer included, end with Would you like to peek into its dreams?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Set the dream scene vividly: the cat's whiskers twitch — it's floating on a fluffy cloud high in the sky! Everything is soft and sparkly — then ask what the cat sees up there"
      scenario: "The cat's whiskers are twitching! It's floating on a big fluffy cloud way up in the sky!"
      constraint: "T0 max 2 sentences, paint the dream with magical sensory details, then ask what the cat sees"
      emotion_tag: dreamy
      acceptable_themes: [birds, stars, moon, sun, rainbow, sky, clouds, butterflies, flying]
      escalation_note: "familiar sky imagery — gentle start"
    - round_number: 2
      goal: "Set the dream scene vividly: the cat's paws are paddling — it's swimming in a magical warm milk ocean! Splish splash — then ask what the cat finds down there"
      scenario: "Now the cat's paws are paddling! It's swimming in a magical ocean made of warm milk! Splish splash!"
      constraint: "T0 max 2 sentences, use playful sound words, then ask what the cat discovers"
      emotion_tag: curious
      acceptable_themes: [fish, treasure, shells, pearl, seaweed, coral, mermaid, boat]
      escalation_note: "fantastical but safe — moderate imagination"
    - round_number: 3
      goal: "Set the dream scene vividly: the cat is purring SO loudly — it found a magical garden where everything is made of its favorite things! — then ask what grows in this dream garden"
      scenario: "Listen — the cat is purring so loudly! It found a magical garden where EVERYTHING is made of its favorite things!"
      constraint: "T0 max 2 sentences, build wonder and excitement, then ask what grows in the garden"
      emotion_tag: excited
      acceptable_themes: [treats, yarn, catnip, fish, toys, flowers, mice, food, tuna]
      escalation_note: "peak creativity — most fantastical round"
  celebrate:
    goal: "Award the child the title 'Dream Whisperer' with fanfare — recap the three magical dreams they peeked into (cloud sky, milk ocean, dream garden). Make the child feel like a dream expert."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific dreams from the game"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: the child used their imagination to think about what someone else might feel and dream — that's the magic of Reflection (thinking about thinking). Plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Reflection naturally connected to what they experienced, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: "Gentle goodbye — the cat is still dreaming happily, they can peek at more dreams anytime"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Cat photo centered with a dreamy soft-focus glow"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Sleepy Cat Friend"
    animation_label: "Dreamy glow"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat floating on a fluffy cloud in a starry sky"
    animation: scene_transition
    trigger: on_round_1
    sfx_cue: scene_woosh
    widget_label: "Dream 1: Cloud Adventure"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat swimming in a magical milk ocean"
    animation: scene_transition
    trigger: on_round_2
    sfx_cue: scene_woosh
    widget_label: "Dream 2: Milk Ocean"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat in a magical garden full of treats and toys"
    animation: gentle_pulse
    trigger: on_round_3
    sfx_cue: celebration_fanfare
    widget_label: "Dream 3: Magic Garden"
    animation_label: "Gentle glow"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Dream Whisperer"
    concepts: [Reflection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Dream Whisperer Cat

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | Dream Whisperer Cat |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T0 (ages 2–4) |
| Core IB Key Concepts | Reflection |
| Related Concepts | Imagination, Empathy, Creativity, Wellbeing |
| ATL Skills Focus | Thinking Skills (imaginative thinking, perspective-taking), Communication Skills (expressing, listening), Social Skills (empathy) |
| Game Style | storytelling_chain |

### B. Activity Overview

**① Brief Description**: The child discovers a sleeping cat and becomes a "Dream Whisperer" who peeks into its magical dreams. The AI paints vivid dream scenes — floating on a fluffy cloud in the sky, swimming through a warm milk ocean, and wandering a magical garden made of the cat's favorite things — and the child imagines what the cat sees, finds, and discovers in each dream. Each round escalates from familiar to fantastical, gently stretching the child's imagination while building the habit of thinking about what someone else might experience.

**② Educational Purpose (KUD)**:
- **K (Know)**: (1) Cats have soft, padded paws, (2) cats have fluffy fur that keeps them warm, (3) cats close their eyes and look peaceful when they sleep, (4) cats purr when they feel happy and comfortable, (5) a cat's whiskers can twitch while it sleeps
- **U (Understand)**: (1) We can use our imagination to think about what someone else might feel or experience — that is a form of Reflection; (2) wondering about another creature's dreams helps us practice thinking about thinking, one of the ways we learn about Who We Are
- **D (Do)**: (1) Imagine and describe scenes from another creature's point of view, (2) build on a story by adding creative details to a dream scene, (3) use sensory and emotional language to express imaginative ideas

**③ Design Highlight**: The storytelling_chain mechanic turns the sleeping cat into a doorway to imagination. Instead of asking the child to recall facts, the AI sets each dream scene with rich sensory detail — soft clouds, warm milk, purring vibrations — and the child fills in what the cat discovers. The child feels like they have a magical power to peek into dreams, but they are actually practicing perspective-taking and creative expression. The escalation from a familiar sky scene to a fully fantastical dream garden lets even the youngest children start with confidence and finish with wonder.

**④ Typical Scenario**: A 2–4-year-old photographs a plush or real cat curled up with its eyes closed. AI notices its soft paws and peaceful face, wonders aloud about its dreams, and invites the child to become a Dream Whisperer who peeks into three magical dream scenes.

### C. Interaction Flow

> Recommended Tier: T0 (ages 2–4)

#### Step 1: Transition Bridge

**AI says:** (soft wonder) "Ohhh, look at this sleepy cat! Look at those soft little paws and that fluffy fur... it looks so peaceful and cozy. Do you think it's having a sweet dream right now?"

**Child responses:**

1. (Ideal) "Yes!" / "It's sleeping!" / "A nice dream!"
2. (Unexpected) "It's not real." / "My cat does that!" / "Meow!"
3. (No response) Child looks at the screen quietly.

**AI follow-up:**

1. (delighted whisper) "I think so too! Its little paws are twitching — I bet it's dreaming about something magical. Would you like to peek into its dreams with me?"
2. (warm, connecting) "You know about cats! This one looks so comfy and sleepy. I wonder what it's dreaming about — would you like to find out together?"
3. (wait 2s) (gentle) "I think this cat is having the coziest dream. Its eyes are closed and it looks so happy. Would you like to peek into its dreams?"

**Screen:** Cat photo centered with a dreamy soft-focus glow, gentle sparkle highlights on the fur, and a soft lullaby ambiance.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful whisper) "Okay, here's how we peek into dreams! I'll tell you where the cat is dreaming, and YOU tell me what it finds there. Like this..."

(dreamy demo) "If the cat dreamed about a garden... it might find a big yarn tree with dangling strings everywhere! See? You just imagine what's in the dream. Would you like to peek into its dreams?"

**Child responses:**

1. (Ideal) "Yes!" / "Let's peek!" / nods eagerly
2. (Unexpected) "A yarn tree?" / "Cats like yarn!" / giggles
3. (No response) Child is listening.

**AI follow-up:**

1. (excited whisper) "Okay, Dream Whisperer — the first dream is starting! Shhhh, let's peek..."
2. (delighted) "They really do love yarn! Imagine a whole tree of it. Now let's see what THIS cat is really dreaming. First dream coming!"
3. (wait 2s) (encouraging) "It's easy — I tell you the dream, and you say what the cat finds. Any answer is a wonderful answer! Here we go..."

**Screen:** Cat photo on the left; on the right, a thought-bubble illustration of a playful yarn tree with dangling strings, a "Dream Whisperer" title in soft glowing letters, and twinkling star particles.

#### Step 3: Multi-Round Interaction

**Round 1 — "Cloud Adventure":**

**AI says:** (dreamy, hushed excitement) "The cat's whiskers are twitching! It's floating on a big fluffy cloud, way up high in the sky! Everything is soft and sparkly up there. What does the cat see from its cloud?"

**Child responses:**

1. (Ideal) "Stars!" / "A rainbow!" / "Birds!" / "The moon!"
2. (Unexpected) "The cat falls!" / "Clouds are wet." / "I see clouds too!"
3. (No response) Child is thinking.

**AI follow-up:**

1. (enchanted) "Oh wow — the cat can see [child's answer] from way up on its cloud! That must be the most beautiful dream. I bet the cat is purring so happily right now."
2. (warm, guiding) "You're thinking about clouds — I love that! Up on this fluffy dream cloud, I bet the cat can see something sparkly. Maybe stars or a big rainbow? What do you think it sees?"
3. (wait 2s) (gentle hint) "Up on the cloud, it's so high! Maybe the cat sees something twinkly — like stars, or a big bright moon. What do you think?"

**Screen:** Illustration of a cat floating peacefully on a fluffy white cloud in a soft starry sky, gentle drifting animation, with a "DREAM 1" stamp in dreamy lettering and a scene-transition woosh.

**Round 2 — "Milk Ocean":**

**AI says:** (playful, bubbly) "Now the cat's little paws are paddling! It's swimming in a magical ocean made of warm milk! Splish splash! What does the cat find in the milk ocean?"

**Child responses:**

1. (Ideal) "Fish!" / "A treasure!" / "A shell!" / "A boat!"
2. (Unexpected) "Cats don't swim!" / "I like milk!" / "Meow!"
3. (No response) Child is quiet.

**AI follow-up:**

1. (amazed) "A [child's answer] in the milk ocean — how magical! The cat is paddling over to it right now. This dream is getting more and more amazing!"
2. (playful) "This is a dream ocean, so this cat can swim and splash! And I bet there's something really cool hiding in all that warm milk. Maybe a sparkly fish or a treasure chest? What do you think?"
3. (wait 2s) (encouraging) "In this warm milky ocean, there could be anything! Maybe a little fish swimming by, or a shiny shell on the bottom. What does the cat find?"

**Screen:** Illustration of a cat happily paddling through a creamy white ocean with gentle milk-wave ripples, soft blue sky above, a "DREAM 2" stamp, and a playful splash animation.

**Round 3 — "Magic Garden":**

**AI says:** (excited, building to peak wonder) "Listen — the cat is purring SO loudly! It found a magical garden where EVERYTHING is made of its favorite things! What grows in this dream garden?"

**Child responses:**

1. (Ideal) "Fish trees!" / "Yarn!" / "Cat treats!" / "Tuna flowers!"
2. (Unexpected) "Flowers!" / "I have a garden!" / "Kitty!"
3. (No response) Child is thinking.

**AI follow-up:**

1. (overjoyed) "[Child's answer] growing in the garden — that is the most magical dream garden ever! The cat is purring louder and louder because it's SO happy!"
2. (warm, building) "A garden is such a wonderful place! But in the cat's dream, everything is made of cat favorites. Maybe flowers made of tuna, or bushes made of yarn? What silly thing do you think grows there?"
3. (wait 2s) (playful hint) "In this magical garden, the flowers might be made of fish, and the bushes might be made of yarn! What do you think the cat's dream garden grows?"

**Screen:** Illustration of a cat in a whimsical garden filled with yarn-ball bushes, fish-shaped flowers, and treat-covered trees, a warm golden glow, a "DREAM 3" stamp, and a gentle pulsing animation.

#### Step 4: Celebration

**AI says:** (proud, ceremonial whisper) "You did it! You peeked into a cloud adventure, a milk ocean swim, and a magical dream garden! You are officially a... Dream Whisperer! Only the most imaginative friends can peek into dreams like you!"

**Child responses:**

1. (Ideal) "Yay!" / "I'm a Dream Whisperer!" / giggles and cheers
2. (Unexpected) "More dreams!" / "Can the cat wake up?" / "I want to dream too!"
3. (No response) Child smiles or looks at screen.

**AI follow-up:**

1. (beaming) "The best Dream Whisperer ever! This cat is so lucky you peeked into its dreams today."
2. (warm) "Maybe next time we'll peek into even more dreams! This cat is still sleeping so happily because of you, Dream Whisperer."
3. (wait 2s) (gentle celebration) "You're a Dream Whisperer now! This sleepy cat had the best dreams because you imagined them."

**Screen:** Animated "Dream Whisperer" badge with a sleeping cat icon and crescent moon, the child's cat photo inset with a dreamy glow, golden stars floating gently, and a celebration chime; all three dream stamps visible below the badge.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what you did that was really special today? You used your imagination to think about what someone ELSE might dream about. You thought about what the cat would see, and find, and love. That's the magic of Reflection — thinking about what goes on inside someone else's mind."

(soft, planting a seed) "Next time you see a sleeping cat — or a sleeping dog, or even a sleeping teddy bear — you can be a Dream Whisperer again. Sweet dreams, friend!"

**Child responses:**

1. (Ideal) "I can dream whisper!" / "Sweet dreams, cat!" / smiles warmly
2. (Unexpected) "What's reflection?" / "My teddy sleeps!" / "Bye bye cat!"

**AI follow-up:**

1. (celebrating) "Yes you can! You'll always be a Dream Whisperer. See you next time, friend!"
2. (warm, clear) "Reflection means thinking about what someone else might feel or imagine — just like you thought about the cat's dreams! See you next time, Dream Whisperer!"

**Screen:** "Reflection" in soft, dreamy lettering with a thought-bubble motif; the sleeping cat photo glowing warmly in the center; three small dream-scene thumbnails (cloud, milk ocean, garden) arranged around it; Dream Whisperer badge in the corner with gentle star particles drifting across the screen.
