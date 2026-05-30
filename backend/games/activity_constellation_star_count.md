---
activity_type: activity_constellation_star_count
activity_set: activity_text_game
source_export_id: concept_constellation_star_count_enumerate
mechanic: enumerate
entity_name: constellation_star_count
category: category_1
display_label: Constellation Star Count
tier: T1
ib_theme: "How The World Works"
ib_key_concept: Form
concepts_earned: [Form]
keywords: [constellation, star, count, sky, pattern]
feature_keywords: [stars, number, pattern, group]
photo_features: [star card, constellation dots, counting path]
play_rounds: 3
plain_description: "The screen shows a small constellation or star group, and the child counts how many stars are visible."
steps_summary:
  - "Become a Star Counter."
  - "Count three star groups."
  - "Compare how star forms make different patterns."
  - "Earn the Star Counter badge."
creative_slots:
  game_mechanic: enumerate
  metaphor: "A small night-sky map where each counted star lights a path."
  role_title: Star Counter
  round_scenarios:
    - "Count a small group of stars."
    - "Count a second group with a different shape."
    - "Count a final constellation and compare the pattern."
  escalation_axis: "small group to changed pattern to final count"
  observation_detail: "visible star dots arranged in a pattern"
step_instructions:
  hook:
    goal: "Open Constellation Star Count and invite the child to count visible stars."
    constraint: "T1 max 3 sentences, end with a counting question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round asks for a typed number and a quick look at the star shape."
    constraint: "T1 max 3 sentences, include one tiny example. Use constellation_count_cards_01 when available; if not, use voice-only or text-only star patterns and do not claim a constellation card is shown."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to count the first small star group."
      scenario: "first star group"
      constraint: "T1 max 3 sentences, invite a number answer."
      emotion_tag: encouraging
      acceptable_themes: [one, two, three, count, stars]
      escalation_note: "small count"
    - round_number: 2
      goal: "Ask the child to count a changed star pattern."
      scenario: "second star pattern"
      constraint: "T1 max 3 sentences, connect count to pattern."
      emotion_tag: curious
      acceptable_themes: [count, stars, pattern, more, less]
      escalation_note: "changed arrangement"
    - round_number: 3
      goal: "Ask for the final count and a short comparison."
      scenario: "final constellation count"
      constraint: "T1 max 3 sentences, ask which group looked bigger or smaller."
      emotion_tag: proud
      acceptable_themes: [count, final, pattern, bigger, smaller]
      escalation_note: "count plus comparison"
  celebrate:
    goal: "Award Star Counter and recap the counted groups."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form through star groups, numbers, and pattern shapes."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any counting attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The child counts visible stars in a constellation card or simplified star pattern.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `enumerate`.
  - 'Preserve this source sequence: The child counts visible stars in a constellation card or simplified star pattern.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Constellation Star Count. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the star counter role, notices the starter cue, or names something connected to the first star group.
      unexpected: Child asks for another game, starts the counting or naming step before the Constellation Star Count mission is framed, or follows an unrelated topic.
      no_response: Child watches the Constellation Star Count opening moment without taking the star counter role yet.
    ai_followups:
      ideal: Name the star counter role, connect it to the starter cue, and preview the first counting or naming step.
      unexpected: Acknowledge the request, return to the Constellation Star Count promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Star Counter role and the first little group of stars, then model one tiny gentle response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Here is how we play: I ask, you count the stars, and we light up one star on our path each turn.'
    child_responses:
      ideal: The child agrees to the counting or naming step loop for Constellation Star Count or asks for the easiest version.
      unexpected: Child tries to skip the first star group, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Constellation Star Count rule without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Constellation Star Count loop as AI asks, child counts the stars, one star lights up, and show where the first answer goes.
      unexpected: Keep the rule tied to the first star group, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Say the Constellation Star Count rule in one sentence and ask if they would like to count the first little group of stars together.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `constellation_count_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a voice-only imaginary star-counting riddle and do not claim a constellation is displayed.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: the child counts the visible stars in a constellation or simplified star pattern. Invite the child to count the first small group of stars.'
      example_ai_line: 'Let us begin counting the stars in this little group. Would you like to tell me how many you see?'
      child_responses:
        ideal: The child counts, names, or checks the stars in the first star group.
        unexpected: Child guesses the first star group without looking, counts unrelated things, or changes which stars to count.
        no_response: Child looks at the first star group without saying a number, name, or first count.
      ai_followups:
        ideal: Repeat the counted stars, light up the number you heard, and show which stars come next.
        unexpected: Bring attention back to the first star group, count one star aloud, and invite the child to keep going.
        no_response: '[wait 2s] Name the first star in the first group, say "one," and invite the child to say the next number.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `constellation_count_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a voice-only imaginary star-counting riddle and do not claim a constellation is displayed.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second enumerate turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child counts, names, or checks the items required for the second star group or pattern.
        unexpected: Child guesses the second star group or pattern without looking, counts unrelated items, or changes the target set.
        no_response: Child looks at the second star group or pattern without saying a number, name, or first count.
      ai_followups:
        ideal: Repeat the counted stars, light up the number you heard, and show which stars come next.
        unexpected: Bring attention back to the second star group or pattern, count one star aloud, and invite the child to keep going.
        no_response: '[wait 2s] Name the first star in the second group or pattern, say "one," and invite the child to say the next number.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `constellation_count_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a voice-only imaginary star-counting riddle and do not claim a constellation is displayed.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child counts, names, or checks the items required for the total constellation recap.
        unexpected: Child guesses the total constellation recap without looking, counts unrelated items, or changes the target set.
        no_response: Child looks at the total constellation recap without saying a number, name, or first count.
      ai_followups:
        ideal: Repeat the counted stars, light up the number you heard, and show which stars come next.
        unexpected: Bring attention back to the total constellation recap, count one star aloud, and invite the child to keep going.
        no_response: '[wait 2s] Name the first star in the whole constellation, say "one," and invite the child to say the next number.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `constellation_count_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a voice-only imaginary star-counting riddle and do not claim a constellation is displayed.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the total constellation recap changed the Constellation Star Count board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Constellation Star Count payoff or ignores how the saved counting or naming step turns connect.
      no_response: Child watches the Constellation Star Count reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's counting or naming step turns, name one star group they counted, and invite a short reflection.
      unexpected: Hold the Constellation Star Count reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Constellation Star Count board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Constellation Star Count moment, asks to play again, or watches the constellation star count recap badge.
      unexpected: Child shifts topic before the recap names the counting or naming step skill or Form.
      no_response: Child stays on the Constellation Star Count recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same enumerate mechanic and the constellation star count frame.
      unexpected: Close Constellation Star Count first, name the practiced counting or naming step, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Constellation Star Count badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `enumerate`, focal attribute `constellation_star_count`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Night-sky card with a small constellation"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Star Map"
    animation_label: "Stars sparkle"
  - widget: character_display
    widget_params:
      description: "First small star group"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Count 1"
    animation_label: "First stars"
  - widget: character_display
    widget_params:
      description: "Second star group in a new shape"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Count 2"
    animation_label: "Pattern shift"
  - widget: character_display
    widget_params:
      description: "Final constellation count"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Final Count"
    animation_label: "Final stars"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Star Counter
    concepts: [Form]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Constellation Star Count

Backend activity definition converted from `concept_constellation_star_count_enumerate`.
