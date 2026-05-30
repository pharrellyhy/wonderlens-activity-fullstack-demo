---
activity_type: activity_animal_sound_imitation
activity_set: activity_text_game
source_export_id: concept_animal_sound_motion_voice
mechanic: motion_voice
entity_name: animal_sound_imitation
category: category_1
display_label: Animal Sound Imitation
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Perspective]
keywords: [animal, sound, imitate, voice, role]
feature_keywords: [animal card, voice, motion, safe, rabbit, cat meow, puppy]
photo_features: [rabbit card, cat meow card, puppy card, sound cue, performance card]
play_rounds: 3
plain_description: "The AI uses a fixed rabbit, cat meow, and puppy card sequence, and the child imitates each sound or speaks in that animal role."
steps_summary:
  - "Become an Animal Voice Performer."
  - "Try three safe animal voice or role prompts."
  - "Choose a favorite performance moment."
  - "Earn the Animal Voice Performer badge."
creative_slots:
  game_mechanic: motion_voice
  metaphor: "A tiny animal stage where the child can try safe voices and roles."
  role_title: Animal Voice Performer
  round_scenarios:
    - "Try a tiny rabbit sniff sound for the highlighted rabbit card."
    - "Change a cat meow with a soft/loud or happy/sleepy feeling."
    - "Speak one short friendly puppy line in the puppy role."
  escalation_axis: "simple sound to variation to role line"
  observation_detail: "fixed rabbit, cat meow, and puppy cards that suggest a sound or point of view"
step_instructions:
  hook:
    goal: "Open Animal Sound Imitation and invite a safe animal voice performance."
    constraint: "T1 max 3 sentences, remind safe volume, end with a question. Do not invent a different starter animal or claim a photo."
    emotion_tag: playful
  transition:
    goal: "Explain that each round is a small safe voice or role try."
    constraint: "T1 max 3 sentences, give a tiny demo and invite readiness. Use animal_sound_cards_01 as supportive art when available; visible sequence is rabbit card, cat meow card, puppy card. Do not invent a different animal or claim a photo."
    emotion_tag: excited
  rounds:
    - round_number: 1
      goal: "Ask for a tiny rabbit sniff sound."
      scenario: "rabbit card voice"
      constraint: "T1 max 3 sentences, encourage safe volume. Keep the animal as rabbit."
      emotion_tag: encouraging
      acceptable_themes: [rabbit, sound, gentle, voice, safe]
      escalation_note: "simple performance"
    - round_number: 2
      goal: "Ask for a cat meow with one feeling or volume change."
      scenario: "cat meow voice or volume"
      constraint: "T1 max 3 sentences, keep movement and volume safe. Keep the animal as cat."
      emotion_tag: curious
      acceptable_themes: [cat meow, loud, soft, happy, sleepy, voice]
      escalation_note: "performance variation"
    - round_number: 3
      goal: "Ask for one short friendly line spoken as the puppy."
      scenario: "puppy role line"
      constraint: "T1 max 3 sentences, ask for a short typed or spoken-style response. Keep the animal as puppy."
      emotion_tag: proud
      acceptable_themes: [puppy, says, role, line, favorite]
      escalation_note: "role perspective"
  celebrate:
    goal: "Award Animal Voice Performer and recap the safest favorite moment."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through animal features and role voice."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate the child trying a safe voice."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The AI prompts the fixed rabbit, cat meow, and puppy sequence, and the child imitates each sound or speaks in that animal role.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `motion_voice`.
  - 'Preserve this source sequence: rabbit sound, cat meow variation, puppy role line. Do not switch to dog-only, cat-only, or any animal not shown by the current asset.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Animal Sound Imitation. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the animal voice performer role, notices the starter cue, or names something connected to the first animal voice.
      unexpected: Child asks for another game, starts the safe sound or movement before the Animal Sound Imitation mission is framed, or follows an unrelated topic.
      no_response: Child watches the Animal Sound Imitation opening moment without taking the animal voice performer role yet.
    ai_followups:
      ideal: Name the animal voice performer role, connect it to the starter cue, and preview the first safe sound or movement.
      unexpected: Acknowledge the request, return to the Animal Sound Imitation promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Animal Sound Imitation role and the first animal, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Here is how we play: I invite, you try a safe animal voice, and we save one little turn each time.'
    child_responses:
      ideal: The child agrees to the safe sound or movement loop for Animal Sound Imitation or asks for the easiest version.
      unexpected: Child tries to skip the first animal voice, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Animal Sound Imitation rule without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Animal Sound Imitation loop as AI invite, child safe sound or movement, saved turn, and show the first response slot.
      unexpected: Keep the rule tied to the first animal voice, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Say the Animal Sound Imitation rule in one sentence and ask for a yes or the first chance to try a safe sound or movement.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `animal_sound_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, the AI describes the animal by voice and must not claim the screen is showing a picture.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the asset promise: the highlighted first animal is rabbit. Invite a tiny rabbit sniff or quiet rabbit sound, and do not switch to a different animal.'
      example_ai_line: 'First up is the rabbit. Would you like to try one tiny rabbit sniff at a safe volume?'
      child_responses:
        ideal: The child tries the first animal voice with safe volume, space, or body control.
        unexpected: Child makes the first animal voice too rough/loud, switches to an unrelated performance, or proposes an unsafe movement.
        no_response: Child watches the first animal voice cue without moving, sounding, or choosing a smaller version.
      ai_followups:
        ideal: Mirror the safe part of the first animal voice, save the performance turn, and cue the next variation.
        unexpected: Name the safety boundary, shrink the action to a safer version, and invite one controlled try for the first animal voice.
        no_response: '[wait 2s] Demonstrate the smallest safe version of the first animal voice, then invite the child to copy just that part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `animal_sound_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, the AI describes the animal by voice and must not claim the screen is showing a picture.'
  - round_number: 2
    source_contract:
      runtime_instruction: 'Keep the asset promise: the second animal is cat meow. Invite a meow with one soft/loud or sleepy/happy variation, and do not keep talking about the rabbit or puppy.'
      example_ai_line: Now it is the cat meow. Could your meow sound sleepy or soft?
      child_responses:
        ideal: The child tries the changed animal voice or volume with safe volume, space, or body control.
        unexpected: Child makes the changed animal voice or volume too rough/loud, switches to an unrelated performance, or proposes an unsafe movement.
        no_response: Child watches the changed animal voice or volume cue without moving, sounding, or choosing a smaller version.
      ai_followups:
        ideal: Mirror the safe part of the changed animal voice or volume, save the performance turn, and cue the next variation.
        unexpected: Name the safety boundary, shrink the action to a safer version, and invite one controlled try for the changed animal voice or volume.
        no_response: '[wait 2s] Demonstrate the smallest safe version of the changed animal voice or volume, then invite the child to copy just that part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `animal_sound_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, the AI describes the animal by voice and must not claim the screen is showing a picture.'
  - round_number: 3
    source_contract:
      runtime_instruction: 'Keep the asset promise: the third animal is puppy. Invite one short friendly puppy line, and do not introduce another animal.'
      example_ai_line: The puppy comes last. What is one friendly puppy line?
      child_responses:
        ideal: The child tries the favorite animal-role line with safe volume, space, or body control.
        unexpected: Child makes the favorite animal-role line too rough/loud, switches to an unrelated performance, or proposes an unsafe movement.
        no_response: Child watches the favorite animal-role line cue without moving, sounding, or choosing a smaller version.
      ai_followups:
        ideal: Mirror the safe part of the favorite animal-role line, save the performance turn, and cue the next variation.
        unexpected: Name the safety boundary, shrink the action to a safer version, and invite one controlled try for the favorite animal-role line.
        no_response: '[wait 2s] Demonstrate the smallest safe version of the favorite animal-role line, then invite the child to copy just that part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `animal_sound_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, the AI describes the animal by voice and must not claim the screen is showing a picture.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the favorite animal-role line changed the Animal Sound Imitation board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Animal Sound Imitation payoff or ignores how the saved safe sound or movement turns connect.
      no_response: Child watches the Animal Sound Imitation reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's safe sound or movement turns, name one concrete saved turn, and invite a short reflection.
      unexpected: Hold the Animal Sound Imitation reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Animal Sound Imitation board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Perspective. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Animal Sound Imitation moment, asks to play again, or watches the animal sound imitation recap badge.
      unexpected: Child shifts topic before the recap names the safe sound or movement skill or Form and Perspective.
      no_response: Child stays on the Animal Sound Imitation recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same motion_voice mechanic and the animal sound imitation frame.
      unexpected: Close Animal Sound Imitation first, name the practiced safe sound or movement, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Animal Sound Imitation badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `motion_voice`, focal attribute `animal_sound_imitation`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Animal stage card with sound tokens"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Animal Stage"
    animation_label: "Stage opens"
  - widget: character_display
    widget_params:
      description: "Gentle animal sound cue"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Voice 1"
    animation_label: "Sound pulse"
  - widget: character_display
    widget_params:
      description: "Animal voice changes feeling or volume"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Voice 2"
    animation_label: "Voice shift"
  - widget: character_display
    widget_params:
      description: "Animal role line spotlight"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Role Line"
    animation_label: "Spotlight"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Animal Voice Performer
    concepts: [Form, Perspective]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Animal Sound Imitation

Backend activity definition converted from `concept_animal_sound_motion_voice`.
