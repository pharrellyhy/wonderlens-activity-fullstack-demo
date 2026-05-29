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
      image: /activity-assets/activity_phoneme_treasure_hunt/items/ball.png
    - id: book
      label: Book
      image: /activity-assets/activity_phoneme_treasure_hunt/items/book.png
    - id: banana
      label: Banana
      image: /activity-assets/activity_phoneme_treasure_hunt/items/banana.png
    - id: basket
      label: Basket
      image: /activity-assets/activity_phoneme_treasure_hunt/items/basket.png
  distractors:
    - id: cup
      label: Cup
      image: /activity-assets/activity_phoneme_treasure_hunt/items/cup.png
    - id: spoon
      label: Spoon
      image: /activity-assets/activity_phoneme_treasure_hunt/items/spoon.png
    - id: toy_car
      label: Toy car
      image: /activity-assets/activity_phoneme_treasure_hunt/items/toy_car.png
    - id: leaf
      label: Leaf
      image: /activity-assets/activity_phoneme_treasure_hunt/items/leaf.png
    - id: sock
      label: Sock
      image: /activity-assets/activity_phoneme_treasure_hunt/items/sock.png
    - id: pencil
      label: Pencil
      image: /activity-assets/activity_phoneme_treasure_hunt/items/pencil.png
step_instructions:
  hook:
    goal: "Open Phoneme Treasure Hunt, name the child as a Sound Treasure Hunter, and introduce a friendly target sound."
    constraint: "T1 max 3 sentences, text-only, do not require a photo, end with a yes-or-ready question."
    emotion_tag: curious
  transition:
    goal: "Explain that each turn saves one word or object whose name starts with the target sound."
    constraint: "T1 max 3 sentences, give one example and invite the first find. Use phoneme_letter_card_01 when available; if not, use text-only sound prompts with no letter screen claim."
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
source_dialogue:
  source_intent_lock: The AI introduces a target sound, then the child finds an object whose word starts with that sound.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `collect`.
  - 'Preserve this source sequence: The AI introduces a target sound, then the child finds an object whose word starts with that sound.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Phoneme Treasure Hunt. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the sound treasure hunter role, notices the starter cue, or names something connected to the target sound and first object.
      unexpected: Child asks for another game, starts the matching-item hunt before the Phoneme Treasure Hunt mission is framed, or follows an unrelated topic.
      no_response: Child watches the Phoneme Treasure Hunt title/trigger card without taking the sound treasure hunter role yet.
    ai_followups:
      ideal: Name the sound treasure hunter role, connect it to the starter cue, and preview the first matching-item hunt.
      unexpected: Acknowledge the request, return to the Phoneme Treasure Hunt promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Point to the Phoneme Treasure Hunt role card and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the matching-item hunt loop for Phoneme Treasure Hunt or asks for the easiest version.
      unexpected: Child tries to skip the target sound and first object, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Phoneme Treasure Hunt rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Phoneme Treasure Hunt loop as AI prompt, child matching-item hunt, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the target sound and first object, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Phoneme Treasure Hunt rule in one sentence and ask for yes, a point, or the first chance to find or show one match.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the card is unavailable, the AI repeats the target sound by voice only and must not claim the screen is showing a letter.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: The AI introduces a target sound, then the child finds an object whose word starts with that sound. Ask the child to find or match in the first small turn.'
      example_ai_line: 'Let us start: The AI introduces a target sound, then the child finds an object whose word starts with that sound. What is your first try?'
      child_responses:
        ideal: The child finds or names something that fits the target sound and first object and lets it become a collected token.
        unexpected: Child offers something that does not match the target sound and first object, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for the target sound and first object but does not name, point to, or show an item.
      ai_followups:
        ideal: Name the matching evidence for the target sound and first object, add the token to the collection, and preview what changes next.
        unexpected: Keep the hunt rule visible, contrast one non-match with one allowed example, and ask for a safer match for the target sound and first object.
        no_response: '[wait 2s] Give one concrete example that would count for the target sound and first object, then ask the child to point, say, or show one.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the card is unavailable, the AI repeats the target sound by voice only and must not claim the screen is showing a letter.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second collect turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child finds or names something that fits the second object for the same sound and lets it become a collected token.
        unexpected: Child offers something that does not match the second object for the same sound, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for the second object for the same sound but does not name, point to, or show an item.
      ai_followups:
        ideal: Name the matching evidence for the second object for the same sound, add the token to the collection, and preview what changes next.
        unexpected: Keep the hunt rule visible, contrast one non-match with one allowed example, and ask for a safer match for the second object for the same sound.
        no_response: '[wait 2s] Give one concrete example that would count for the second object for the same sound, then ask the child to point, say, or show one.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the card is unavailable, the AI repeats the target sound by voice only and must not claim the screen is showing a letter.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child finds or names something that fits the sound treasure recap and lets it become a collected token.
        unexpected: Child offers something that does not match the sound treasure recap, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for the sound treasure recap but does not name, point to, or show an item.
      ai_followups:
        ideal: Name the matching evidence for the sound treasure recap, add the token to the collection, and preview what changes next.
        unexpected: Keep the hunt rule visible, contrast one non-match with one allowed example, and ask for a safer match for the sound treasure recap.
        no_response: '[wait 2s] Give one concrete example that would count for the sound treasure recap, then ask the child to point, say, or show one.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the card is unavailable, the AI repeats the target sound by voice only and must not claim the screen is showing a letter.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the sound treasure recap changed the Phoneme Treasure Hunt board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Phoneme Treasure Hunt payoff or ignores how the saved matching-item hunt turns connect.
      no_response: Child watches the Phoneme Treasure Hunt reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's matching-item hunt turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Phoneme Treasure Hunt reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Phoneme Treasure Hunt board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Connection. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Phoneme Treasure Hunt moment, asks to play again, or watches the phoneme hunt recap badge.
      unexpected: Child shifts topic before the recap names the matching-item hunt skill or Form and Connection.
      no_response: Child stays on the Phoneme Treasure Hunt recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same collect mechanic and the phoneme hunt frame.
      unexpected: Close Phoneme Treasure Hunt first, name the practiced matching-item hunt, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Phoneme Treasure Hunt badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `collect`, focal attribute `phoneme_hunt`, and next-step hint.
  synthesis:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the sound treasure recap changed the Phoneme Treasure Hunt board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Phoneme Treasure Hunt payoff or ignores how the saved matching-item hunt turns connect.
      no_response: Child watches the Phoneme Treasure Hunt reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's matching-item hunt turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Phoneme Treasure Hunt reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Phoneme Treasure Hunt board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
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
