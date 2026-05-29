---
activity_type: activity_recognition_pop_challenge
activity_set: activity_text_game
source_export_id: concept_recognition_pop_probe
mechanic: compare
entity_name: recognition_pop_challenge
category: category_1
display_label: Recognition Pop Challenge
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Perspective]
keywords: [recognition, match, compare, picture, pop]
feature_keywords: [target, match, different, same, red apple, blue car, strawberry, cherries, basketball]
photo_features: [red apple target, blue car distractor, strawberry distractor, cherries distractor, basketball distractor]
play_rounds: 3
plain_description: "The child quickly types or names the picture that matches a red apple target from fixed changing sets with blue car, strawberry, cherries, and basketball distractors."
steps_summary:
  - "Become a Match Spotter."
  - "Compare three changing target sets by typing a choice."
  - "Explain what looked the same or different."
  - "Earn the Match Spotter badge."
creative_slots:
  game_mechanic: compare
  metaphor: "A pop board where target pictures appear and the child types the best match."
  role_title: Match Spotter
  round_scenarios:
    - "Match the red apple target against a red apple choice and a blue car distractor."
    - "Compare the red apple target with strawberry and cherries distractors."
    - "Match the red apple target against a red apple choice and a basketball distractor."
  escalation_axis: "obvious match to close comparison to reasoned match"
  observation_detail: "a red apple target beside fixed changing choices"
step_instructions:
  hook:
    goal: "Open Recognition Pop Challenge and invite the child to spot matching forms."
    constraint: "T1 max 3 sentences, end with a typed match question. The target is a red apple; do not introduce animals or unrelated choices. Do not ask the child to point, tap, or click."
    emotion_tag: curious
  transition:
    goal: "Explain that each round shows a target and asks which choice matches best."
    constraint: "T1 max 3 sentences, include one simple same-or-different example. Use recognition_challenge_cards_01 as supportive art when available; the visible target is a red apple and the choices are fixed to red apple, blue car, strawberry, cherries, and basketball across rounds. Do not ask the child to point, tap, or click."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to type which choice matches the red apple target against a blue car distractor."
      scenario: "red apple target with blue car distractor"
      constraint: "T1 max 3 sentences, accept typed labels or descriptions. Do not ask the child to point, tap, or click."
      emotion_tag: encouraging
      acceptable_themes: [same, match, target, picture, choice]
      escalation_note: "obvious match"
    - round_number: 2
      goal: "Ask the child to compare the red apple target with strawberry and cherries and type the best match or closest choice."
      scenario: "red apple target with strawberry and cherries"
      constraint: "T1 max 3 sentences, ask what is same or different. Do not ask the child to point, tap, or click."
      emotion_tag: curious
      acceptable_themes: [same, different, compare, match, close]
      escalation_note: "similar distractor"
    - round_number: 3
      goal: "Ask the child to type the final red apple match and one reason against a basketball distractor."
      scenario: "red apple target with basketball distractor"
      constraint: "T1 max 3 sentences, connect reason to visible form. Do not ask the child to point, tap, or click."
      emotion_tag: proud
      acceptable_themes: [reason, form, same, match, target]
      escalation_note: "reasoned comparison"
  celebrate:
    goal: "Award Match Spotter and recap the comparison clues."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through matching, comparing, and noticing."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any matching attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The child quickly chooses matching target pictures from a fixed red apple sequence with blue car, strawberry, cherries, and basketball distractors.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `compare`.
  - 'Preserve this source sequence: red apple target; blue car distractor in round 1; strawberry and cherries distractors in round 2; basketball distractor in round 3. Do not introduce animal cards.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Recognition Pop Challenge. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the quick match spotter role, notices the starter cue, or names something connected to the first target picture.
      unexpected: Child asks for another game, starts the comparison choice before the Recognition Pop Challenge mission is framed, or follows an unrelated topic.
      no_response: Child watches the Recognition Pop Challenge title and start cue without taking the quick match spotter role yet.
    ai_followups:
      ideal: Name the quick match spotter role, connect it to the starter cue, and preview the first comparison choice.
      unexpected: Acknowledge the request, return to the Recognition Pop Challenge promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Recognition Pop Challenge role badge and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the comparison choice loop for Recognition Pop Challenge or asks for the easiest version.
      unexpected: Child tries to skip the first target picture, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Recognition Pop Challenge rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Recognition Pop Challenge loop as AI prompt, child comparison choice, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the first target picture, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Recognition Pop Challenge rule in one sentence and ask for yes or one word about the visible options.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `recognition_challenge_cards_01` in `center_display_area` during prod.step_2; prod.step_3.round_1-3; fallback: If tap UI or state timing is unavailable, block at Phase 0 rather than converting to dialogue.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the asset promise: the target is a red apple and the first distractor is a blue car. Ask the child to type the matching red apple choice.'
      example_ai_line: 'The target is a red apple. Which choice matches it: red apple or blue car?'
      child_responses:
        ideal: The child compares the visible options for the first target picture and chooses or explains one.
        unexpected: Child responds to only one side of the first target picture, changes the comparison rule, or talks about an option that is not visible.
        no_response: Child looks between the first target picture options without choosing, pointing, or naming a difference.
      ai_followups:
        ideal: Name the comparison evidence, save the selected option, and keep the next comparison state clear.
        unexpected: Restate the two visible options and the comparison lens for the first target picture, then ask for the matching picture name or a short description.
        no_response: '[wait 2s] Name one difference in the first target picture, model a choice, and invite one word or short description.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `recognition_challenge_cards_01` in `center_display_area` during prod.step_2; prod.step_3.round_1-3; fallback: If tap UI or state timing is unavailable, block at Phase 0 rather than converting to dialogue.'
  - round_number: 2
    source_contract:
      runtime_instruction: 'Keep the asset promise: the target remains a red apple and the close distractors are strawberry and cherries. Ask for a typed comparison, not a tap or point.'
      example_ai_line: 'Now compare red apple with strawberry and cherries. Which one is the best match, and what looks different?'
      child_responses:
        ideal: The child compares the visible options for the new target among distractors and chooses or explains one.
        unexpected: Child responds to only one side of the new target among distractors, changes the comparison rule, or talks about an option that is not visible.
        no_response: Child looks between the new target among distractors options without choosing, pointing, or naming a difference.
      ai_followups:
        ideal: Name the comparison evidence, save the selected option, and keep the next comparison state clear.
        unexpected: Restate the two visible options and the comparison lens for the new target among distractors, then ask for the matching picture name or a short description.
        no_response: '[wait 2s] Name one difference in the new target among distractors, model a choice, and invite one word or short description.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `recognition_challenge_cards_01` in `center_display_area` during prod.step_2; prod.step_3.round_1-3; fallback: If tap UI or state timing is unavailable, block at Phase 0 rather than converting to dialogue.'
  - round_number: 3
    source_contract:
      runtime_instruction: 'Keep the asset promise: the target is a red apple and the final distractor is basketball. Ask for the red apple match plus one form clue.'
      example_ai_line: 'Last pop: red apple or basketball. Which matches the target, and what clue helped?'
      child_responses:
        ideal: The child compares the visible options for the final match rule and chooses or explains one.
        unexpected: Child responds to only one side of the final match rule, changes the comparison rule, or talks about an option that is not visible.
        no_response: Child looks between the final match rule options without choosing, pointing, or naming a difference.
      ai_followups:
        ideal: Name the comparison evidence, save the selected option, and keep the next comparison state clear.
        unexpected: Restate the two visible options and the comparison lens for the final match rule, then ask for the matching picture name or a short description.
        no_response: '[wait 2s] Name one difference in the final match rule, model a choice, and invite one word or short description.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `recognition_challenge_cards_01` in `center_display_area` during prod.step_2; prod.step_3.round_1-3; fallback: If tap UI or state timing is unavailable, block at Phase 0 rather than converting to dialogue.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the final match rule changed the Recognition Pop Challenge board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Recognition Pop Challenge payoff or ignores how the saved comparison choice turns connect.
      no_response: Child watches the Recognition Pop Challenge reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's comparison choice turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Recognition Pop Challenge reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Recognition Pop Challenge board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Perspective. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Recognition Pop Challenge moment, asks to play again, or watches the whack a mole recognition recap badge.
      unexpected: Child shifts topic before the recap names the comparison choice skill or Form and Perspective.
      no_response: Child stays on the Recognition Pop Challenge recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same compare mechanic and the whack a mole recognition frame.
      unexpected: Close Recognition Pop Challenge first, name the practiced comparison choice, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Recognition Pop Challenge badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `compare`, focal attribute `whack_a_mole_recognition`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Pop board with a target picture and match slots"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Pop Board"
    animation_label: "Target appears"
  - widget: character_display
    widget_params:
      description: "First target and matching choice"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Match 1"
    animation_label: "First pop"
  - widget: character_display
    widget_params:
      description: "Two similar choices beside the target"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Compare"
    animation_label: "Choices pop"
  - widget: character_display
    widget_params:
      description: "Final target match with reason prompt"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Reason"
    animation_label: "Final pop"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Match Spotter
    concepts: [Form, Perspective]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Recognition Pop Challenge

Backend activity definition converted from `concept_recognition_pop_probe`.
