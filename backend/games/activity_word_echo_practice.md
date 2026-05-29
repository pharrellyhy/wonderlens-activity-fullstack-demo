---
activity_type: activity_word_echo_practice
activity_set: activity_text_game
source_export_id: concept_word_echo_remember
mechanic: remember
entity_name: word_echo_practice
category: category_1
display_label: Word Echo Practice
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [word, echo, repeat, remember, phrase]
feature_keywords: [word card, echo, memory, repeat]
photo_features: [word card, echo token, memory trail]
play_rounds: 3
plain_description: "The AI says a simple word or phrase and the child repeats it back in a playful echo round."
steps_summary:
  - "Become an Echo Player."
  - "Echo three short word or phrase prompts."
  - "Remember the echo pattern."
  - "Earn the Echo Player badge."
creative_slots:
  game_mechanic: remember
  metaphor: "An echo trail where each repeated word lights the next step."
  role_title: Echo Player
  round_scenarios:
    - "Echo one simple word."
    - "Echo a two-word phrase."
    - "Remember and echo a favorite pair."
  escalation_axis: "single word to short phrase to remembered pair"
  observation_detail: "a word card that starts an echo trail"
step_instructions:
  hook:
    goal: "Open Word Echo Practice and invite the child into an echo trail."
    constraint: "T1 max 3 sentences, text-only, end with a readiness question."
    emotion_tag: warm
  transition:
    goal: "Explain that the AI gives a word or phrase and the child types it back."
    constraint: "T1 max 3 sentences, include one tiny demo. Use word_echo_cards_01 when available; if not, use voice-only or text-only echo prompts and do not claim a word card is shown."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Give one simple word to echo."
      scenario: "first echo word"
      constraint: "T1 max 3 sentences, accept close typed repeats."
      emotion_tag: encouraging
      acceptable_themes: [echo, repeat, word, same, remember]
      escalation_note: "single word"
    - round_number: 2
      goal: "Give a short phrase to echo."
      scenario: "echo variation prompt"
      constraint: "T1 max 3 sentences, split the phrase if needed."
      emotion_tag: curious
      acceptable_themes: [phrase, echo, repeat, remember, words]
      escalation_note: "two-word phrase"
    - round_number: 3
      goal: "Ask the child to echo or recall a favorite word pair."
      scenario: "remembered echo pair"
      constraint: "T1 max 3 sentences, support partial recall."
      emotion_tag: proud
      acceptable_themes: [remember, echo, pair, favorite, words]
      escalation_note: "recall closure"
  celebrate:
    goal: "Award Echo Player and recap the echo trail."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Connection through word shapes and repeated links."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any echo attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The AI says a simple word or phrase and the child repeats it back in a playful echo round.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `remember`.
  - 'Preserve this source sequence: The AI says a simple word or phrase and the child repeats it back in a playful echo round.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Word Echo Practice. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the echo player role, notices the starter cue, or names something connected to the first echo word.
      unexpected: Child asks for another game, starts the echo or recall before the Word Echo Practice mission is framed, or follows an unrelated topic.
      no_response: Child watches the Word Echo Practice title/trigger card without taking the echo player role yet.
    ai_followups:
      ideal: Name the echo player role, connect it to the starter cue, and preview the first echo or recall.
      unexpected: Acknowledge the request, return to the Word Echo Practice promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Point to the Word Echo Practice role card and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the echo or recall loop for Word Echo Practice or asks for the easiest version.
      unexpected: Child tries to skip the first echo word, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Word Echo Practice rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Word Echo Practice loop as AI prompt, child echo or recall, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the first echo word, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Word Echo Practice rule in one sentence and ask for yes, a point, or the first chance to echo or recall the prompt.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `word_echo_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the activity voice-only and do not claim the screen is showing a word.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: The AI says a simple word or phrase and the child repeats it back in a playful echo round. Ask the child to echo or recall in the first small turn.'
      example_ai_line: 'Let us start: The AI says a simple word or phrase and the child repeats it back in a playful echo round. What is your first try?'
      child_responses:
        ideal: The child repeats, remembers, or answers the first echo word prompt closely enough to keep the memory loop going.
        unexpected: Child changes the first echo word word/fact, guesses randomly, or turns the echo into unrelated talk.
        no_response: Child listens to the first echo word prompt without echoing, answering, or choosing a smaller repeat.
      ai_followups:
        ideal: Repeat back the remembered part, mark the memory token, and cue the next echo or recall.
        unexpected: Slow the first echo word into smaller pieces, accept a partial recall, and ask for just the next word or sound.
        no_response: '[wait 2s] Say the first echo word prompt in two short beats, then invite the child to copy one beat.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `word_echo_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the activity voice-only and do not claim the screen is showing a word.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second remember turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child repeats, remembers, or answers the echo variation prompt closely enough to keep the memory loop going.
        unexpected: Child changes the echo variation word/fact, guesses randomly, or turns the echo into unrelated talk.
        no_response: Child listens to the echo variation prompt without echoing, answering, or choosing a smaller repeat.
      ai_followups:
        ideal: Repeat back the remembered part, mark the memory token, and cue the next echo or recall.
        unexpected: Slow the echo variation into smaller pieces, accept a partial recall, and ask for just the next word or sound.
        no_response: '[wait 2s] Say the echo variation prompt in two short beats, then invite the child to copy one beat.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `word_echo_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the activity voice-only and do not claim the screen is showing a word.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child repeats, remembers, or answers the remembered echo pair prompt closely enough to keep the memory loop going.
        unexpected: Child changes the remembered echo pair word/fact, guesses randomly, or turns the echo into unrelated talk.
        no_response: Child listens to the remembered echo pair prompt without echoing, answering, or choosing a smaller repeat.
      ai_followups:
        ideal: Repeat back the remembered part, mark the memory token, and cue the next echo or recall.
        unexpected: Slow the remembered echo pair into smaller pieces, accept a partial recall, and ask for just the next word or sound.
        no_response: '[wait 2s] Say the remembered echo pair prompt in two short beats, then invite the child to copy one beat.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `word_echo_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the activity voice-only and do not claim the screen is showing a word.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the remembered echo pair changed the Word Echo Practice board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Word Echo Practice payoff or ignores how the saved echo or recall turns connect.
      no_response: Child watches the Word Echo Practice reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's echo or recall turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Word Echo Practice reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Word Echo Practice board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Connection. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Word Echo Practice moment, asks to play again, or watches the word echo practice recap badge.
      unexpected: Child shifts topic before the recap names the echo or recall skill or Form and Connection.
      no_response: Child stays on the Word Echo Practice recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same remember mechanic and the word echo practice frame.
      unexpected: Close Word Echo Practice first, name the practiced echo or recall, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Word Echo Practice badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `remember`, focal attribute `word_echo_practice`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Word echo card with three empty trail lights"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Echo Trail"
    animation_label: "Trail lights"
  - widget: character_display
    widget_params:
      description: "Single word echo card"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Word"
    animation_label: "First echo"
  - widget: character_display
    widget_params:
      description: "Two-word phrase echo card"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Phrase"
    animation_label: "Phrase echo"
  - widget: character_display
    widget_params:
      description: "Remembered word pair card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Recall"
    animation_label: "Recall glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Echo Player
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Word Echo Practice

Backend activity definition converted from `concept_word_echo_remember`.
