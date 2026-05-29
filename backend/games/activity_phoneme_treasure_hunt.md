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
photo_features: [letter B picture, word clue, B-word marker]
plain_description: "The AI introduces letter B, then the child finds or names objects whose words start with B."
steps_summary:
  - "Enter the Sound Treasure Hunter role and hear the letter B rule."
  - "Find or name three B-starting words or objects."
  - "Recap the B pattern and saved finds."
  - "Earn the Sound Treasure Hunter badge."
creative_slots:
  observation_angle: form
  collection_criterion: "objects or words whose names start with letter B"
  collection_count: 3
  mission_metaphor: "You are a Sound Treasure Hunter collecting words that begin with letter B."
  role_title: Sound Treasure Hunter
  synthesis_type: naming_story
  stuck_hint: "Try a B word near you, like ball, book, banana, or basket."
  naming_prompt: "What B word or B object did you find?"
  detail_question_template: "Which B word did you choose?"
  sorting_criterion: ""
story_scaffold:
  premise: "Each collected word becomes a B treasure in a tiny word map."
  harvest_per_round: b_word
  harvest_question_strategy: "R1: ask which B word was chosen; R2: compare to the first B word; R3: recap all B-starting words."
  synthesis_goal: "Show how the collected words connect because they start with B."
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
    goal: "Open Phoneme Treasure Hunt, name the child as a Sound Treasure Hunter, introduce the friendly letter B rule, and ask if they are ready to find B words."
    constraint: "T1 max 3 sentences, text-only, do not require a photo, do not ask how the letter feels or whether it is smooth or bumpy, end with a ready-to-find-B-words question."
    emotion_tag: curious
  transition:
    goal: "Explain that each turn saves one word or object whose name starts with letter B."
    constraint: "T1 max 3 sentences, give one example and invite the first find. Use phoneme_letter_card_01 when available; if not, use text-only B prompts with no letter screen claim."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask for the first word or object that starts with B."
      scenario: "first B-starting treasure"
      constraint: "T1 max 3 sentences, accept typed text as the find."
      emotion_tag: encouraging
      acceptable_themes: [letter b, b word, starts, object, match]
      escalation_note: "easy first B match"
    - round_number: 2
      goal: "Ask for a second matching word and connect it to the same letter B start."
      scenario: "second B-starting treasure"
      constraint: "T1 max 3 sentences, compare to the first word."
      emotion_tag: curious
      acceptable_themes: [same, starts, letter b, another, word]
      escalation_note: "repeat with comparison"
    - round_number: 3
      goal: "Ask for a final B word and help the child recap the B-starting pattern."
      scenario: "B treasure recap"
      constraint: "T1 max 3 sentences, prompt a short typed recap."
      emotion_tag: proud
      acceptable_themes: [three, letter b, words, starts, treasure]
      escalation_note: "complete the collection"
  celebrate:
    goal: "Celebrate the three B treasures and award Sound Treasure Hunter."
    constraint: "T1 max 3 sentences, mention the collected words when available."
    emotion_tag: proud
  closing:
    goal: "Name Form and Connection through the shape of beginning sounds and how B words connect."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  synthesis:
    goal: "Turn the collected B words into a tiny word map or chant."
    constraint: "T1 max 3 sentences, invite the child to notice the shared B beginning sound."
    emotion_tag: amazed
  early_exit:
    goal: "Gently close and validate any word the child found."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The AI introduces letter B, then the child finds an object whose word starts with B.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `collect`.
  - 'Preserve this source sequence: The AI introduces letter B, then the child finds an object whose word starts with B.'
  hook:
    runtime_instruction: Open from the source trigger, name the child's role, and keep the first question about finding words that start with letter B.
    example_ai_line: 'Today our letter is B. Are you ready to find words that start with B, like ball?'
    child_responses:
      ideal: The child accepts the sound treasure hunter role, notices the starter cue, or names something connected to letter B and a first B word.
      unexpected: Child asks for another game, starts the matching-item hunt before the Phoneme Treasure Hunt mission is framed, or follows an unrelated topic.
      no_response: Child watches the Phoneme Treasure Hunt title prompt without taking the sound treasure hunter role yet.
    ai_followups:
      ideal: Name the sound treasure hunter role, connect it to letter B, and preview the first B-word hunt.
      unexpected: Acknowledge the request, return to the Phoneme Treasure Hunt promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Say "Ball starts with B," then ask if the child is ready to find one B word.'
    screen: Shows title, child role, source trigger, and empty progress markers.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I name letter B, you choose a B word, and one marker lights up for each turn.'
    child_responses:
      ideal: The child agrees to the matching-item hunt loop for Phoneme Treasure Hunt or asks for the easiest version.
      unexpected: Child tries to skip letter B and the first B object, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Phoneme Treasure Hunt rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Phoneme Treasure Hunt loop as AI prompt, child B-word hunt, saved marker, and show the first response slot.
      unexpected: Keep the rule tied to letter B and the first B object, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Phoneme Treasure Hunt rule in one sentence and ask for yes or the first chance to find one B match.'
    screen: 'Shows the rule strip, current round marker, and asset/fallback note. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the asset is unavailable, the AI repeats the B rule by voice only and must not claim the screen is showing a letter.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: the AI introduces letter B, then the child finds an object whose word starts with B. Ask the child to choose the first B-starting item.'
      example_ai_line: 'Let us start with letter B. Which item starts with B: ball, cup, or book?'
      child_responses:
        ideal: The child finds or names something that starts with B and lets it become a collected word.
        unexpected: Child offers something that does not start with B, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for the first B item but does not name or choose an item.
      ai_followups:
        ideal: Name the B-starting evidence, add the word to the collection, and preview what changes next.
        unexpected: Keep the B rule visible, contrast one non-match with one allowed B example, and ask for a safer B match.
        no_response: '[wait 2s] Give one concrete B example like ball, then ask the child to say or type one B word.'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the asset is unavailable, the AI repeats the B rule by voice only and must not claim the screen is showing a letter.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second B-starting item.
      example_ai_line: Now choose another word that starts with B. Which B word should we save next?
      child_responses:
        ideal: The child finds or names a second B-starting word and lets it become a collected word.
        unexpected: Child offers something that does not start with B, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for a second B item but does not name or choose an item.
      ai_followups:
        ideal: Name the B-starting evidence, add the word to the collection, and preview what changes next.
        unexpected: Keep the B rule visible, contrast one non-match with one allowed B example, and ask for a safer B match.
        no_response: '[wait 2s] Give one concrete B example like banana, then ask the child to say or type one B word.'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the asset is unavailable, the AI repeats the B rule by voice only and must not claim the screen is showing a letter.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask for a final B-starting item and prepare to recap the three B words.
      example_ai_line: 'One last B word. Which item starts with B: basket, car, or sock?'
      child_responses:
        ideal: The child finds or names a final B-starting word and lets it become a collected word.
        unexpected: Child offers something that does not start with B, changes the hunt rule, or asks for credit without a find.
        no_response: Child scans for the final B item but does not name or choose an item.
      ai_followups:
        ideal: Name the B-starting evidence, add the word to the collection, and preview the B-word recap.
        unexpected: Keep the B rule visible, contrast one non-match with one allowed B example, and ask for a safer B match.
        no_response: '[wait 2s] Give one concrete B example like basket, then ask the child to say or type one B word.'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `phoneme_letter_card_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If the asset is unavailable, the AI repeats the B rule by voice only and must not claim the screen is showing a letter.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the sound treasure recap changed the Phoneme Treasure Hunt board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Phoneme Treasure Hunt payoff or ignores how the saved matching-item hunt turns connect.
      no_response: Child watches the Phoneme Treasure Hunt reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's matching-item hunt turns, name one concrete saved word, and invite a short reflection.
      unexpected: Hold the Phoneme Treasure Hunt reveal, name the saved turn that matters, and ask what changed because of it.
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
      ideal: Tie the reveal to the child's matching-item hunt turns, name one concrete saved word, and invite a short reflection.
      unexpected: Hold the Phoneme Treasure Hunt reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Phoneme Treasure Hunt board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Letter B prompt with three empty treasure markers"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Letter B"
    animation_label: "B prompt appears"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 3
    animation: card_slide_in
    trigger: on_round_1
    widget_label: "Find 1"
    animation_label: "First marker"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 3
    animation: celebration_burst
    trigger: on_round_2
    widget_label: "Find 2"
    animation_label: "Second marker"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 3
    animation: celebration_burst
    trigger: on_round_3
    widget_label: "Find 3"
    animation_label: "Final marker"
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
