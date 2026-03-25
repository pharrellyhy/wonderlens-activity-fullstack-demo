---
activity_type: sound_detective_agency_piano
entity_name: piano
category: category_5
display_label: Piano
tier: T1
ib_theme: How We Express Ourselves
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [piano, keys, music, sound, instrument]
feature_keywords: [black, white, row, teeth, strings]
photo_features: [black and white keys, wooden body, pedals, music stand]
plain_description: "Go outside to find 3 things that make interesting sounds, describe each sound, and then sort them from highest to lowest pitch."
steps_summary:
  - "Watch a quick example of tapping something and describing its sound"
  - "Look at the piano and talk about the sounds it makes"
  - "Find 3 things outside that make sounds when tapped or shaken"
  - "Describe each sound and sort them by pitch"
  - "Earn the Sound Detective badge!"
creative_slots:
  observation_angle: form
  collection_criterion: Find things outside that make interesting sounds when you tap, shake, or blow on them
  collection_count: 3
  mission_metaphor: You are a Sound Detective on an acoustic investigation!
  role_title: Sound Detective
  synthesis_type: sorting_game
  stuck_hint: Try looking down at sticks and rocks for tap-tap sounds, or at metal fences for clang sounds.
  naming_prompt: What kind of sound does this make when you tap or shake it?
  detail_question_template: "What kind of sound does this one make — is it high or low, loud or soft?"
  sorting_criterion: "pitch (highest sounds to lowest sounds)"
collection_catalog:
  correct:
  - id: metal_fence
    label: Metal fence
    image: /icons/metal_fence.png
  - id: wooden_bench
    label: Wooden bench
    image: /icons/wooden_bench.png
  - id: dry_leaves
    label: Dry leaves
    image: /icons/dry_leaves.png
  - id: hollow_pipe
    label: Hollow pipe
    image: /icons/hollow_pipe.png
  distractors:
  - id: soft_moss
    label: Soft moss
    image: /icons/soft_moss.png
  - id: fluffy_cloud
    label: Fluffy cloud
    image: /icons/fluffy_cloud.png
  - id: smooth_pebble
    label: Smooth pebble
    image: /icons/smooth_pebble.png
  - id: green_grass
    label: Green grass
    image: /icons/green_grass.png
  - id: quiet_puddle
    label: Quiet puddle
    image: /icons/quiet_puddle.png
  - id: flower_petal
    label: Flower petal
    image: /icons/flower_petal.png
  - id: pinecone
    label: Pinecone
    image: /icons/pinecone.png
  - id: sand_pile
    label: Sand pile
    image: /icons/sand_pile.png
step_instructions:
  hook:
    goal: React with wonder to the piano's black and white keys lined up like neat teeth. Ask the child an imaginative question
      about what they think the piano sounds like.
    constraint: T1 max 3 sentences, experience/preference hook, MUST end with an imaginative question about the sound
    emotion_tag: excited
  transition:
    goal: 'Build on the child''s response to introduce the Sound Detective mission. Frame the collection as an acoustic investigation
      to find 3 things outside that make interesting sounds. End with a genuine invitation: Would you like to be a Sound Detective?'
    constraint: T1 max 3 sentences, build mission from child's response, frame as invitation not command, end with Would you
      like to be a Sound Detective?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: Spark curiosity about finding the first sound-making item. Suggest where to look (metal fences, wooden sticks) as
      an invitation, then ask the child to describe the sound it makes when tapped.
    scenario: first collection find — tapping or shaking an object
    constraint: T1 max 3 sentences, invitational phrasing, encourage the child to describe the sound
    emotion_tag: encouraging
    acceptable_themes: [metal, wood, tap, clang, loud, sound, fence, stick]
    escalation_note: easy first find — accessible items that make noise
  - round_number: 2
    goal: Celebrate the previous find, then spark curiosity for the next. Ask the child to compare this new sound to the first
      one (is it higher? lower?), and suggest a new material to look for.
    scenario: second collection find — comparing sounds
    constraint: T1 max 3 sentences, invitational phrasing, encourage comparison between sounds
    emotion_tag: curious
    acceptable_themes: [high, low, soft, wood, bench, tree, knock, sound]
    escalation_note: moderate — requires listening closely to differences
  - round_number: 3
    goal: Guide the child to find one more sound-making item — the third and last one. Build excitement and ask them to name
      this final acoustic treasure and its unique sound.
    scenario: third collection find
    constraint: T1 max 3 sentences, invitational phrasing, prompt child to go find it
    emotion_tag: excited
    acceptable_themes: [leaves, wind, shake, swoosh, rustle, loud, soft, sound]
    escalation_note: peak energy — final item to complete the collection
  celebrate:
    goal: Award the child the title 'Sound Detective' with ceremony. Recap their acoustic discoveries and celebrate the process
      of listening closely to the world.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific sounds from the hunt
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: they noticed how the Form (shape and material) changes the sound, and found a Connection
      between the piano and everyday objects. Plant a curiosity seed for next time.'
    constraint: T1 max 3 sentences, name Form and Connection naturally, warm goodbye
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye — great detective work, the sounds will be waiting next time.
    constraint: T1 max 3 sentences, no pressure to continue
    emotion_tag: gentle
  synthesis:
    goal: Look at all the collected items together and guide a sorting game. Invite the child to sort the items by whether
      they make a HIGH, LOW, or LOUD sound, comparing how different shapes make different noises.
    constraint: T1 max 3 sentences, sorting game + comparison, frame as invitation
    emotion_tag: amazed
screen_frames:
- widget: photo_display
  widget_params:
    description: Piano photo centered with the key pattern highlighted by a soft glow
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Piano Keys
  animation_label: Sparkle highlight
- widget: progress_tracker
  widget_params:
    filled: 1
    total: 4
  animation: card_slide_in
  trigger: on_round_1
  sfx_cue: photo_shutter_click
  widget_label: 'Find 1: First Sound'
  animation_label: Card slide in
- widget: progress_tracker
  widget_params:
    filled: 2
    total: 4
  animation: celebration_burst
  trigger: on_round_2
  sfx_cue: photo_shutter_click
  widget_label: 'Find 2: Second Sound'
  animation_label: Collection burst
- widget: progress_tracker
  widget_params:
    filled: 3
    total: 4
  animation: celebration_burst
  trigger: on_round_3
  sfx_cue: mission_complete_fanfare
  widget_label: 'Find 3: Final Sound'
  animation_label: Collection burst
celebration_frame:
  widget: badge_award
  widget_params:
    title: Sound Detective
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## The Sound Detective Agency

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Sound Detective Agency |
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Form, Connection |
| Related Concepts | Creativity, Expression, Discovery, Structure |
| ATL Skills Focus | Research Skills (observation, data collection), Thinking Skills (critical thinking, transfer), Communication Skills (expressing) |
| Game Style | comparison_chart |

### B. Activity Overview

**① Brief Description**

After photographing a piano, the AI marvels at its rows of black and white keys — like neat teeth all lined up — and wonders what OTHER things nearby make interesting sounds when you tap, shake, or blow on them. The child becomes a "Sound Detective" on a mission to find 3 things outside that make sounds, photograph each one, and describe what kind of sound it makes. At the end, the child sorts their collection into groups — things that make HIGH sounds, LOW sounds, or LOUD sounds — and reflects on how different shapes and sizes make different sounds, just like different piano keys.

**② Educational Purpose (KUD)**

- **K (Know):** Learn the vocabulary "keys," "strings," "high," "low," "loud," "soft." Learn that a piano has black keys in groups of two and three, that tight strings inside get tapped by tiny hammers, and that different shapes and materials make different sounds.
- **U (Understand):** Understand that the Form of an object — its shape, size, and material — affects what kind of sound it makes. Understand that there is a Connection between physical features and the sounds they produce, just as piano keys connect to strings to make music.
- **D (Do):** Observe and compare sound-making features of different objects. Sort collected sounds by properties like high, low, loud. Describe what sounds remind them of.

**③ Design Highlight**

The "Sound Detective" role turns a walk outside into an acoustic investigation. The child is not just finding objects — they are discovering that the world is full of things that make sounds, and that the SHAPE and SIZE of each thing changes what it sounds like. This mirrors the piano itself, where long strings sound low and short strings sound high. The synthesis step — sorting by high, low, or loud — earns the Form and Connection concepts naturally by linking physical features to acoustic properties.

**④ Typical Scenario**

Child photographs a piano, AI notices the rows of keys and wonders what else makes interesting sounds, child becomes a Sound Detective and finds 3 sound-making things outside, photographs each, describes its sound, and sorts them by whether the sound is high, low, or loud.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted surprise) "Wow, a piano! Look at all those keys lined up like neat teeth — black ones and white ones, all in a row! I bet every single key makes a different sound. What do you think a piano sounds like?"

**Child responses:**

1. (Ideal) "It goes ding ding!" / "It sounds pretty!" / "Loud!"
2. (Unexpected) "My grandma has one!" / "I can play it!"
3. (No response) Child looks at the piano or screen.

**AI follow-up:**

1. (impressed) "Yes! Some keys go ding ding up high, and some go boooom down low. The big keys and little keys all sound different! I wonder if OTHER things make cool sounds too. What if we went outside to find out?"
2. (warm, connecting) "Your grandma has a piano — how cool! A piano makes so many sounds from all those keys. You know what? The world outside has lots of sounds too. Want to go on a sound hunt?"
3. (wait 2s) (playful) "Listen — a piano has keys that go high and keys that go low. Every one sounds different! What if we went outside and found MORE things that make interesting sounds?"

**Screen:** Piano photo centered with the key pattern highlighted by a soft glow; animated musical notes of different sizes float upward from the keys.

#### Step 2: Rule Introduction + Demo

**AI says:** (adventurous, detective) "Okay — you are now an official Sound Detective! Your mission has three parts. Part one: find 3 things outside that make a sound. Part two: take a photo of each one. Part three: we sort them — does each one sound HIGH, LOW, or LOUD? Ready, Detective?"

**Child responses:**

1. (Ideal) "Ready!" / "Let's go!" / "I know where to find sounds!"
2. (Uncertain) "What makes a sound?" / "Like what?"
3. (No response) Child looks around.

**AI follow-up:**

1. (cheering) "Detective is on the case! Go outside, find something you can tap, shake, or blow on, and take a photo. Report back to me!"
2. (explaining warmly) "Anything that makes a noise when you tap it, shake it, or blow on it! A metal fence goes CLANG. A stick on the ground goes tap tap. Even a leaf can whoosh! Go find one and take a photo!"
3. (wait 2s) (gently encouraging) "Here is your first clue — look for something metal, something wooden, or something that moves in the wind. Tap it and listen! Then take a photo."

**Screen:** Mission card with "Sound Detective" badge (magnifying glass with a musical note), 4 collection slots (first filled with piano photo labeled "Sound: High + Low!"), and a three-step task list.

#### Step 3: Multi-Round Interaction

**Round 1 — First Find:**

*(Child photographs something outside — e.g., a metal fence, a railing, a pipe)*

**AI says:** (eager detective voice) "Detective report! What did you find? Try tapping it — what kind of sound does it make?"

**Child responses:**

1. (Ideal) "A fence! It goes clang clang!" / "It makes a loud sound!"
2. (Unexpected) "I just took a picture." / "I don't know."
3. (No response) Just takes the photo.

**AI follow-up:**

1. (thrilled) "Clang clang — a METAL sound! Metal things make loud, ringing sounds because they are hard and thin. That is like the piano strings — they ring when the hammers tap them! Detective Log: 'Metal Fence — Sound: Loud Clang!' Two more to find, Detective!"
2. (curious, scaffolding) "Great photo! Now try giving it a little tap with your hand. Does it go clang? Or thud? Or tap tap? Tell me what you hear!"
3. (wait 2s) (enthusiastic) "I see something in your photo! It looks hard and shiny. If you tapped it, I bet it would go CLANG — like a loud bell. What do YOU think it sounds like?"

**Screen:** New photo slides into second slot with sparkle animation; label appears: "Sound: ?" filling in based on conversation. Counter: "2 of 4."

**Round 2 — "Wood Sound":** Child photographs something wooden (e.g., a bench, stick, tree trunk); AI connects the deeper knock sound to the LOW keys on the piano, noting wood sounds softer than metal. Counter: "3 of 4."

**Round 3 — "Final Find":** Child photographs a third item (e.g., a leaf pile, wind chimes, a plastic bucket); AI celebrates that every find sounds different and links it back to shape and material. Collection complete.

**STUCK BRANCH:** AI suggests looking down at sticks and rocks for tap-tap sounds, at fences or railings for clang sounds, or at leaf piles for swoosh sounds.

#### Step 4: Celebration

**AI says:** (proud and excited) "Sound Detective, look at your collection! A piano with high and low keys, a [first find] that goes [sound], a [second find] that goes [sound], and a [third find] that goes [sound]. Now the big question — can you sort them? Which ones sound HIGH? Which ones sound LOW? Which ones sound LOUD?"

**Child responses:**

1. (Ideal) "The fence is loud! The wood is low!" / Child sorts with confidence.
2. (Unexpected) "They all sound different!" / "I do not know how to sort."
3. (No response) Child looks at the collection quietly.

**AI follow-up:**

1. (delighted) "Great sorting! See how each thing has a DIFFERENT sound? The shape and size change everything — thin metal goes high, thick wood goes low, big things go loud! Just like on the piano!"
2. (playfully scaffolding) "They DO all sound different! Let's start easy — which one was the LOUDEST? Point to it! Now which one was the softest? See — you just started sorting!"
3. (wait 2s) (warm, guiding) "Let's try this — think about the fence. Was it high, low, or loud? Now think about the wood. Was THAT high, low, or loud? See — they go in different groups!"

**Screen:** All 4 photos in a row; three sorting labels below: "HIGH" (light blue, high note), "LOW" (deep purple, low note), "LOUD" (red, exclamation mark). Photos shift under matching labels as child sorts.

**AI says:** (amazed, warm) "Detective, you found FOUR different things and they all make different sounds! A thin metal fence goes clang, a thick wood bench goes knock, a [third find] goes [sound] — every shape and material has its own voice. Why do you think different things sound different?"

**Child responses:**

1. (Ideal) "Because they are made of different stuff!" / "Big things sound low!"
2. (Unexpected) "I don't know." / "Because they just do."
3. (No response) Child looks at the screen.

**AI follow-up:**

1. (impressed) "That is exactly right! The SHAPE and what it is MADE OF change the sound. Thin, hard things ring high. Thick, soft things sound deep. The piano works the same way — short strings sound high and long strings sound low!"
2. (warm, extending) "That is a great wonder! Here is a clue — the fence is thin and metal, so it rings high. The bench is thick and wooden, so it sounds deeper. The stuff things are made of changes everything about their sound!"
3. (wait 2s) (gentle, prompting) "Think about the fence and the bench. One is thin metal, one is thick wood. They sound SO different! What is different about them that might change the sound?"

**Screen:** Collection displayed with each photo labeled with its sound; gentle animated sound waves in different colors (high = light blue, low = purple, loud = red); dotted connection lines link to the piano photo.

#### Step 5: Closing + IB Concepts

**AI says:** (warm celebration) "Congratulations, Sound Detective! You discovered the Form of so many different things — their shape, their size, what they are made of — and figured out how Form changes the sound they make. And you found a Connection between the piano and the whole world outside — keys connect to strings, fingers connect to sounds, and every different shape has its own special voice! You earned your Sound Detective Badge!"

**Child responses:**

1. (Engaged) "I am a Sound Detective!" / "Can I find more sounds?" / Child cheers.
2. (Quiet) Smiles or says nothing.
3. (No response) Child looks at the badge.

**AI follow-up:**

1. (encouraging) "Keep those detective ears open! Next time you are outside, try tapping, shaking, and listening. Every thing has a sound waiting to be discovered! See you on the next case, Detective!"
2. (warm) "Your badge is saved! Remember — every shape has its own voice. Bye for now, Detective!"
3. (wait 2s) (soft) "Your Sound Detective Badge is glowing. Great ears today, Detective!"

**Screen:** Golden "Sound Detective Badge" shaped like a magnifying glass with a musical note at center; piano photo in the middle surrounded by 3 collection photo insets. "Form" in bold blocky letters with shape icons, "Connection" in flowing script with dotted lines. Gentle chime and animated sound waves.
