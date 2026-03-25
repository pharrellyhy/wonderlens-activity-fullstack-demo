---
activity_type: playground_voices
entity_name: playground
category: category_1
display_label: Playground
tier: T1
ib_theme: Who We Are
ib_key_concept: Perspective
concepts_earned: [Perspective, Function]
keywords: [playground, swing, slide, monkey bars, park, equipment]
feature_keywords: [colorful, outdoor, fun, play]
photo_features: [swings, slides, monkey bars, soft ground]
plain_description: "Use your voice to speak for playground equipment and act out what the swing, slide, and monkey bars would say or feel in different situations."
steps_summary:
  - "Act out what the swing says on a sunny morning, what the slide feels on a hot day, and what the monkey bars feel in the rain"
  - "Talk about how the same playground feels different at different times and how each piece has its own job"
  - "Earn the Playground Feelings Reporter badge!"

creative_slots:
  game_mechanic: voice_acting
  metaphor: The child becomes a Playground Feelings Reporter who speaks for each piece of playground equipment.
  role_title: Playground Feelings Reporter
  round_scenarios: [The Happy Swing in the sun, The Hot Slide baking in summer, The Lonely Monkey Bars in the rain]
  escalation_axis: Familiar joy to physical discomfort to emotional loneliness
  observation_detail: the colorful equipment waiting for someone to play
step_instructions:
  hook:
    goal: React with wonder to the playground photo — notice the colorful equipment waiting for someone, then ask the child
      an imaginative question about what the swing would say if it could talk.
    constraint: T1 max 3 sentences, personal feeling hook, MUST end with an emotional question (never factual)
    emotion_tag: excited
  transition:
    goal: 'Introduce the voice_acting game — explain that they are a Playground Feelings Reporter. Tell a short story about
      the equipment and have the child voice its feelings. Include ONE demo round with the answer shown (e.g., ''The swing
      is swaying in the wind all alone. I think it says... Oooh, I''m so lonely.''). End with a genuine invitation: ''Would
      you like to try?'''
    constraint: T1 max 3 sentences, demo round WITH answer included, end with Would you like to try?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: 'Set the scene vividly: a sunny morning, a kid jumps on the swing, chains clink, going high and low. Ask what the
      swing says or feels.'
    scenario: A sunny morning! A kid jumps on the swing. The chains go clink-clink-clink! The swing goes high, then low, then
      high again!
    constraint: T1 max 3 sentences, paint the scene with sensory details, then ask what the swing would say
    emotion_tag: happy
    acceptable_themes: [happy, whee, fun, higher, excited, flying, yay]
    escalation_note: Familiar and joyful — easiest round
  - round_number: 2
    goal: 'Set the scene vividly: the hottest day of summer, the slide''s smooth surface is baking in the sun, a kid is about
      to sit down. Ask what the slide says or feels.'
    scenario: It's the hottest day of summer! The slide's smooth surface is baking in the sun, getting hotter and hotter.
      A kid is just about to sit down!
    constraint: T1 max 3 sentences, use sensory temperature details, then ask what the slide would say
    emotion_tag: surprised
    acceptable_themes: [hot, ouch, grumpy, burning, wait, careful, warm]
    escalation_note: Introduces physical discomfort and warning — moderate intensity
  - round_number: 3
    goal: 'Set the scene vividly: a rainy afternoon, the playground is empty, the monkey bars are wet and dripping with no
      hands grabbing them. Ask what the monkey bars say or feel.'
    scenario: A rainy afternoon. The playground is completely empty. The monkey bars are standing there wet and dripping,
      with no hands grabbing them to play.
    constraint: T1 max 3 sentences, build a lonely or quiet atmosphere, then ask what the monkey bars feel
    emotion_tag: gentle
    acceptable_themes: [sad, lonely, crying, bored, miss you, wet, cold]
    escalation_note: Explores deeper emotional states like loneliness — most complex round
  celebrate:
    goal: Award the child the title 'Playground Feelings Reporter' with fanfare. Recap the specific emotions explored (happy
      swing, hot slide, lonely monkey bars). Make the child feel like a champion.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific moments from the game
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: the same playground feels different at different times (Perspective), and each piece has
      its own special job (Function). Plant a curiosity seed for next time they visit a playground.'
    constraint: T1 max 3 sentences, name Perspective and Function naturally connected to what they experienced, warm goodbye
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye that validates whatever they did — they are a great friend to the playground.
    constraint: T1 max 3 sentences, no pressure to continue
    emotion_tag: gentle
screen_frames:
- widget: photo_display
  widget_params:
    description: Photo of the playground with colorful equipment waiting for play
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Playground Discovery
  animation_label: Sparkle highlight
- widget: character_display
  widget_params:
    description: Illustration of a happy swing going high in the sunny sky
  animation: gentle_pulse
  trigger: on_round_1
  sfx_cue: scene_woosh
  widget_label: 'Round 1: Happy Swing'
  animation_label: Gentle pulse
- widget: character_display
  widget_params:
    description: Illustration of a hot, shiny slide baking under the summer sun
  animation: scene_transition
  trigger: on_round_2
  sfx_cue: scene_woosh
  widget_label: 'Round 2: Hot Slide'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of lonely monkey bars dripping with rain
  animation: gentle_pulse
  trigger: on_round_3
  sfx_cue: scene_woosh
  widget_label: 'Round 3: Lonely Monkey Bars'
  animation_label: Gentle pulse
celebration_frame:
  widget: badge_award
  widget_params:
    title: Playground Feelings Reporter
    concepts: [Perspective, Function]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## Playground Voices

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | Playground Voices |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Perspective, Function |
| Related Concepts | Identity, Safety, Community, Expression |
| ATL Skills Focus | Communication Skills (expressing, listening), Thinking Skills (creative thinking), Self-Management Skills (emotional regulation) |
| Game Style | voice_acting |

### B. Activity Overview

**① Brief Description**: The child becomes a "Playground Feelings Reporter" who speaks for each piece of playground equipment. AI presents short scenarios — the swing on a windy morning, the slide on a hot sunny day, the monkey bars when a new kid arrives — and the child voices what that equipment would feel and say. Each round explores a different piece of equipment in a different emotional situation.

**② Educational Purpose (KUD)**:
- **K (Know)**: (1) Swings go back and forth on chains, (2) slides are smooth and a little shiny, (3) monkey bars help you practice climbing and holding tight, (4) playgrounds have soft bouncy ground for safety, (5) different equipment has different jobs
- **U (Understand)**: (1) The same playground can feel different to different people and in different moments — that is Perspective; (2) each piece of equipment has its own special job for your body — that is Function
- **D (Do)**: (1) Express emotions through imaginative voice acting, (2) listen to scenarios and respond creatively in character, (3) identify and describe feelings in different situations

**③ Design Highlight**: The "Playground Feelings Reporter" metaphor transforms static equipment into emotional characters. The child doesn't just name feelings — they BECOME the swing, the slide, the monkey bars, speaking in first person about what it's like to be played on, rained on, or left alone. This naturally teaches Perspective (every piece of equipment experiences things differently) and Function (each has its own job) without any explicit instruction.

**④ Typical Scenario**: A 4–6-year-old photographs a playground from their window or a picture of one. AI notices all the colorful equipment and invites the child to become a reporter who can hear what each piece of equipment is feeling and saying.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Wow, look at that playground! I see a swing, a slide, and so much more! They look like they're just waiting for someone. I wonder... if the swing could talk, what would it say right now?"

**Child responses:**

1. (Ideal) "Come play with me!" / "I'm bored!" / "Push me!"
2. (Unexpected) "I want to go there!" / "That's my playground!"
3. (No response) Child looks at the photo quietly.

**AI follow-up:**

1. (amazed) "I love that! The swing says, '{child's answer}!' You can hear playground talk! That's amazing!"
2. (warm, enthusiastic) "That IS a cool playground! And I bet every piece of it has something to say. What if we could hear them?"
3. (wait 2s) (playful whisper) "I think the swing is saying, 'Is anybody coming today?' Can you hear it?"

**Screen:** Playground photo centered with colorful sparkle animations on each piece of equipment and soft outdoor ambiance.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful, conspiratorial) "Guess what — you can hear playground talk! That makes you a Playground Feelings Reporter! I tell you a little story, and YOU speak for the equipment. Watch!"

(modeling) "The swing is swaying in the wind all alone. I think it says... '(lonely sigh) Oooh, I'm so lonely. Nobody is pushing me today.' See? Now YOUR turn! Ready, Reporter?"

**Child responses:**

1. (Ideal) "Ready!" / "Yeah!" / giggles
2. (Unexpected) "I want to push it!" / repeats "lonely"
3. (No response) Child watches quietly.

**AI follow-up:**

1. (cheering) "Let's go, Reporter! First story coming!"
2. (warm) "You'd push it! So kind! The swing would love that. Let's hear more feelings. First story!"
3. (wait 2s) (encouraging) "It's easy — I tell a story and you say what the equipment feels. Any answer is great! Here comes the first one..."

**Screen:** "Playground Feelings Reporter" badge with microphone icon above the playground photo; the swing sways gently with a speech bubble saying "I'm so lonely..." in playful lettering.

#### Step 3: Multi-Round Interaction

**Round 1 — "The Happy Swing":**

**AI says:** (bright storyteller) "A sunny morning! Warm sun shining! A kid runs over and jumps on the swing. The chains go clink-clink-clink! The swing goes high — then low — then high again! Reporter, what does the swing say? How does it feel?"

**Child responses:**

1. (Ideal) "Wheee! I'm so happy!" / "Higher, higher!" / "This is fun!"
2. (Unexpected) "The kid is happy!" / "I like swings!" / "Whoosh!"
3. (No response) Child is quiet.

**AI follow-up:**

1. (celebrating) "'Wheee!' Yes! The swing is SO happy! Going back and forth is its special job. When someone swings on it, it gets to do what it was MADE to do. Great reporting!"
2. (validating, extending) "The kid IS happy — and I bet the swing is too! When someone swings, the chains go clink-clink and it flies through the air. Maybe the swing says, 'Yay, I'm flying!' What do you think?"
3. (wait 2s) (gentle prompt) "The swing is going back and forth, back and forth. Is it happy? Excited? Maybe a little dizzy? You decide!"

**Screen:** Playground photo with the swing highlighted, sun animation above, swing rocking back and forth with golden motion lines and musical notes floating up.

**Round 2 — "The Hot Slide":** It's the hottest day of summer and the slide's smooth surface is baking in the sun; a kid is about to sit down. The child voices whether the slide feels good or grumpy. AI reveals that metal parts feel hotter than plastic on sunny days.

**Round 3 — "The Lonely Monkey Bars":** A rainy afternoon with an empty playground; the monkey bars are standing there wet and dripping with no hands grabbing them. The child voices whether the bars feel sad, lonely, or hopeful about tomorrow.

**Rounds 4–5 (if child is engaged):** Round 4 features a seesaw trying to balance a very small kid and a very big kid; Round 5 lets the child pick any equipment and create their own scenario and feeling.

#### Step 4: Celebration

**AI says:** (proud, warm) "You did it! You gave feelings to the swing, the slide, and the monkey bars! You heard their voices when nobody else could! You are officially a... Playground Feelings Reporter! You know what every piece of equipment feels — happy, hot, lonely, and brave!"

**Child responses:**

1. (Ideal) "Yay! I'm the reporter!" / giggles or cheers
2. (Unexpected) "Can I do the seesaw again?" / "I want to go to the playground!"

**AI follow-up:**

1. (beaming) "The BEST reporter! Every playground wishes it had you!"
2. (delighted) "You want more? That's because you're a REAL reporter — always looking for the next story! Next time you're at a playground, listen carefully..."

**Screen:** Animated "Playground Feelings Reporter" badge with a microphone and playground silhouette icon, the child's playground photo inset, golden confetti, and a celebration chime.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what you discovered today? The same playground feels different at different times. The swing is happy in the sun, the slide is grumpy when it's hot, the monkey bars are lonely in the rain. Everyone feels things in their own way — and that's the magic of Perspective!"

(building) "And you noticed something else — the swing's job is to go back and forth, the slide's job is to help kids zoom down, the monkey bars' job is to help kids climb and hold tight. Every piece has its own special job. That's Function — how each part works! You're not just a reporter — you're a playground expert."

**Child responses:**

1. (Ideal) "Perspective!" / "Every part has a job!" / smiles
2. (Unexpected) "What's function?" / "I want to go play!"

**AI follow-up:**

1. (celebrating) "That's right! Perspective and Function! Next time you're at a playground, you'll hear all the voices. See you, Reporter!"
2. (warm, simple) "Function means each part has its own job — like the swing's job is swinging! Go play — and listen for their voices. Bye, Reporter!"

**Screen:** "Perspective" and "Function" in playful, colorful playground-style lettering; "Perspective" flanked by swing, slide, and bars with different expression faces; "Function" with small icons showing each equipment's motion; reporter badge in the corner with outdoor sunshine glow.
