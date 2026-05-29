---
activity_type: activity_career_decision_role_play
activity_set: activity_text_game
source_export_id: concept_career_decision_decide
mechanic: decide
entity_name: career_decision_role_play
category: category_1
display_label: Career Decision Role Play
tier: T1
ib_theme: "How We Organize Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Responsibility]
keywords: [career, firefighter, smoke alarm, role, decision, safety]
feature_keywords: [firefighter, alarm, water hose, safety choice]
photo_features: [firefighter portrait, smoke alarm, water hose, safety picture]
play_rounds: 3
plain_description: "The AI makes the child the firefighter in a smoke-alarm scene, then asks simple safety decisions."
steps_summary:
  - "Become the firefighter."
  - "Decide whether the team should send help."
  - "Choose the water hose instead of cooking oil."
  - "Pick the first safe action and earn the Firefighter Helper badge."
creative_slots:
  game_mechanic: decide
  metaphor: "A pretend fire station board where each safety choice lights up one helper marker."
  role_title: Firefighter Helper
  round_scenarios:
    - "Today you are the firefighter. A smoke alarm is ringing, and your team needs a first decision."
    - "The fire scene needs the right tool: water hose or cooking oil."
    - "The firefighter chooses the first safe action: check that people are outside or run inside alone."
  escalation_axis: "role assignment to tool choice to safety-first responsibility"
  observation_detail: "a firefighter picture, smoke alarm cue, water hose, and safety-choice marker"
step_instructions:
  hook:
    goal: "Open Career Decision Role Play by naming the firefighter mission and the smoke-alarm cue."
    constraint: "T1 max 3 sentences, end with a choice question."
    emotion_tag: curious
  transition:
    goal: "Explain the loop: AI gives one firefighter prompt, the child makes one safety choice, and one marker lights up."
    constraint: "T1 max 3 sentences, include one bounded sample choice. Use career_portrait_cards_01 as supportive art when available; if not, describe the firefighter role by text only and do not claim a person portrait is shown."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Assign the child the firefighter role and ask whether the team should send help for the smoke alarm."
      scenario: "firefighter smoke alarm decision"
      constraint: "T1 max 3 sentences, keep the child inside the firefighter role and offer send help now or check first."
      emotion_tag: encouraging
      acceptable_themes: [firefighter, alarm, help, send, check, safe]
      escalation_note: "become the firefighter and make the first dispatch decision"
    - round_number: 2
      goal: "Ask the firefighter to choose the safe tool for the fire scene: water hose or cooking oil."
      scenario: "firefighter tool decision"
      constraint: "T1 max 3 sentences, name the unsafe tool plainly and return to the two visible choices."
      emotion_tag: curious
      acceptable_themes: [water, hose, firefighter, tool, safe, fire]
      escalation_note: "choose the tool that fits the firefighter job"
    - round_number: 3
      goal: "Ask the firefighter to choose the first safe action: check that people are outside or run inside alone."
      scenario: "firefighter first safe action"
      constraint: "T1 max 3 sentences, validate wanting to help while emphasizing team safety."
      emotion_tag: proud
      acceptable_themes: [safe, outside, check, people, team, firefighter]
      escalation_note: "connect the decision to responsibility"
  celebrate:
    goal: "Award Firefighter Helper and recap the smoke alarm, water hose, and safety-first choices."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Responsibility through the firefighter role, water hose tool, and safe first action."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any firefighter safety choice."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: 'Preserve the sequence: assign the child a profession, place them inside a concrete work scenario, ask a simple expert decision, then respond to the decision. Do not turn this into choosing which profession matches a scenario.'
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `decide`.
  - 'Preserve this source sequence: Preserve the sequence: assign the child a profession, place them inside a concrete work scenario, ask a simple expert decision, then respond to the decision. Do not turn this into choosing which profession matches a scenario.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Career Decision Role Play. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the firefighter role-player role, notices the starter cue, or names something connected to the firefighter alarm decision.
      unexpected: Child asks for another game, starts the choice before the Career Decision Role Play mission is framed, or follows an unrelated topic.
      no_response: Child watches the Career Decision Role Play title prompt without taking the firefighter role-player role yet.
    ai_followups:
      ideal: Name the firefighter role-player role, connect it to the starter cue, and preview the first choice.
      unexpected: Acknowledge the request, return to the Career Decision Role Play promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Career Decision Role Play role and first marker, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress markers.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you make one safety choice, and one marker lights up for each turn.'
    child_responses:
      ideal: The child agrees to the choice loop for Career Decision Role Play or asks for the easiest version.
      unexpected: Child tries to skip the firefighter alarm decision, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Career Decision Role Play rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Career Decision Role Play loop as AI prompt, child choice, saved marker, and show the first response slot.
      unexpected: Keep the rule tied to the firefighter alarm decision, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Career Decision Role Play rule in one sentence and ask for yes or the first chance to make a choice.'
    screen: 'Shows the rule strip, current round marker, and asset/fallback note. Use `career_portrait_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If art is unavailable, describe the helper role by voice and avoid claiming the screen shows a person.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: Assign the profession first and keep the child inside the role.
      example_ai_line: Today you are the firefighter. A smoke alarm is ringing. Should your team send help now?
      child_responses:
        ideal: The child answers as the firefighter and decides whether the team sends help for the alarm.
        unexpected: Child drops the firefighter role, names another job, or talks about alarms without making the dispatch decision.
        no_response: Child stays with the firefighter alarm scene without choosing what the team does.
      ai_followups:
        ideal: Confirm the firefighter decision, name the safety reason, and keep the alarm scenario moving.
        unexpected: Put the child back in the firefighter role, restate the smoke alarm problem, and offer send help now or check first as bounded choices.
        no_response: '[wait 2s] Model "As the firefighter, I send help," then ask for send help or wait/check.'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `career_portrait_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If art is unavailable, describe the helper role by voice and avoid claiming the screen shows a person.'
  - round_number: 2
    source_contract:
      runtime_instruction: Ask for a tool choice inside the same work scenario.
      example_ai_line: 'Firefighter, which tool fits this fire scene: water hose or cooking oil?'
      child_responses:
        ideal: The child chooses the water hose over cooking oil for the fire scene.
        unexpected: Child picks an unsafe tool, leaves the firefighter role, or asks for a tool unrelated to the fire scene.
        no_response: Child looks between the water hose and cooking oil choices without picking a tool.
      ai_followups:
        ideal: Confirm the tool choice, say why it fits a firefighter, and place the tool marker beside the scene.
        unexpected: Keep the child in role, name the unsafe tool plainly, and return to the two visible choices.
        no_response: '[wait 2s] Say "Firefighters use water for fire," then ask for hose or oil.'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `career_portrait_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If art is unavailable, describe the helper role by voice and avoid claiming the screen shows a person.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask what the professional checks before acting.
      example_ai_line: Should the firefighter check that people are safe outside, or run inside alone?
      child_responses:
        ideal: 'The child chooses the safer first action: check that people are outside.'
        unexpected: Child chooses to run inside alone, ignores the safety check, or talks about being brave instead of making the first-action choice.
        no_response: Child is unsure about the safety choice and has not picked outside check or run inside.
      ai_followups:
        ideal: Affirm the safety-first action, show the people-safe marker, and close the firefighter scenario.
        unexpected: 'Validate wanting to help, then restate that firefighters work with teams and ask for the safe first action: check people are safe outside or run inside alone.'
        no_response: '[wait 2s] Model "I check people are safe first," then ask: should the firefighter check people are safe outside, or run inside alone?'
      screen: 'Shows the active round marker, child response slot, and source-intent cue. Use `career_portrait_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If art is unavailable, describe the helper role by voice and avoid claiming the screen shows a person.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the first safe firefighter action changed the Career Decision Role Play board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Career Decision Role Play payoff or ignores how the saved choice turns connect.
      no_response: Child watches the Career Decision Role Play reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's choice turns, name one concrete saved marker, and invite a short reflection.
      unexpected: Hold the Career Decision Role Play reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Career Decision Role Play board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Responsibility. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Career Decision Role Play moment, asks to play again, or watches the career decision recap badge.
      unexpected: Child shifts topic before the recap names the choice skill or Form and Responsibility.
      no_response: Child stays on the Career Decision Role Play recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same decide mechanic and the career decision frame.
      unexpected: Close Career Decision Role Play first, name the practiced choice, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Career Decision Role Play badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `decide`, focal attribute `career_decision`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Firefighter mission picture with smoke alarm and helper markers"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Fire Station"
    animation_label: "Mission picture"
  - widget: character_display
    widget_params:
      description: "Firefighter smoke alarm decision picture"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Alarm"
    animation_label: "Send help"
  - widget: character_display
    widget_params:
      description: "Water hose and cooking oil tool choice picture"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Tool Choice"
    animation_label: "Hose choice"
  - widget: character_display
    widget_params:
      description: "Firefighter safety-first action picture"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Safe First"
    animation_label: "Safety marker"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Firefighter Helper
    concepts: [Form, Responsibility]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Career Decision Role Play

Backend activity definition converted from `concept_career_decision_decide`.
