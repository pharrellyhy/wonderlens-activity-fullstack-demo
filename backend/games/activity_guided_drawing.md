---
activity_type: activity_guided_drawing
activity_set: activity_text_game
source_export_id: concept_guided_drawing_probe
mechanic: build
entity_name: guided_drawing
category: category_3
display_label: Guided Drawing
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Change]
keywords: [guided drawing, drawing, pencil, paper, build, create]
feature_keywords: [line, shape, detail, drawing]
photo_features: [paper, pencil, simple lines, visible shape]
play_rounds: 3
plain_description: "The AI guides the child to use paper and pencil to complete a simple drawing step by step."
steps_summary:
  - "Set up paper and pencil for a guided drawing."
  - "Add a first line or shape, then report what changed."
  - "Add a second detail and a final finishing choice."
  - "Earn the Guided Artist badge."

creative_slots:
  game_mechanic: build
  metaphor: "The child becomes a Guided Artist who grows a drawing one small step at a time."
  role_title: Guided Artist
  build_materials: [paper, pencil]
  build_steps:
    - "Draw one simple line or shape to start the picture."
    - "Add one small detail that changes what the picture could become."
    - "Choose one finishing mark and describe the finished drawing."
  escalation_axis: "single mark to changed drawing to finished recap"
  observation_detail: "a first line or shape that can change into a drawing"

step_instructions:
  hook:
    goal: "Open Guided Drawing, name the child as a Guided Artist, and invite them to make one small drawing step."
    constraint: "T1 max 3 sentences, text-only, do not claim to see the paper, end with an invitation."
    emotion_tag: curious
  transition:
    goal: "Explain the loop: I give a small drawing step, the child tries it, then types what they did."
    constraint: "T1 max 3 sentences, mention paper and pencil, do not ask for a photo, end by asking if they are ready. Use guided_drawing_step_cards_01 when available; if not, use text-only step descriptions. Require caregiver or child self-report and no-assessment language."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to draw one simple line or shape and type what they added."
      scenario: "first line or shape"
      constraint: "T1 max 3 sentences, one small action, no visual assessment."
      emotion_tag: encouraging
      acceptable_themes: [line, circle, square, mark, shape, start]
      escalation_note: "easy first mark"
    - round_number: 2
      goal: "Ask the child to add one detail that changes what the drawing could become."
      scenario: "second guided detail"
      constraint: "T1 max 3 sentences, connect the detail to change, ask for a typed report."
      emotion_tag: curious
      acceptable_themes: [detail, eyes, legs, roof, leaf, change]
      escalation_note: "adds meaning or transformation"
    - round_number: 3
      goal: "Ask the child to add one finishing mark and describe the finished drawing."
      scenario: "finished drawing recap"
      constraint: "T1 max 3 sentences, recap sequence, ask for a short description."
      emotion_tag: proud
      acceptable_themes: [finished, done, drawing, picture, made, changed]
      escalation_note: "closure and reflection"
  celebrate:
    goal: "Award the Guided Artist title and recap the reported drawing sequence."
    constraint: "T1 max 3 sentences, reference reported steps, no visual inspection claims."
    emotion_tag: proud
  closing:
    goal: "Name Form and Change, connecting them to how small marks changed the drawing."
    constraint: "T1 max 3 sentences, warm goodbye, suggest a next guided drawing."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any drawing effort the child reported."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle

source_dialogue:
  source_intent_lock: The AI guides the child to use paper and pencil to complete a simple drawing step by step.
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `build`.
  - 'Preserve this source sequence: The AI guides the child to use paper and pencil to complete a simple drawing step by step.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Guided Drawing. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the guided artist role, notices the starter cue, or names something connected to the first line or shape.
      unexpected: Child asks for another game, starts the making step before the Guided Drawing mission is framed, or follows an unrelated topic.
      no_response: Child watches the Guided Drawing title/trigger card without taking the guided artist role yet.
    ai_followups:
      ideal: Name the guided artist role, connect it to the starter cue, and preview the first making step.
      unexpected: Acknowledge the request, return to the Guided Drawing promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Point to the Guided Drawing role card and first token, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Rule: I prompt, you try the activity action, and we save one token for each turn.'
    child_responses:
      ideal: The child agrees to the making step loop for Guided Drawing or asks for the easiest version.
      unexpected: Child tries to skip the first line or shape, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Guided Drawing rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Guided Drawing loop as AI prompt, child making step, saved token, and show the first response slot.
      unexpected: Keep the rule tied to the first line or shape, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Read the Guided Drawing rule in one sentence and ask for yes, a point, or the first chance to add one making step.'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `guided_drawing_step_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If step cards are unavailable, use voice-only step descriptions; the Cat3 material workflow still requires product approval before package generation.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: 'Preserve the workbook promise: The AI guides the child to use paper and pencil to complete a simple drawing step by step. Ask the child to create or assemble in the first small turn.'
      example_ai_line: 'Let us start: The AI guides the child to use paper and pencil to complete a simple drawing step by step. What is your first try?'
      child_responses:
        ideal: The child adds the requested first line or shape piece, mark, word, or construction step.
        unexpected: Child skips the first line or shape step, changes the target, or asks the AI to complete the making for them.
        no_response: Child looks at the first line or shape prompt without adding a mark, piece, word, or choice.
      ai_followups:
        ideal: Name what the child added, show how it changes the creation, and cue the next build step.
        unexpected: Keep the target small, restate the one required first line or shape step, and offer an easier mark, word, or piece.
        no_response: '[wait 2s] Model the smallest possible first line or shape addition, then invite the child to copy or choose one part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `guided_drawing_step_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If step cards are unavailable, use voice-only step descriptions; the Cat3 material workflow still requires product approval before package generation.'
  - round_number: 2
    source_contract:
      runtime_instruction: Keep the same source frame and ask for a second build turn with a small variation.
      example_ai_line: Now try one more turn in the same game. What changes this time?
      child_responses:
        ideal: The child adds the requested second guided detail piece, mark, word, or construction step.
        unexpected: Child skips the second guided detail step, changes the target, or asks the AI to complete the making for them.
        no_response: Child looks at the second guided detail prompt without adding a mark, piece, word, or choice.
      ai_followups:
        ideal: Name what the child added, show how it changes the creation, and cue the next build step.
        unexpected: Keep the target small, restate the one required second guided detail step, and offer an easier mark, word, or piece.
        no_response: '[wait 2s] Model the smallest possible second guided detail addition, then invite the child to copy or choose one part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `guided_drawing_step_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If step cards are unavailable, use voice-only step descriptions; the Cat3 material workflow still requires product approval before package generation.'
  - round_number: 3
    source_contract:
      runtime_instruction: Ask the child to recap, show, choose, or explain the result so the source action has closure.
      example_ai_line: What did we make, find, choose, or learn from your turns?
      child_responses:
        ideal: The child adds the requested finished drawing recap piece, mark, word, or construction step.
        unexpected: Child skips the finished drawing recap step, changes the target, or asks the AI to complete the making for them.
        no_response: Child looks at the finished drawing recap prompt without adding a mark, piece, word, or choice.
      ai_followups:
        ideal: Name what the child added, show how it changes the creation, and cue the next build step.
        unexpected: Keep the target small, restate the one required finished drawing recap step, and offer an easier mark, word, or piece.
        no_response: '[wait 2s] Model the smallest possible finished drawing recap addition, then invite the child to copy or choose one part.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `guided_drawing_step_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If step cards are unavailable, use voice-only step descriptions; the Cat3 material workflow still requires product approval before package generation.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the finished drawing recap changed the Guided Drawing board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Guided Drawing payoff or ignores how the saved making step turns connect.
      no_response: Child watches the Guided Drawing reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's making step turns, name one concrete saved token, and invite a short reflection.
      unexpected: Hold the Guided Drawing reveal, point to the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Guided Drawing board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Change. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Guided Drawing moment, asks to play again, or watches the guided drawing recap badge.
      unexpected: Child shifts topic before the recap names the making step skill or Form and Change.
      no_response: Child stays on the Guided Drawing recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same build mechanic and the guided drawing frame.
      unexpected: Close Guided Drawing first, name the practiced making step, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Guided Drawing badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `build`, focal attribute `guided_drawing`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Guided drawing setup with paper and pencil"
      entity: guided_drawing
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Guided Drawing"
    animation_label: "Ready to draw"
  - widget: character_display
    widget_params:
      description: "A first line or simple shape begins the drawing"
      entity: guided_drawing
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Round 1: First Mark"
    animation_label: "First mark"
  - widget: character_display
    widget_params:
      description: "A small detail changes what the drawing could become"
      entity: guided_drawing
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Round 2: Change It"
    animation_label: "Drawing changes"
  - widget: character_display
    widget_params:
      description: "A finishing mark completes the guided drawing"
      entity: guided_drawing
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Round 3: Finish"
    animation_label: "Finished drawing"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Guided Artist
    concepts: [Form, Change]
    entity: guided_drawing
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Guided Drawing

Backend activity definition converted from `concept_guided_drawing_probe`.
