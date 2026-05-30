---
activity_type: activity_partial_reveal_guess
activity_set: activity_text_game
source_export_id: concept_partial_reveal_deduce
mechanic: deduce
entity_name: partial_reveal_guess
category: category_1
display_label: Partial Reveal Guess
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Causation]
keywords: [partial, reveal, clue, guess, object]
feature_keywords: [part, whole, clue, evidence, cat ears, cat paws, cat face]
photo_features: [cat ears clue, cat paws clue, cat face reveal card]
play_rounds: 3
plain_description: "The screen reveals each distinctive part as fixed cat clues: cat ears first, cat paws next, and cat face at the reveal, while the child guesses the whole animal from visible clues."
steps_summary:
  - "Become a Picture Clue Detective."
  - "Make three clue-based guesses as more evidence appears."
  - "Reveal how the clues caused the final answer."
  - "Earn the Picture Clue Detective badge."
creative_slots:
  game_mechanic: deduce
  metaphor: "A mystery lens reveals small clues before the whole picture."
  role_title: Picture Clue Detective
  round_scenarios:
    - "Cat ears peek out from a hidden picture."
    - "Cat paws appear and change or confirm the best guess."
    - "The cat face is nearly revealed for a final answer."
  escalation_axis: "single clue to added evidence to final reveal"
  observation_detail: "cat ears, cat paws, and cat face clues that hint at the whole cat"
step_instructions:
  hook:
    goal: "Open Partial Reveal Guess and invite the child to become a Picture Clue Detective."
    constraint: "T1 max 3 sentences, text-only, end with a question. The hidden answer is cat; do not switch to another animal or object."
    emotion_tag: curious
  transition:
    goal: "Explain that each round uses one clue to make or revise a guess."
    constraint: "T1 max 3 sentences, include one tiny demo guess. Use partial_reveal_cards_01 when available; visible clues are cat ears, cat paws, and cat face. If cards are unavailable, use a voice-only or text-only cat-clue fallback and do not claim a card is shown."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Present cat ears and ask for a maybe-guess."
      scenario: "cat ears clue"
      constraint: "T1 max 3 sentences, ask what the clue could belong to."
      emotion_tag: curious
      acceptable_themes: [guess, clue, maybe, part, evidence]
      escalation_note: "first clue"
    - round_number: 2
      goal: "Add cat paws and ask whether the guess changes."
      scenario: "cat paws clue"
      constraint: "T1 max 3 sentences, connect evidence to the changed guess."
      emotion_tag: surprised
      acceptable_themes: [change, clue, evidence, maybe, guess]
      escalation_note: "guess revision"
    - round_number: 3
      goal: "Invite the final cat guess as the cat face appears."
      scenario: "cat face final guess"
      constraint: "T1 max 3 sentences, ask for a final answer and one reason."
      emotion_tag: proud
      acceptable_themes: [answer, whole, clue, reason, reveal]
      escalation_note: "final deduction"
  celebrate:
    goal: "Reveal the answer and award Picture Clue Detective."
    constraint: "T1 max 3 sentences, recap how clues caused the guess."
    emotion_tag: proud
  closing:
    goal: "Name Form and Causation through visible parts and evidence changing guesses."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and praise clue thinking."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The screen shows fixed cat ears, cat paws, and cat face clues, and the child guesses the whole cat from visible clues.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `deduce`.
  - 'Preserve this source sequence: cat ears clue, cat paws clue, cat face reveal. Do not switch to another hidden animal or object.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Partial Reveal Guess. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the picture clue detective role, notices the starter cue, or names something connected to the first visible clue.
      unexpected: Child asks for another game, starts the clue guess before the Partial Reveal Guess mission is framed, or follows an unrelated topic.
      no_response: Child watches the Partial Reveal Guess opening moment without taking the picture clue detective role yet.
    ai_followups:
      ideal: Name the picture clue detective role, connect it to the starter cue, and preview the first clue guess.
      unexpected: Acknowledge the request, return to the Partial Reveal Guess promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the picture clue detective role and the first clue, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I share a clue, you make one guess, and we light up one step of the mystery for each turn.'
    child_responses:
      ideal: The child agrees to the clue guess loop for Partial Reveal Guess or asks for the easiest version.
      unexpected: Child tries to skip the first visible clue, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Partial Reveal Guess rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Partial Reveal Guess loop as a clue from me, a guess from you, one mystery step lit up, and show the first response slot.
      unexpected: Keep the rule tied to the first visible clue, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Partial Reveal Guess rule in one sentence and ask for a yes or the first chance to make a clue-based guess.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `partial_reveal_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If partial cards are unavailable, switch to a voice-only partial-clue riddle and do not claim the screen is showing a picture.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the asset promise: the first visible clue is cat ears. Ask for a maybe-guess from the ears, and do not reveal or switch to another answer.'
      example_ai_line: 'First clue: cat ears are peeking out. What could this hidden animal be?'
      child_responses:
        ideal: The child uses the first visible clue to make or revise a plausible guess.
        unexpected: Child guesses without using the first visible clue, asks for the answer, or follows a detail that is not evidence yet.
        no_response: Child studies the first visible clue clue area without offering a maybe-guess.
      ai_followups:
        ideal: Tie the guess to the visible clue, reveal whether that clue fits, and set up the next evidence step.
        unexpected: Name the clue in the first visible clue, separate it from one distracting detail, and ask for one maybe-guess.
        no_response: '[wait 2s] Name one visible clue from the first visible clue, model a "maybe it is" guess, and invite a copy or new guess.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `partial_reveal_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If partial cards are unavailable, switch to a voice-only partial-clue riddle and do not claim the screen is showing a picture.'
  - round_number: 2
    source_contract:
      runtime_instruction: 'Keep the asset promise: the second visible clue is cat paws. Ask whether the cat guess changes or gets stronger.'
      example_ai_line: 'Now we can see cat paws too. Does that change your guess, or make cat feel stronger?'
      child_responses:
        ideal: The child uses the second revealed clue to make or revise a plausible guess.
        unexpected: Child guesses without using the second revealed clue, asks for the answer, or follows a detail that is not evidence yet.
        no_response: Child studies the second revealed clue clue area without offering a maybe-guess.
      ai_followups:
        ideal: Tie the guess to the visible clue, reveal whether that clue fits, and set up the next evidence step.
        unexpected: Name the clue in the second revealed clue, separate it from one distracting detail, and ask for one maybe-guess.
        no_response: '[wait 2s] Name one visible clue from the second revealed clue, model a "maybe it is" guess, and invite a copy or new guess.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `partial_reveal_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If partial cards are unavailable, switch to a voice-only partial-clue riddle and do not claim the screen is showing a picture.'
  - round_number: 3
    source_contract:
      runtime_instruction: 'Keep the asset promise: the final reveal shows a cat face. Ask for the final cat answer and one clue reason.'
      example_ai_line: 'The cat face is almost revealed. What is your final answer, and which clue helped most?'
      child_responses:
        ideal: The child uses the final whole-object guess to make or revise a plausible guess.
        unexpected: Child guesses without using the final whole-object guess, asks for the answer, or follows a detail that is not evidence yet.
        no_response: Child studies the final whole-object guess clue area without offering a maybe-guess.
      ai_followups:
        ideal: Tie the guess to the visible clue, reveal whether that clue fits, and set up the next evidence step.
        unexpected: Name the clue in the final whole-object guess, separate it from one distracting detail, and ask for one maybe-guess.
        no_response: '[wait 2s] Name one visible clue from the final whole-object guess, model a "maybe it is" guess, and invite a copy or new guess.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `partial_reveal_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If partial cards are unavailable, switch to a voice-only partial-clue riddle and do not claim the screen is showing a picture.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the final whole-object guess changed the Partial Reveal Guess board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Partial Reveal Guess payoff or ignores how the saved clue guess turns connect.
      no_response: Child watches the Partial Reveal Guess reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's clue guess turns, name one concrete saved turn, and invite a short reflection.
      unexpected: Hold the Partial Reveal Guess reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Partial Reveal Guess board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Causation. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Partial Reveal Guess moment, asks to play again, or watches the partial reveal guess recap badge.
      unexpected: Child shifts topic before the recap names the clue guess skill or Form and Causation.
      no_response: Child stays on the Partial Reveal Guess recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same deduce mechanic and the partial reveal guess frame.
      unexpected: Close Partial Reveal Guess first, name the practiced clue guess, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Partial Reveal Guess badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `deduce`, focal attribute `partial_reveal_guess`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "A mystery card with one partial clue visible"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Mystery Clue"
    animation_label: "Clue appears"
  - widget: character_display
    widget_params:
      description: "First partial clue on a hidden picture"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Clue 1"
    animation_label: "First clue"
  - widget: character_display
    widget_params:
      description: "Second clue added beside the first"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Clue 2"
    animation_label: "More evidence"
  - widget: character_display
    widget_params:
      description: "Final reveal card ready for a whole-object guess"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Final Guess"
    animation_label: "Reveal glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Picture Clue Detective
    concepts: [Form, Causation]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Partial Reveal Guess

Backend activity definition converted from `concept_partial_reveal_deduce`.
