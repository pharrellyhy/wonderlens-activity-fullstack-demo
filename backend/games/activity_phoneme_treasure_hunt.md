---
activity_type: activity_phoneme_treasure_hunt
activity_set: activity_text_game
source_export_id: concept_phoneme_hunt_collect
mechanic: collect
entity_name: phoneme_treasure_hunt
category: category_5
display_label: Phoneme Treasure Hunt
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [phoneme, sound, word, treasure, letter]
feature_keywords: [start sound, word, object, clue]
photo_features: [letter card, word clue, sound token]
plain_description: "The AI introduces a target sound, then the child finds or names objects whose words start with that sound."
steps_summary:
  - "Enter the sound treasure hunter role and hear the target sound."
  - "Find or name three matching words or objects."
  - "Recap the sound pattern and saved finds."
  - "Earn the Sound Treasure Hunter badge."
creative_slots:
  observation_angle: form
  collection_criterion: "objects or words whose names start with the target sound"
  collection_count: 3
  mission_metaphor: "You are a Sound Treasure Hunter collecting words that begin with one sound."
  role_title: Sound Treasure Hunter
  synthesis_type: naming_story
  stuck_hint: "Try a word near you, like ball, book, or banana if the sound is b."
  naming_prompt: "What word or object did you find for the target sound?"
  detail_question_template: "What sound does your word start with?"
  sorting_criterion: ""
story_scaffold:
  premise: "Each collected word becomes a sound treasure in a tiny word map."
  harvest_per_round: sound_label
  harvest_question_strategy: "R1: ask for first sound; R2: compare to first word; R3: recap all matching starts."
  synthesis_goal: "Show how the collected words connect through the same beginning sound."
  synthesis_format: collaborative_story
  story_themes:
    - "The sound treasures light up one path."
    - "The words become a little chant."
collection_catalog:
  correct:
    - id: ball
      label: Ball
      image: /icons/ball.png
    - id: book
      label: Book
      image: /icons/book.png
    - id: banana
      label: Banana
      image: /icons/banana.png
    - id: basket
      label: Basket
      image: /icons/basket.png
  distractors:
    - id: cup
      label: Cup
      image: /icons/cup.png
    - id: spoon
      label: Spoon
      image: /icons/spoon.png
    - id: toy_car
      label: Toy car
      image: /icons/toy_car.png
    - id: leaf
      label: Leaf
      image: /icons/leaf.png
    - id: sock
      label: Sock
      image: /icons/sock.png
    - id: pencil
      label: Pencil
      image: /icons/pencil.png
step_instructions:
  hook:
    goal: "Open Phoneme Treasure Hunt, name the child as a Sound Treasure Hunter, and introduce a friendly target sound."
    constraint: "T1 max 3 sentences, text-only, do not require a photo, end with a yes-or-ready question."
    emotion_tag: curious
  transition:
    goal: "Explain that each turn saves one word or object whose name starts with the target sound."
    constraint: "T1 max 3 sentences, give one example and invite the first find."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask for the first matching word or object."
      scenario: "first beginning-sound treasure"
      constraint: "T1 max 3 sentences, accept typed text as the find."
      emotion_tag: encouraging
      acceptable_themes: [sound, word, starts, object, match]
      escalation_note: "easy first sound match"
    - round_number: 2
      goal: "Ask for a second matching word and connect it to the same start sound."
      scenario: "second beginning-sound treasure"
      constraint: "T1 max 3 sentences, compare to the first word."
      emotion_tag: curious
      acceptable_themes: [same, starts, sound, another, word]
      escalation_note: "repeat with comparison"
    - round_number: 3
      goal: "Ask for a final word and help the child recap the sound pattern."
      scenario: "sound treasure recap"
      constraint: "T1 max 3 sentences, prompt a short typed recap."
      emotion_tag: proud
      acceptable_themes: [three, sound, words, starts, treasure]
      escalation_note: "complete the collection"
  celebrate:
    goal: "Celebrate the three sound treasures and award Sound Treasure Hunter."
    constraint: "T1 max 3 sentences, mention the collected words when available."
    emotion_tag: proud
  closing:
    goal: "Name Form and Connection through the shape of beginning sounds and how words connect."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  synthesis:
    goal: "Turn the collected words into a tiny sound map or chant."
    constraint: "T1 max 3 sentences, invite the child to notice the shared beginning sound."
    emotion_tag: amazed
  early_exit:
    goal: "Gently close and validate any word the child found."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Target sound card with three empty treasure tokens"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Target Sound"
    animation_label: "Sound card appears"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 3
    animation: card_slide_in
    trigger: on_round_1
    widget_label: "Find 1"
    animation_label: "First token"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 3
    animation: celebration_burst
    trigger: on_round_2
    widget_label: "Find 2"
    animation_label: "Second token"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 3
    animation: celebration_burst
    trigger: on_round_3
    widget_label: "Find 3"
    animation_label: "Final token"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Sound Treasure Hunter
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Phoneme Treasure Hunt

Backend activity definition converted from `concept_phoneme_hunt_collect`.
