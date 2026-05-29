---
activity_type: activity_emotion_reader
activity_set: activity_text_game
source_export_id: concept_emotion_reader_care
mechanic: care
entity_name: emotion_reader
category: category_1
display_label: Emotion Reader
tier: T1
ib_theme: "Who We Are"
ib_key_concept: Form
concepts_earned: [Form, Responsibility]
keywords: [emotion, feeling, face, body, help]
feature_keywords: [expression, feeling, cue, caring]
photo_features: [face card, body cue, feeling token]
play_rounds: 3
plain_description: "The child notices an obvious expression or body cue and thinks about what feeling or help might fit."
steps_summary:
  - "Become a Feeling Helper."
  - "Read three simple feeling cues."
  - "Choose kind responses that fit."
  - "Earn the Feeling Helper badge."
creative_slots:
  game_mechanic: care
  metaphor: "A caring station where visible cues help the child choose kind actions."
  role_title: Feeling Helper
  round_scenarios:
    - "A character shows one obvious feeling cue."
    - "A second cue changes what help might fit."
    - "The child chooses a kind response for the feeling."
  escalation_axis: "notice cue to infer feeling to choose help"
  observation_detail: "a visible face or body cue"
step_instructions:
  hook:
    goal: "Open Emotion Reader and invite the child to notice a feeling cue."
    constraint: "T1 max 3 sentences, nonjudgmental, end with a question."
    emotion_tag: gentle
  transition:
    goal: "Explain that each round notices a cue, names a feeling, and chooses kind help."
    constraint: "T1 max 3 sentences, include one caring demo. Use emotion_expression_cards_01 when available; if not, use a story-description fallback and do not claim expression cards are shown."
    emotion_tag: warm
  rounds:
    - round_number: 1
      goal: "Ask what feeling might match one visible cue."
      scenario: "visible face or body cue"
      constraint: "T1 max 3 sentences, offer two feeling choices if useful."
      emotion_tag: curious
      acceptable_themes: [happy, sad, scared, tired, feeling]
      escalation_note: "name a feeling"
    - round_number: 2
      goal: "Ask what help could fit a second feeling cue."
      scenario: "possible feeling cue"
      constraint: "T1 max 3 sentences, keep help gentle and realistic."
      emotion_tag: warm
      acceptable_themes: [help, kind, ask, hug, rest]
      escalation_note: "connect cue to need"
    - round_number: 3
      goal: "Ask the child to choose a kind response."
      scenario: "kind help choice"
      constraint: "T1 max 3 sentences, praise caring reasoning."
      emotion_tag: proud
      acceptable_themes: [care, help, feeling, kind, responsible]
      escalation_note: "responsible action"
  celebrate:
    goal: "Award Feeling Helper and recap the kind choices."
    constraint: "T1 max 3 sentences, do not judge emotions as right or wrong."
    emotion_tag: proud
  closing:
    goal: "Name Form and Responsibility through visible cues and caring choices."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate noticing feelings."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: The child notices an obvious expression or body cue and thinks about what feeling or help might fit.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `care`.
  - 'Preserve this source sequence: The child notices an obvious expression or body cue and thinks about what feeling or help might fit.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Emotion Reader. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the feeling helper role, notices the starter cue, or names something connected to the visible face or body cue.
      unexpected: Child asks for another game, starts the kind response before the Emotion Reader mission is framed, or follows an unrelated topic.
      no_response: Child watches the Emotion Reader title/trigger card without taking the feeling helper role yet.
    ai_followups:
      ideal: Name the feeling helper role, connect it to the starter cue, and preview the first kind response.
      unexpected: Acknowledge the request, return to the Emotion Reader promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Point to the Emotion Reader role card and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the kind response loop for Emotion Reader or asks for the easiest version.
      unexpected: Child tries to skip the visible face or body cue, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Emotion Reader rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Emotion Reader loop as AI prompt, child kind response, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the visible face or body cue, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Emotion Reader rule in one sentence and ask for yes, a point, or the first chance to choose a kind response.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `emotion_expression_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a story description of a character''s visible cues and avoid claiming the screen shows a face.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: The child notices an obvious expression or body cue and thinks about what feeling or help might fit. Ask the child to notice a need and help in the first small turn.'
      example_ai_line: 'Let us start: The child notices an obvious expression or body cue and thinks about what feeling or help might fit. What is your first try?'
      child_responses:
        ideal: The child notices the visible face or body cue cue and suggests a fitting feeling, need, or kind action.
        unexpected: Child judges the person/object, ignores the visible face or body cue cue, or offers help that does not fit the need.
        no_response: Child watches the visible face or body cue cue without naming a feeling, need, or helpful action.
      ai_followups:
        ideal: Connect the cue to the caring choice, save the kindness token, and show the calmer or helped state.
        unexpected: Reframe without judging, point to the cue for the visible face or body cue, and offer two gentle help choices.
        no_response: '[wait 2s] Model one caring sentence for the visible face or body cue, then ask the child to choose a feeling or help action.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `emotion_expression_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a story description of a character''s visible cues and avoid claiming the screen shows a face.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second care turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child notices the possible feeling cue and suggests a fitting feeling, need, or kind action.
        unexpected: Child judges the person/object, ignores the possible feeling cue, or offers help that does not fit the need.
        no_response: Child watches the possible feeling cue without naming a feeling, need, or helpful action.
      ai_followups:
        ideal: Connect the cue to the caring choice, save the kindness token, and show the calmer or helped state.
        unexpected: Reframe without judging, point to the cue for the possible feeling, and offer two gentle help choices.
        no_response: '[wait 2s] Model one caring sentence for the possible feeling, then ask the child to choose a feeling or help action.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `emotion_expression_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a story description of a character''s visible cues and avoid claiming the screen shows a face.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child notices the kind help choice cue and suggests a fitting feeling, need, or kind action.
        unexpected: Child judges the person/object, ignores the kind help choice cue, or offers help that does not fit the need.
        no_response: Child watches the kind help choice cue without naming a feeling, need, or helpful action.
      ai_followups:
        ideal: Connect the cue to the caring choice, save the kindness token, and show the calmer or helped state.
        unexpected: Reframe without judging, point to the cue for the kind help choice, and offer two gentle help choices.
        no_response: '[wait 2s] Model one caring sentence for the kind help choice, then ask the child to choose a feeling or help action.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `emotion_expression_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If cards are unavailable, use a story description of a character''s visible cues and avoid claiming the screen shows a face.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the kind help choice changed the Emotion Reader board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Emotion Reader payoff or ignores how the saved kind response turns connect.
      no_response: Child watches the Emotion Reader reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's kind response turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Emotion Reader reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Emotion Reader board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Responsibility. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Emotion Reader moment, asks to play again, or watches the emotion reader recap badge.
      unexpected: Child shifts topic before the recap names the kind response skill or Form and Responsibility.
      no_response: Child stays on the Emotion Reader recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same care mechanic and the emotion reader frame.
      unexpected: Close Emotion Reader first, name the practiced kind response, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Emotion Reader badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `care`, focal attribute `emotion_reader`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Feeling card with one clear expression cue"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Feeling Cue"
    animation_label: "Cue glow"
  - widget: character_display
    widget_params:
      description: "First expression or body cue"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Notice"
    animation_label: "Cue pulse"
  - widget: character_display
    widget_params:
      description: "Second feeling cue with help choices"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Feeling"
    animation_label: "Help choices"
  - widget: character_display
    widget_params:
      description: "Kind response card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Help"
    animation_label: "Kind glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Feeling Helper
    concepts: [Form, Responsibility]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Emotion Reader

Backend activity definition converted from `concept_emotion_reader_care`.
