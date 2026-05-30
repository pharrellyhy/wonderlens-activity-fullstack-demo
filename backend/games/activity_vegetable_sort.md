---
activity_type: activity_vegetable_sort
activity_set: activity_text_game
source_export_id: concept_vegetable_sort_sort
mechanic: sort
entity_name: vegetable_sort
category: category_1
display_label: Vegetable Sort
tier: T1
ib_theme: "How We Organize Ourselves"
ib_key_concept: Form
concepts_earned: [Form]
keywords: [vegetable, sort, group, color, shape]
feature_keywords: [vegetable, category, form, rule]
photo_features: [vegetable cards, basket groups, sort rule]
play_rounds: 3
plain_description: "The child sorts vegetable cards or photographed vegetables by a visible or meaningful rule such as color, shape, edible part, or cooking use."
steps_summary:
  - "Become a Veggie Sorter."
  - "Sort vegetable cards or photographed vegetables by clear rules."
  - "Explain the sorting rule."
  - "Earn the Veggie Sorter badge."
creative_slots:
  game_mechanic: sort
  metaphor: "A little market table where vegetables jump into matching baskets."
  role_title: Veggie Sorter
  round_scenarios:
    - "Sort vegetables by color."
    - "Sort vegetables by shape or edible part."
    - "Choose a cooking use or child-chosen basket rule and explain it."
  escalation_axis: "visible color to shape or edible part to cooking use or child-chosen rule"
  observation_detail: "vegetable cards with clear colors and shapes"
step_instructions:
  hook:
    goal: "Open Vegetable Sort and invite the child to organize veggie cards."
    constraint: "T1 max 3 sentences, end with a sorting question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round sorts by one rule and the child types the group or rule."
    constraint: "T1 max 3 sentences, include one sample basket. Use vegetable_sort_cards_01 when available; if not, use photographed vegetables or a text-only prompt and do not claim cards are shown."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask which vegetables belong together by color."
      scenario: "color basket sort"
      constraint: "T1 max 3 sentences, invite a short typed answer."
      emotion_tag: encouraging
      acceptable_themes: [color, green, red, yellow, basket]
      escalation_note: "color sort"
    - round_number: 2
      goal: "Ask which vegetables belong together by shape or edible part."
      scenario: "shape or edible part basket sort"
      constraint: "T1 max 3 sentences, ask for one reason."
      emotion_tag: curious
      acceptable_themes: [shape, long, round, root, leaf, edible]
      escalation_note: "form comparison"
    - round_number: 3
      goal: "Ask the child to choose a cooking use or basket rule and name it."
      scenario: "cooking use or child-chosen basket rule"
      constraint: "T1 max 3 sentences, accept plausible rules."
      emotion_tag: proud
      acceptable_themes: [sort, rule, basket, group, same, cook, cooking]
      escalation_note: "child-created rule"
  celebrate:
    goal: "Award Veggie Sorter and recap the sorting rules."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form through visible vegetable features and groups."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any sorting idea."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The child sorts vegetable cards or photographed vegetables by a visible or meaningful rule.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `sort`.
  - 'Preserve this source sequence: The child sorts vegetable cards or photographed vegetables by a visible or meaningful rule.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Vegetable Sort. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the vegetable sorter role, notices the starter cue, or names something connected to the first vegetable group.
      unexpected: Child asks for another game, starts the sorting move before the Vegetable Sort mission is framed, or follows an unrelated topic.
      no_response: Child watches the Vegetable Sort opening moment without taking the vegetable sorter role yet.
    ai_followups:
      ideal: Name the vegetable sorter role, connect it to the starter cue, and preview the first sorting move.
      unexpected: Acknowledge the request, return to the Vegetable Sort promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Vegetable Sort role and the first vegetable group, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save your idea for each turn.'
    child_responses:
      ideal: The child agrees to the sorting move loop for Vegetable Sort or asks for the easiest version.
      unexpected: Child tries to skip the first vegetable group, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Vegetable Sort rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Vegetable Sort loop as AI prompt, child sorting move, saved idea, and show the first response slot.
      unexpected: Keep the rule tied to the first vegetable group, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Vegetable Sort rule in one sentence and ask for a yes or the first chance to place one item by the rule.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `vegetable_sort_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use photographed vegetables or a voice-only sorting prompt and do not claim cards are shown.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: the child sorts the vegetables by a visible or meaningful rule. Invite the child to group or organize the vegetables in the first small turn.'
      example_ai_line: 'Let us start by sorting these vegetables by a rule we can see. Which ones would you like to group together first?'
      child_responses:
        ideal: The child places or names an item according to the first vegetable group rule.
        unexpected: Child mixes rules for the first vegetable group, sorts by an invisible reason, or moves items without naming a grouping idea.
        no_response: Child looks at the items for the first vegetable group without placing or naming one group.
      ai_followups:
        ideal: Name the grouping rule the child used, keep that group visible, and ask for the next item or rule check.
        unexpected: Hold the current groups still, compare two possible rules, and ask which one controls the first vegetable group.
        no_response: '[wait 2s] Model placing one item by the first vegetable group rule, then ask the child to place or name one more.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `vegetable_sort_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use photographed vegetables or a voice-only sorting prompt and do not claim cards are shown.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second sort turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child places or names an item according to the new sorting rule rule.
        unexpected: Child mixes rules for the new sorting rule, sorts by an invisible reason, or moves items without naming a grouping idea.
        no_response: Child looks at the items for the new sorting rule without placing or naming one group.
      ai_followups:
        ideal: Name the grouping rule the child used, keep that group visible, and ask for the next item or rule check.
        unexpected: Hold the current groups still, compare two possible rules, and ask which one controls the new sorting rule.
        no_response: '[wait 2s] Model placing one item by the new sorting rule rule, then ask the child to place or name one more.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `vegetable_sort_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use photographed vegetables or a voice-only sorting prompt and do not claim cards are shown.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child places or names an item according to the final sorting rule explanation rule.
        unexpected: Child mixes rules for the final sorting rule explanation, sorts by an invisible reason, or moves items without naming a grouping idea.
        no_response: Child looks at the items for the final sorting rule explanation without placing or naming one group.
      ai_followups:
        ideal: Name the grouping rule the child used, keep that group visible, and ask for the next item or rule check.
        unexpected: Hold the current groups still, compare two possible rules, and ask which one controls the final sorting rule explanation.
        no_response: '[wait 2s] Model placing one item by the final sorting rule explanation rule, then ask the child to place or name one more.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `vegetable_sort_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use photographed vegetables or a voice-only sorting prompt and do not claim cards are shown.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the final sorting rule explanation changed the Vegetable Sort board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Vegetable Sort payoff or ignores how the saved sorting move turns connect.
      no_response: Child watches the Vegetable Sort reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's sorting move turns, name one concrete saved idea, and invite a short reflection.
      unexpected: Hold the Vegetable Sort reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Vegetable Sort board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Vegetable Sort moment, asks to play again, or watches the vegetable sort recap badge.
      unexpected: Child shifts topic before the recap names the sorting move skill or Form.
      no_response: Child stays on the Vegetable Sort recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same sort mechanic and the vegetable sort frame.
      unexpected: Close Vegetable Sort first, name the practiced sorting move, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Vegetable Sort badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `sort`, focal attribute `vegetable_sort`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Market table with vegetable cards and empty baskets"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Veggie Table"
    animation_label: "Basket glow"
  - widget: character_display
    widget_params:
      description: "Vegetables sorted by color"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Color"
    animation_label: "Color sort"
  - widget: character_display
    widget_params:
      description: "Vegetables sorted by shape or edible part"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Shape"
    animation_label: "Shape sort"
  - widget: character_display
    widget_params:
      description: "Child chooses a cooking use or basket rule"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Rule"
    animation_label: "Rule glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Veggie Sorter
    concepts: [Form]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Vegetable Sort

Backend activity definition converted from `concept_vegetable_sort_sort`.
