---
activity_type: activity_travel_planner
activity_set: activity_text_game
source_export_id: concept_travel_planner_predict
mechanic: predict
entity_name: travel_planner
category: category_1
display_label: Travel Planner
tier: T1
ib_theme: "Where We Are In Place And Time"
ib_key_concept: Form
concepts_earned: [Form, Causation]
keywords: [travel, plan, trip, weather, pack]
feature_keywords: [destination, bag, route, prediction]
photo_features: [travel card, route path, packing tokens]
play_rounds: 3
plain_description: "The child plans a pretend trip by choosing what to pack, how to travel, and what might happen."
steps_summary:
  - "Become a Mini Travel Planner."
  - "Choose what to pack, how to travel, and what might happen."
  - "Predict how one choice changes the trip."
  - "Earn the Mini Travel Planner badge."
creative_slots:
  game_mechanic: predict
  metaphor: "A tiny travel desk where each plan choice changes the pretend route."
  role_title: Mini Travel Planner
  round_scenarios:
    - "Choose what to pack for a sunny place."
    - "Choose how to travel or what to do if the weather changes."
    - "Predict what happens after one travel choice."
  escalation_axis: "simple packing to change response to cause-effect prediction"
  observation_detail: "a route card with packing and weather symbols"
step_instructions:
  hook:
    goal: "Open Travel Planner and invite the child to plan a pretend trip."
    constraint: "T1 max 3 sentences, end with a destination or packing question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round makes one plan and predicts what might happen next."
    constraint: "T1 max 3 sentences, include one sample prediction. Use travel_planning_cards_01 when available; if not, use text-only place, weather, vehicle, and habitat prompts."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask what to pack for the first pretend destination."
      scenario: "sunny place packing choice"
      constraint: "T1 max 3 sentences, invite one item and reason."
      emotion_tag: encouraging
      acceptable_themes: [pack, sun, hat, water, bag]
      escalation_note: "simple planning"
    - round_number: 2
      goal: "Ask how to travel or what the traveler should do if weather changes."
      scenario: "weather change plan"
      constraint: "T1 max 3 sentences, connect choice to effect."
      emotion_tag: curious
      acceptable_themes: [rain, coat, change, plan, weather]
      escalation_note: "adaptation"
    - round_number: 3
      goal: "Ask the child to predict what happens after a travel choice."
      scenario: "next travel event prediction"
      constraint: "T1 max 3 sentences, ask for a because reason."
      emotion_tag: proud
      acceptable_themes: [next, because, trip, choose, happen]
      escalation_note: "cause and effect"
  celebrate:
    goal: "Award Mini Travel Planner and recap the plan choices."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Causation through trip details and choice effects."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any travel plan."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The child helps plan a pretend trip by choosing what to pack, how to travel, and what might happen.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `predict`.
  - 'Preserve this source sequence: The child helps plan a pretend trip by choosing what to pack, how to travel, and what might happen.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Travel Planner. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the pretend trip planner role, notices the starter cue, or names something connected to the pack choice.
      unexpected: Child asks for another game, starts the plan or prediction before the Travel Planner mission is framed, or follows an unrelated topic.
      no_response: Child watches the Travel Planner title/trigger card without taking the pretend trip planner role yet.
    ai_followups:
      ideal: Name the pretend trip planner role, connect it to the starter cue, and preview the first plan or prediction.
      unexpected: Acknowledge the request, return to the Travel Planner promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Point to the Travel Planner role card and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the plan or prediction loop for Travel Planner or asks for the easiest version.
      unexpected: Child tries to skip the pack choice, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Travel Planner rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Travel Planner loop as AI prompt, child plan or prediction, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the pack choice, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Travel Planner rule in one sentence and ask for yes, a point, or the first chance to make a plan or prediction.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `travel_planning_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the planning conversation by voice only.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: The child helps plan a pretend trip by choosing what to pack, how to travel, and what might happen. Ask the child to predict or plan in the first small turn.'
      example_ai_line: 'Let us start: The child helps plan a pretend trip by choosing what to pack, how to travel, and what might happen. What is your first try?'
      child_responses:
        ideal: The child makes a plan or prediction for the pack choice and accepts that it can be checked or imagined next.
        unexpected: Child treats the pack choice as a fixed answer, jumps past the check, or proposes a plan outside the pretend setup.
        no_response: Child looks at the pack choice choices without making a prediction or plan.
      ai_followups:
        ideal: Record the prediction, say what would make it true, and show how the next step will check or play it out.
        unexpected: Keep the pretend setup, narrow the pack choice to two possible outcomes, and ask which one might happen.
        no_response: '[wait 2s] Model "I think this will happen because.." for the pack choice, then ask for one guess or choice.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `travel_planning_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the planning conversation by voice only.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second predict turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child makes a plan or prediction for the transport or weather choice and accepts that it can be checked or imagined next.
        unexpected: Child treats the transport or weather choice as a fixed answer, jumps past the check, or proposes a plan outside the pretend setup.
        no_response: Child looks at the transport or weather choice choices without making a prediction or plan.
      ai_followups:
        ideal: Record the prediction, say what would make it true, and show how the next step will check or play it out.
        unexpected: Keep the pretend setup, narrow the transport or weather choice to two possible outcomes, and ask which one might happen.
        no_response: '[wait 2s] Model "I think this will happen because.." for the transport or weather choice, then ask for one guess or choice.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `travel_planning_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the planning conversation by voice only.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child makes a plan or prediction for the what might happen on the trip and accepts that it can be checked or imagined next.
        unexpected: Child treats the what might happen on the trip as a fixed answer, jumps past the check, or proposes a plan outside the pretend setup.
        no_response: Child looks at the what might happen on the trip choices without making a prediction or plan.
      ai_followups:
        ideal: Record the prediction, say what would make it true, and show how the next step will check or play it out.
        unexpected: Keep the pretend setup, narrow the what might happen on the trip to two possible outcomes, and ask which one might happen.
        no_response: '[wait 2s] Model "I think this will happen because.." for the what might happen on the trip, then ask for one guess or choice.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `travel_planning_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, run the planning conversation by voice only.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the what might happen on the trip changed the Travel Planner board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Travel Planner payoff or ignores how the saved plan or prediction turns connect.
      no_response: Child watches the Travel Planner reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's plan or prediction turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Travel Planner reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Travel Planner board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Causation. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Travel Planner moment, asks to play again, or watches the travel planner recap badge.
      unexpected: Child shifts topic before the recap names the plan or prediction skill or Form and Causation.
      no_response: Child stays on the Travel Planner recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same predict mechanic and the travel planner frame.
      unexpected: Close Travel Planner first, name the practiced plan or prediction, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Travel Planner badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `predict`, focal attribute `travel_planner`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Travel route card with bag, weather, and path icons"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Trip Map"
    animation_label: "Route appears"
  - widget: character_display
    widget_params:
      description: "Packing choice for a sunny place"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Pack"
    animation_label: "Bag glow"
  - widget: character_display
    widget_params:
      description: "Weather change plan card"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Weather"
    animation_label: "Weather shift"
  - widget: character_display
    widget_params:
      description: "Next event prediction card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Predict"
    animation_label: "Path glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Mini Travel Planner
    concepts: [Form, Causation]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Travel Planner

Backend activity definition converted from `concept_travel_planner_predict`.
