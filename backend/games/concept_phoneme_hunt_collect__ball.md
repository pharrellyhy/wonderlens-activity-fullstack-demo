---
activity_type: concept_phoneme_hunt_collect__ball
entity_name: ball
category: category_5
display_label: Ball
tier: T1
ib_theme: How We Express Ourselves
ib_key_concept: Form
concepts_earned: &id001
- Form
- Connection
keywords:
- ball
- concept_phoneme_hunt_collect
- concept_phoneme_hunt_collect__ball
feature_keywords:
- beginning_b_sound
- spoken_word
photo_features:
- beginning_b_sound
- spoken_word
creative_slots:
  observation_angle: pattern
  collection_criterion: Let's use your sound ears and find things that start with /b/.
  collection_count: 2
  mission_metaphor: The child finds three everyday treasures whose names begin with the /b/ sound.
  role_title: B-Sound Scout
  synthesis_type: naming_story
  stuck_hint: Look nearby and choose something that matches the mission.
  naming_prompt: What should we call this find?
  detail_question_template: What do you notice about this find?
  sorting_criterion: ''
step_instructions:
  hook:
    goal: Notice the bound entity and ask one imaginative question.
    constraint: T1 max 2 sentences, must end with a question
    emotion_tag: excited
  transition:
    goal: Introduce the activity mission as a gentle invitation.
    constraint: T1 max 3 sentences, end with Would you like to try?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: 'Invite collection find 1: Let''s use your sound ears and find things that start with /b/.'
    scenario: collection find 1
    constraint: invitational phrasing, ask about the next matching item
    emotion_tag: encouraging
    acceptable_themes:
    - find
    - notice
    - match
    - look
    - choose
    escalation_note: collection round 1
  - round_number: 2
    goal: 'Invite collection find 2: Let''s use your sound ears and find things that start with /b/.'
    scenario: collection find 2
    constraint: invitational phrasing, ask about the next matching item
    emotion_tag: curious
    acceptable_themes:
    - find
    - notice
    - match
    - look
    - choose
    escalation_note: collection round 2
  celebrate:
    goal: Award the child the title 'B-Sound Scout' and recap the activity.
    constraint: T1 max 2 sentences, warm and specific
    emotion_tag: proud
  closing:
    goal: Connect the activity naturally to Form, Connection.
    constraint: T1 max 2 sentences, warm goodbye
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye that validates the child's participation.
    constraint: T1 max 2 sentences, no pressure
    emotion_tag: gentle
  synthesis:
    goal: Invite the child to compare or name the collected finds and make one tiny shared story.
    constraint: T1 max 3 sentences, frame as invitation
    emotion_tag: amazed
screen_frames:
- widget: photo_display
  widget_params:
    description: ball activity hero
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Ball
  animation_label: Sparkle highlight
- widget: progress_tracker
  widget_params:
    filled: 1
    total: 4
  animation: card_slide_in
  trigger: on_round_1
  sfx_cue: photo_shutter_click
  widget_label: Find 1
  animation_label: Collection progress
- widget: progress_tracker
  widget_params:
    filled: 2
    total: 4
  animation: celebration_burst
  trigger: on_round_2
  sfx_cue: photo_shutter_click
  widget_label: Find 2
  animation_label: Collection progress
- widget: progress_tracker
  widget_params:
    filled: 3
    total: 4
  animation: celebration_burst
  trigger: on_round_3
  sfx_cue: photo_shutter_click
  widget_label: Find 3
  animation_label: Collection progress
celebration_frame:
  widget: badge_award
  widget_params:
    title: B-Sound Scout
    concepts: *id001
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
plain_description: The child finds three everyday treasures whose names begin with the /b/ sound.
steps_summary:
- The child finds three everyday treasures whose names begin with the /b/ sound.
- Collect matching finds.
- Share a tiny wrap-up.
- Earn a badge.
collection_catalog:
  correct:
  - id: ball
    label: Ball
    image: /activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png
  distractors:
  - id: demo_distractor_1
    label: Other 1
    image: /icons/plain_leaf.png
  - id: demo_distractor_2
    label: Other 2
    image: /icons/plain_leaf.png
template_type: cat5
demo_filename: concept_phoneme_hunt_collect__ball.png
icon_src: /activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png
autodesign:
  source_activity_id: concept_phoneme_hunt_collect
  source_commit: 72b97241b4f3bd235fe23df91f2fb3aa08ce8b47
  package_dir: tests/fixtures/autodesign_packages/valid/degraded_cat5_reference_bound
entity_binding:
  entity_id: ball
  display_label: Ball
  source_entity_exemplar: ball
demo_support:
  status: degraded
  ui_template: cat5_judgment
  support_level: catalog_simulated_judgment
  unsupported_reasons: []
  degraded_reasons:
  - The demo uses catalog choices and text explanation for beginning-sound judgment instead of real camera/ASR validation.
  requires:
    generated_assets: true
    real_camera: false
    runtime_judgment: true
    device_round_screen: true
  consumer_notes:
    fullstack_demo: Show the limitation before play and do not claim production vision validation.
asset_readiness:
  status: ready
  required_missing: []
  optional_missing: []
asset_manifest:
  activity_id: concept_phoneme_hunt_collect
  entity_id: ball
  version: 1
  style_id: wonderlens_device_mint_soft_3d
  palette:
    shell: warm porcelain off-white
    screen: green-tinted near black
    primary_accent: soft mint green
    secondary_accent: pale sage
    shadow: cool gray green
  screen_targets:
    round_device_screen:
      aspect_ratio: '1:1'
      crop_shape: circle
      master_size: 1024
      safe_area: central 72 percent circle
    catalog_grid:
      aspect_ratio: '1:1'
      master_size: 512
  assets:
    ball_sound_card:
      id: ball_sound_card
      role: collection_correct
      label: Ball
      collection_catalog_id: ball
      requiredness: required
      accuracy_mode: illustrative
      source_strategy: generated_illustrative
      transformation_policy: generate_new
      prompt_en: Soft 3D educational toy illustration of a simple ball, mint green and warm porcelain palette, centered for
        a small round screen, no letters, no watermark.
      variants:
      - id: icon_256
        target: catalog_grid
        size: 256x256
        path: activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png
        browser_url: /activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png
      fallback_behavior: Use the spoken word "ball" without showing a card.
      browser_url: /activity-assets/concept_phoneme_hunt_collect__ball/ball_sound_card__icon_256.png
play_rounds: 2
---

## B-Sound Treasure Hunt

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | B-Sound Treasure Hunt |
| Activity Category | 5 -- Collection/Tracking Exploration (Out-of-Device, Solo) |
| Recommended Tier | T1 (ages 4-6) |
| Core IB Key Concepts | Form and Connection |
| Related Concepts | Sound Pattern, Beginning Sound, Classification, Evidence |
| ATL Skills Focus | Communication Skills (sound play), Research Skills (finding examples), Thinking Skills (classification) |
| Experience Pillar | Adventure |
| Game Style | quest_collector |

### B. Activity Overview

**1. Brief Description**

The child hears the target sound `/b/` and finds three nearby objects whose names start with that sound. Each photo becomes a possible treasure, and the AI helps the child sound out the beginning.

**2. Educational Purpose (KUD)**

- **K (Know):** Words can start with the same sound; `/b/` begins words like ball, book, block, bear, bottle, and banana; pictures can remind us of spoken words.
- **U (Understand):** Form includes the shape of spoken words. Connection helps us group different objects by the same beginning sound.
- **D (Do):** Listen for `/b/`, find and photograph three matching treasures, and explain the first sound in each word.

**3. Design Highlight**

The treasure rule is a sound, not a visual color or shape. Each find must pass through a playful spoken check: name the object, hear the first sound, then decide whether it joins the `/b/` map. The optional card supports memory, but the core game works by voice, naming, and a visible treasure trail.

**4. Typical Scenario**

Child enters sound hunt mode; the AI says `/b/`, and the child searches the room for a ball, book, or block. A nonmatch can go into the different-sound basket without losing the three main treasure slots.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4-6)

#### Step 1: Transition Bridge

**AI says:** [playful sound tone] "Listen: /b/, /b/, /b/. It pops like a bubble. Ball starts with /b/. Can we find /b/ treasures?"

**Child responses:**

1. (Ideal) "Ball!" / "I see one!"
2. (Unexpected) "I see a car." / "I like bubbles."
3. (No response) Child listens or looks around.

**AI follow-up:**

1. [excited scout tone] "Yes, ball starts with /b/. Your sound ears are ready."
2. [warmly validating] "Cars are fun. This hunt needs /b/. Try ball, book, block, or bear."
3. [wait 2s] [gentle repeat tone] "Try it with me: /b/. Short and bouncy."

**Screen:** If `phoneme_letter_card_01` is available, show it beside a pulsing sound bubble. If unavailable, show only the bubble labeled "Sound: /b/" and do not show or mention a letter card.

#### Step 2: Mission Briefing -- Sound Treasure Scout

**AI says:** [adventurous guide tone] "You are the Sound Treasure Scout. Find three things with /b/ names. Snap each treasure. We will sound it out."

**Child responses:**

1. (Ideal) "Ready!" / "I know one!"
2. (Unexpected) "What is /b/?" / "Can I ask Mom?"
3. (No response) Child hesitates before searching.

**AI follow-up:**

1. [cheering] "Mission starts now. Find your first /b/ treasure."
2. [clear modeling tone] "/b/ is the first sound in ball. Ask a grown-up if you want."
3. [wait 2s] [helpful whisper] "Look for a ball, book, block, bear, bottle, or banana."

**Screen:** A treasure map appears with three empty slots. The sound bubble "/b/" sits at the top. If the optional card is available, a small card tab can reopen it; otherwise the tab is absent.

#### Step 3: Multi-Round Exploration

**Round 1 -- First /b/ Treasure:**

**AI says:** [curious scout tone] "First treasure photo! What is its name? Does it start with /b/?"

**Child responses:**

1. (Ideal) "Ball!" / "Book!" / "Bear!"
2. (Unexpected) "Cup." / "I do not know."
3. (No response) Child waits or points.

**AI follow-up:**

1. [triumphant] "Yes! Ball starts with /b/. Treasure 1 is found."
2. [kind redirect] "Cup starts with /k/. Good try. Can you find ball, book, or bear?"
3. [wait 2s] [soft clue tone] "Try naming it with me. If it starts /b/, it can join."

**Screen:** The photo moves into slot 1 with a "B-SOUND MATCH" stamp. If the optional card is available, it flashes once; otherwise the /b/ sound bubble bounces.

**Round 2 -- Second /b/ Treasure:**

**AI says:** [playful detective tone] "Second treasure photo! Say its name slowly. Do you hear /b/ at the start?"

**Child responses:**

1. (Ideal) "Block!" / "Bottle!"
2. (Unexpected) "It is blue." / "It is big."
3. (No response) Child holds the photo quietly.

**AI follow-up:**

1. [delighted] "Block starts with /b/. Treasure 2 joins the map."
2. [validating then focusing] "Blue and big are good details. Now listen: does its name start /b/?"
3. [wait 2s] [gentle model tone] "I will model one: bottle. /b/ottle. Now try yours."

**Screen:** Slot 2 fills. A dotted path connects treasure 1 and treasure 2. The sound bubble repeats "/b/..." with small pop marks.

**Round 3 -- Final /b/ Treasure:**

**AI says:** [building suspense] "Final treasure photo! If its name starts /b/, your sound map is complete."

**Child responses:**

1. (Ideal) "Banana!" / "Bag!" / "Box!"
2. (Unexpected) "I cannot find one." / "Nothing starts that way."
3. (No response) Child keeps searching or looks unsure.

**AI follow-up:**

1. [celebration burst] "Banana begins with /b/. Treasure 3 is found. Map complete."
2. [reassuring search coach] "That is okay. /b/ treasures hide. Check books, bags, blocks, beds, or bottles."
3. [wait 2s] [calm guide tone] "Search one small place. Try a shelf, bag, or toy bin."

**Screen:** Slot 3 glows. When accepted, all three slots pop in order. The map counter flips to "3 /b/ treasures."

**Round 3 helper branch -- Not a /b/ treasure yet:**

**AI says:** [friendly redirect tone] "This is a nice photo. I hear a different first sound. Let's keep hunting for /b/."

**Child responses:**

1. (Ideal) "I will find another." / "Maybe book!"
2. (Unexpected) "I want this one." / "It should count."
3. (No response) Child looks disappointed.

**AI follow-up:**

1. [encouraging] "Good plan. Book is a strong /b/ treasure."
2. [respectful and clear] "We can save this for another map. This map needs /b/."
3. [wait 2s] [soft reset tone] "No problem. Say /b/. Now look for ball, book, or bear."

**Screen:** The photo goes into a "different sound" basket. The three main treasure slots stay visible so progress is not lost.

#### Step 4: Magic Moment -- The B-Sound Map

**AI says:** [wonder-filled reveal tone] "Sound map complete! Look at your treasures. Ball, book, and banana are different things. But each one starts with /b/."

**Child responses:**

1. (Ideal) "They all start with /b/!" / "B-b-b!"
2. (Unexpected) "I like the banana." / "They are yellow."
3. (No response) Child looks at the completed map.

**AI follow-up:**

1. [impressed] "Yes! You found the hidden sound pattern."
2. [validating and extending] "Banana is tasty. It also starts with /b/. That makes it a sound treasure."
3. [wait 2s] [gentle repeat tone] "Listen again: ball, book, banana. /b/, /b/, /b/."

**Screen:** The three accepted photos arrange on a small treasure map. A path line connects their first sound bubbles. A banner says "B-Sound Team."

#### Step 5: Closing + IB Concepts

**AI says:** [warm celebration] "You did it, Sound Treasure Scout. You used Form today. You noticed word sounds. You used Connection too. Different treasures shared one first sound."

**Child responses:**

1. (Ideal) "I want another sound!" / "I found them!"
2. (Unexpected) "Can I find more B things?" / "I like the badge."
3. (No response) Child watches the badge screen.

**AI follow-up:**

1. [proud guide tone] "Your sound ears are strong. Next time, try a new sound."
2. [delighted] "More B things can join. Keep hunting after the badge shines."
3. [wait 2s] [soft goodbye tone] "Your B-Sound badge is saved. You found a sound pattern."

**Screen:** A "B-Sound Scout" badge appears with three photo insets. The words "Form" and "Connection" glow on the map. A next-step card says, "Next: try a new first sound."
