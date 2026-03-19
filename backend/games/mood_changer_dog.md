---
activity_type: mood_changer_dog
entity_name: dog
category: category_1
display_label: Stuffed Dog
tier: T0
ib_theme: "Who We Are"
ib_key_concept: Perspective
concepts_earned: [Perspective]
keywords: [dog, puppy, stuffed dog, toy dog]
feature_keywords: [plush, stuffed, toy]
photo_features: [floppy ears, soft fur, cute face, fluffy body]

creative_slots:
  game_mechanic: voice_acting
  metaphor: "This fluffy dog friend has so many feelings inside!"
  role_title: Emotion Translator
  round_scenarios:
    - warm sunshine on belly
    - tripped and went bump
    - favorite treat arrives
  escalation_axis: comfortable to excited
  observation_detail: "those cute floppy ears and super soft fur"

step_instructions:
  hook:
    goal: "React with wonder to the stuffed dog — notice its soft fur and floppy ears, then ask the child an EMOTIONAL question about the dog's current mood or feelings (e.g. 'How does it look today — happy, sleepy, or a little bored?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an emotional question (never factual)"
    emotion_tag: excited
  transition:
    goal: "Introduce the voice_acting game — explain that you will describe something happening to the dog and the child says what the dog would say or feel. Include ONE demo round with the answer shown (e.g. 'If the dog's favorite ball went missing, it might sigh and say Oh no, where is my ball?'). End with a genuine invitation."
    constraint: "T0 max 3 sentences, demo round WITH answer included, end with Would you like to try?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Set the scene vividly: morning time, warm sunshine pouring onto the dog's belly, the dog stretches and yawns — then ask what the dog says or feels"
      scenario: "Morning! The warm sunshine lands on the doggy's belly. It stretches out with a big yawn!"
      constraint: "T0 max 2 sentences, paint the scene with sensory details, then ask what the dog would say"
      emotion_tag: warm
      acceptable_themes: [happy, cozy, warm, comfy, nice, sleepy, relaxed]
      escalation_note: "comfortable, familiar — easiest round"
    - round_number: 2
      goal: "Set the scene vividly: the dog trips and goes bump — a surprising little tumble — then ask what the dog says or does"
      scenario: "Oops! The doggy trips and goes bump on its bottom! What a surprise!"
      constraint: "T0 max 2 sentences, use onomatopoeia (bump, oops, whoa), then ask what the dog would say"
      emotion_tag: surprised
      acceptable_themes: [surprised, startled, oh no, ouch, shocked, scared, whoa]
      escalation_note: "unexpected contrast — moderate intensity"
    - round_number: 3
      goal: "Set the scene vividly: the owner brings the dog's absolute favorite treat — the dog can smell it — then ask how the dog reacts"
      scenario: "Sniff sniff! The owner brings the doggy's favorite treat! It smells SO good!"
      constraint: "T0 max 2 sentences, build excitement with sensory details (smell, wagging), then ask what the dog does"
      emotion_tag: excited
      acceptable_themes: [excited, happy, yay, wag, treats, hungry, eager, jump]
      escalation_note: "peak excitement — most energetic round"
  celebrate:
    goal: "Award the child the title 'Emotion Translator' with fanfare — recap the specific emotions explored (happy in sunshine, surprised by the bump, excited for treats). Make the child feel like a champion."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific moments from the game"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: the same dog feels different things when different things happen — that's the magic of Perspective (everyone sees the world a little differently). Then plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Perspective naturally connected to what they experienced, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: "Gentle goodbye that validates whatever they did — they are a great friend to the dog"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Photo of the stuffed dog on the bed with a soft golden glow"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Your Fluffy Friend"
    animation_label: "Sparkle highlight"
  - widget: character_display
    widget_params:
      description: "Illustration of a cozy dog napping in a sunbeam"
    animation: gentle_pulse
    trigger: on_round_1
    sfx_cue: scene_woosh
    widget_label: "Round 1: Warm Sunshine"
    animation_label: "Gentle glow"
  - widget: character_display
    widget_params:
      description: "Illustration of a dog looking surprised after a little bump"
    animation: scene_transition
    trigger: on_round_2
    sfx_cue: scene_woosh
    widget_label: "Round 2: Oops, a Bump!"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a dog wagging its tail excitedly for a treat"
    animation: gentle_pulse
    trigger: on_round_3
    sfx_cue: celebration_fanfare
    widget_label: "Round 3: Treat Time!"
    animation_label: "Gentle glow"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Emotion Translator"
    concepts: [Perspective]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Mood Changer Dog

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | Mood Changer Dog |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T0 (ages 2–4) |
| Core IB Key Concepts | Perspective |
| Related Concepts | Feelings, Identity, Empathy, Discovery |
| ATL Skills Focus | Communication Skills (expressing, listening), Thinking Skills (creative thinking), Self-Management Skills (emotional awareness) |
| Game Style | voice_acting |

### B. Activity Overview

**① Brief Description**: After the child photographs their stuffed dog, the AI gasps at its cute floppy ears and super soft fur. The child becomes an "Emotion Translator" — someone who knows exactly what the dog is feeling inside. The AI paints vivid little scenes — warm sunshine on the belly, a surprise tumble, a favorite treat arriving — and the child tells the AI what the dog would say or feel. Each scenario helps the child step into someone else's shoes and explore how different things make us feel different ways.

**② Educational Purpose (KUD)**:
- **K (Know)**: A stuffed dog has soft floppy ears that hang down; its fur feels warm and cuddly when you squeeze it; dogs stretch and yawn when they feel cozy; a surprised face looks wide-eyed with a big open mouth; tails wag fast when dogs feel excited and happy
- **U (Understand)**: The same dog can feel happy, surprised, or excited — it depends on what is happening around it. When we imagine how someone else feels, we are using Perspective — seeing the world through another's eyes.
- **D (Do)**: Practice naming and expressing different emotions, imagine how someone else might feel in a situation, use voice and words to act out feelings

**③ Design Highlight**: The "Emotion Translator" metaphor turns a quiet stuffed dog into a character bursting with hidden feelings. The child does not answer questions ABOUT the dog — they speak FOR the dog, giving it a voice and emotions. Each scenario shifts the emotional tone (cozy to surprised to excited), so the child naturally practices recognizing and expressing a range of feelings. The escalation from comfortable warmth to peak excitement keeps toddlers engaged while building emotional vocabulary.

**④ Typical Scenario**: Child photographs their stuffed dog on the bed, AI notices its floppy ears and soft fur, and the child becomes an Emotion Translator who voices what the dog feels during cozy, surprising, and exciting moments.

### C. Interaction Flow

> Recommended Tier: T0 (ages 2–4)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Ohhh WOW, look at this fluffy friend! Those cute floppy ears and that super soft fur! I think this doggy has SO many feelings inside. How does the doggy look right now — happy, sleepy, or a little bored?"

**Child responses:**

1. (Ideal) "Happy!" / "Sleepy!" / "He looks happy!"
2. (Unexpected) "That's my dog!" / "Doggy!" / "It's soft!"
3. (No response) Child watches the screen silently.

**AI follow-up:**

1. (warm, impressed) "Ooh, you can tell! You looked right at the doggy and knew. I bet you know ALL the doggy's feelings!"
2. (enthusiastic) "It IS your doggy! And you know it so well. I bet this fluffy friend has lots of feelings you can tell me about!"
3. (wait 2s) (soft, wondering) "This doggy looks so cuddly. I think it has secret feelings inside. Would you like to help me find out?"

**Screen:** Stuffed dog photo centered with gentle golden sparkle radiating from the fur and tiny heart animations pulsing softly around the floppy ears.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful, warm) "Okay, here is a fun game! I tell you something that happens to the doggy. And YOU tell me what the doggy says or feels! Watch — I will show you!"

(demo) "If I say... 'the doggy's favorite ball went missing' — hmm, what would the doggy say? I think the doggy would go... (sad sigh) 'Oh noooo, where is my ball?' See? Now YOUR turn! Would you like to try?"

**Child responses:**

1. (Ideal) "Yeah!" / "Yes!" / nods eagerly.
2. (Unexpected) "My doggy has a ball!" / giggles / "Oh no!"
3. (No response) Child is quiet, possibly processing.

**AI follow-up:**

1. (excited) "Yay! Okay, here comes the first one! Listen carefully..."
2. (delighted) "Oh no is right! Poor doggy lost its ball! You already know how it feels. Here comes the first one!"
3. (wait 2s) (encouraging) "It is easy — I say what happens, and you tell me what the doggy feels. Here is the first one..."

**Screen:** Stuffed dog photo on the left; on the right, a cartoon speech-bubble icon with "Emotion Translator" in playful letters and a simple animation of the dog with a thought bubble ("Oh no, my ball!").

#### Step 3: Multi-Round Interaction

**Round 1 — "Warm Sunshine":**

**AI says:** (warm, cozy narrator) "Mmmmm... it is morning time. Warm sunshine comes through the window and lands right on the doggy's belly. The doggy stretches out big and does a huuuge yawn! What does the doggy say?"

**Child responses:**

1. (Ideal) "Ahhhh!" / "So cozy!" / "Mmm warm!" / "Happy!"
2. (Unexpected) "Doggy sleeping!" / "I like sunshine!" / giggles or makes a yawn sound.
3. (No response) Child is quiet or looking at the photo.

**AI follow-up:**

1. (warm) "Ahhhh, so cozy! The doggy feels all warm and snuggly in that sunshine. You knew just how it felt!"
2. (gentle) "You like sunshine too! I bet the doggy is saying 'Mmmmm, this sunshine feels so warm on my tummy!' You are a great Emotion Translator!"
3. (wait 2s) (helpful) "The sunshine feels so warm and cozy on the doggy's belly. Is the doggy feeling happy or grumpy?"

**Screen:** Illustration of a cozy dog napping in a sunbeam with gentle golden glow pulsing around its belly; "ROUND 1" stamp with a warm yellow star.

**Round 2 — "Oops, a Bump!":**

**AI says:** (surprised narrator) "Uh oh! The doggy is walking along and — OOPS! — it trips and goes BUMP right on its bottom! What a surprise! What does the doggy say?"

**Child responses:**

1. (Ideal) "Ouch!" / "Oh no!" / "Whoa!" / "Ow ow ow!"
2. (Unexpected) "Haha, doggy fell!" / "Bump!" / "I fall down too!"
3. (No response) Child is quiet or watching.

**AI follow-up:**

1. (animated) "Ouch! Poor doggy got a surprise bump! But I think the doggy is okay — just a little shocked! You felt that surprise right away!"
2. (warm) "Bump! Yes! The doggy went bump and got SO surprised — big wide eyes and everything! You fall down sometimes too, and you know just how it feels!"
3. (wait 2s) (helpful) "The doggy went bump! Was the doggy surprised or was the doggy expecting it?"

**Screen:** Illustration of a dog looking wide-eyed and surprised after a tumble with cartoon stars and motion lines around it; "ROUND 2" stamp with a blue star.

**Round 3 — "Favorite Treat":**

**AI says:** (excited narrator) "Ooh ooh ooh! Sniff sniff! Someone is bringing the doggy's favorite treat! The doggy can smell it coming — it smells SO good! The tail starts going wag wag wag! What does the doggy do?"

**Child responses:**

1. (Ideal) "YAY!" / "Woof woof!" / "Gimme gimme!" / "So excited!" / "Wag wag!"
2. (Unexpected) "I like treats too!" / "Yummy!" / child bounces or claps.
3. (No response) Child is quiet or watching.

**AI follow-up:**

1. (thrilled) "YAY is right! The doggy is SO excited — tail wagging like crazy, jumping up and down! You are the BEST Emotion Translator!"
2. (delighted) "You like treats too! The doggy is going 'Yay yay yay, my favorite!' — tail wagging SO fast! You and the doggy feel the same way about treats!"
3. (wait 2s) (helpful) "That treat smells amazing! Is the doggy feeling calm and quiet... or super duper excited?"

**Screen:** Illustration of a dog wagging its tail wildly with excitement, tongue out, little treat icon floating nearby with sparkle lines; "ROUND 3" stamp with a golden star and confetti burst.

#### Step 4: Celebration

**AI says:** (proud, beaming) "WOW! You knew every single feeling! Cozy in the sunshine, surprised by the bump, and SO excited for that treat! You are officially an... EMOTION TRANSLATOR! You gave the doggy a voice!"

**Child responses:**

1. (Ideal) "Yay!" / "I did it!" / giggles or cheers.
2. (Unexpected) "More doggy!" / "Again!" / "I love the doggy!"

**AI follow-up:**

1. (beaming) "The BEST Emotion Translator! The doggy is so lucky to have you!"
2. (delighted) "You love the doggy! And the doggy loves YOU — because you understand all its feelings!"

**Screen:** Golden badge animation with "EMOTION TRANSLATOR" in bold playful letters, stuffed dog photo inside the badge, confetti in pink and gold, and a cheerful chime.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what you did today? The same fluffy doggy felt cozy, surprised, and excited — all different feelings, depending on what happened! When we imagine how someone else feels, that is called Perspective — seeing the world through someone else's eyes. You are not just a translator. You are a wonderful friend."

**Child responses:**

1. (Ideal) "Perspective!" / "I'm a friend!" / repeats a word happily.
2. (Unexpected) "Bye doggy!" / "Can we play again?"

**AI follow-up:**

1. (celebrating) "That is right — Perspective! You earned your badge, Emotion Translator. Next time you see a friend looking happy or sad, you will know just how they feel!"
2. (warm) "We can play again soon! And next time, maybe the doggy will have brand new feelings for you to discover. Bye bye, Emotion Translator!"

**Screen:** Emotion Translator badge centered with "Perspective" in warm golden lettering below; a heart-and-eyes icon for Perspective; stuffed dog photo glowing warmly behind the text with soft sparkle animations.
