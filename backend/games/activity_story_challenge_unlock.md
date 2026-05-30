---
activity_type: activity_story_challenge_unlock
activity_set: activity_text_game
source_export_id: concept_story_unlock_probe
mechanic: imagine
entity_name: story_challenge_unlock
category: category_1
display_label: Story Challenge Unlock
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Perspective]
keywords: [story, challenge, unlock, fox, moon door, owl, bonjour]
feature_keywords: [moon door, owl bridge, star word, color challenge]
photo_features: [fox story path, moon door, sleepy owl bridge, star word page]
play_rounds: 3
plain_description: "A fox unlocks story gates with a moon-door color, a quiet owl sound, and the word bonjour."
steps_summary:
  - "Become a Story Gate Opener."
  - "Open the moon door with silver, white, or blue."
  - "Wake the owl bridge with a quiet hoo-hoo."
  - "Echo bonjour for the star page."
  - "Earn the Story Gate Opener badge."
creative_slots:
  game_mechanic: imagine
  metaphor: "A fox story path with three tiny locks: moon color, owl sound, and star word."
  role_title: Story Gate Opener
  round_scenarios:
    - "The fox reaches a moon door that opens with silver, white, or blue."
    - "The fox finds a sleepy owl bridge that wakes with a quiet hoo-hoo."
    - "The fox reaches a star page that asks for the echo word bonjour."
  escalation_axis: "color unlock to quiet sound unlock to word echo unlock"
  observation_detail: "moon door colors, a sleepy owl bridge, and a glowing star word page"
step_instructions:
  hook:
    goal: "Open Story Challenge Unlock with the fox, the locked story path, and the first moon-door cue."
    constraint: "T1 max 3 sentences, end with an imagination question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round needs one tiny response to unlock the fox's next story gate."
    constraint: "T1 max 3 sentences, name color, sound, and word as the three kinds of keys. Use story_unlock_cards_01 when available; if not, use voice-only story choices and do not claim a screen element unlocked."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Tell the fox-at-the-moon-door beat and ask for silver, white, or blue to open it."
      scenario: "unlock the moon door"
      constraint: "T1 max 3 sentences, keep the allowed color choices clear and accept named or shown colors."
      emotion_tag: encouraging
      acceptable_themes: [silver, white, blue, moon, door, color]
      escalation_note: "first unlock uses a moon-door color challenge"
    - round_number: 2
      goal: "Continue to the sleepy owl bridge and ask for a quiet hoo-hoo or gentle hello."
      scenario: "wake the owl bridge"
      constraint: "T1 max 3 sentences, keep the owl sound soft and offer hoo-hoo or hello owl."
      emotion_tag: curious
      acceptable_themes: [owl, hoo, quiet, hello, bridge, soft]
      escalation_note: "second unlock uses a gentle animal sound"
    - round_number: 3
      goal: "Continue to the star page and ask the child to echo bonjour."
      scenario: "echo the star word"
      constraint: "T1 max 3 sentences, say bonjour slowly and accept a small echo attempt."
      emotion_tag: proud
      acceptable_themes: [bonjour, bon, jour, echo, star, word]
      escalation_note: "final unlock uses a word echo"
  celebrate:
    goal: "Award Story Gate Opener and recap the moon color, owl sound, and bonjour word tokens."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through the fox story gates and the child's three unlock responses."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and save the fox's current story gate for next time."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
source_dialogue:
  source_intent_lock: 'Preserve the sequence: story beat, paused gate, small child challenge such as finding a color, making an animal sound, or echoing a word, then unlocked next story beat. Do not generate standalone challenges without story narration.'
  runtime_detail_floor_notes:
  - Use `Runtime AI instruction` plus `Example AI line` so runtime can adapt wording while preserving intent.
  - Do not claim unsupported sensing, recoloring, pose detection, cleanup verification, OCR, or hidden state.
  - Keep the repeated child action aligned to `imagine`.
  - 'Preserve this source sequence: Preserve the sequence: story beat, paused gate, small child challenge such as finding a color, making an animal sound, or echoing a word, then unlocked next story beat. Do not generate standalone challenges without story narration.'
  hook:
    runtime_instruction: Open from the source trigger and name the child's role in this activity.
    example_ai_line: 'I found a small mission for us: Story Challenge Unlock. I will guide one step at a time.'
    child_responses:
      ideal: The child accepts the story gate unlocker role, notices the starter cue, or names something connected to the moon door color challenge.
      unexpected: Child asks for another game, starts the story unlock response before the Story Challenge Unlock mission is framed, or follows an unrelated topic.
      no_response: Child watches the Story Challenge Unlock opening moment without taking the story gate unlocker role yet.
    ai_followups:
      ideal: Name the story gate unlocker role, connect it to the starter cue, and preview the first story unlock response.
      unexpected: Acknowledge the request, return to the Story Challenge Unlock promise, and offer the smallest supported first action.
      no_response: '[wait 2s] Name the Story Challenge Unlock role and the first moment, then model one tiny in-frame response.'
    screen: Shows title, child role, source trigger, and empty progress tokens.
  transition:
    runtime_instruction: Explain the rule as an action loop and name any required asset or honest fallback.
    example_ai_line: 'Here is how it goes: I share a story moment, you give one little answer, and a gate opens each turn.'
    child_responses:
      ideal: The child agrees to the story unlock response loop for Story Challenge Unlock or asks for the easiest version.
      unexpected: Child tries to skip the moon door color challenge, ignore the required rule/asset, or count a different kind of response.
      no_response: Child looks at the Story Challenge Unlock rule strip without confirming how to start the first turn.
    ai_followups:
      ideal: Restate the Story Challenge Unlock loop as a story moment, the child's little answer, an opened gate, and invite the first response.
      unexpected: Keep the rule tied to the moon door color challenge, name the supported fallback, and offer one allowed first turn.
      no_response: '[wait 2s] Say the Story Challenge Unlock idea in one sentence and ask, would you like to give the first little answer?'
    screen: 'Shows the rule strip, current round token, and asset/fallback chip. Use `story_unlock_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If unlock UI is unavailable, use voice-only story choices and do not claim a screen element has unlocked.'
  rounds:
  - round_number: 1
    source_contract:
      runtime_instruction: Tell the story beat before the task, then pause for a color challenge.
      example_ai_line: The fox reaches a moon door. Can you name or show silver, white, or blue so it opens?
      child_responses:
        ideal: The child names or shows silver, white, or blue for the moon door.
        unexpected: Child answers before the moon-door story pause, gives an unrelated color/object, or tries to open the door without the color challenge.
        no_response: Child watches the locked moon door without naming or showing a moon-color item.
      ai_followups:
        ideal: Open the moon door, narrate the fox stepping through, and keep the color saved.
        unexpected: Return to the moon-door cliffhanger, repeat the allowed colors, and ask for one named or shown color.
        no_response: '[wait 2s] Name the moon door colors, model "blue opens it," and invite the child to say or show one color.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `story_unlock_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If unlock UI is unavailable, use voice-only story choices and do not claim a screen element has unlocked.'
  - round_number: 2
    source_contract:
      runtime_instruction: Continue the story, then pause for a soft animal sound challenge.
      example_ai_line: The fox finds a sleepy owl bridge. Can you make a quiet hoo-hoo?
      child_responses:
        ideal: The child makes a soft owl sound or says a gentle hello to wake the bridge.
        unexpected: Child shouts, switches animals, or talks about the bridge without trying the owl sound challenge.
        no_response: Child stays at the sleepy owl bridge without making a sound or greeting.
      ai_followups:
        ideal: Wake the owl bridge softly, narrate the fox crossing, and keep the sound saved.
        unexpected: Keep the sleepy-owl scene, lower the volume target, and offer "hoo-hoo" or "hello owl" as the two safe responses.
        no_response: '[wait 2s] Make one quiet "hoo-hoo" example, then ask the child to copy it or whisper hello.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `story_unlock_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If unlock UI is unavailable, use voice-only story choices and do not claim a screen element has unlocked.'
  - round_number: 3
    source_contract:
      runtime_instruction: Continue to the final gate, then ask for one echo word.
      example_ai_line: A star page asks for bonjour. Can you echo bonjour?
      child_responses:
        ideal: The child echoes "bonjour" or tries a close pronunciation for the star page.
        unexpected: Child answers with a different word, asks to skip the word gate, or treats the page as a quiz answer instead of an echo.
        no_response: Child looks at the star-word page without repeating the word.
      ai_followups:
        ideal: Let the star page glow, repeat the echoed word once in the story, and keep the word saved.
        unexpected: Stay in the final gate scene, say the target word again slowly, and accept a tiny echo attempt.
        no_response: '[wait 2s] Say "bon-jour" in two beats and invite the child to copy just one beat if needed.'
      screen: 'Shows the active round token, child response slot, and source-intent cue. Use `story_unlock_cards_01` in `center_card_area` during prod.step_2; prod.step_3.round_1-3; fallback: If unlock UI is unavailable, use voice-only story choices and do not claim a screen element has unlocked.'
  celebrate:
    runtime_instruction: Reveal the outcome caused by the child's saved turns and recap concrete choices.
    example_ai_line: 'Your turns made the board light up: first we started, then we tried, then we finished the mission.'
    child_responses:
      ideal: The child notices how the star-word echo challenge changed the Story Challenge Unlock board or names a favorite saved turn.
      unexpected: Child asks to restart before seeing the Story Challenge Unlock payoff or ignores how the saved story unlock response turns connect.
      no_response: Child watches the Story Challenge Unlock reveal without commenting on the saved turns.
    ai_followups:
      ideal: Tie the reveal to the child's story unlock response turns, name one concrete saved moment, and invite a short reflection.
      unexpected: Hold the Story Challenge Unlock reveal, name the saved turn that matters, and ask what changed because of it.
      no_response: '[wait 2s] Narrate one before/after change from the Story Challenge Unlock board, then offer two favorite-turn choices.'
    screen: Shows a final board with saved turns, asset/fallback note when relevant, and source-specific payoff.
  closing:
    runtime_instruction: Close with the two key concepts and one parent-reviewable recap.
    example_ai_line: Today you practiced Form and Perspective. You used your own answer to move the activity forward.
    child_responses:
      ideal: The child names a favorite Story Challenge Unlock moment, asks to play again, or watches the story challenge unlock recap badge.
      unexpected: Child shifts topic before the recap names the story unlock response skill or Form and Perspective.
      no_response: Child stays on the Story Challenge Unlock recap badge without responding.
    ai_followups:
      ideal: Offer a next-time variation using the same imagine mechanic and the story challenge unlock frame.
      unexpected: Close Story Challenge Unlock first, name the practiced story unlock response, and then offer one next-round seed.
      no_response: '[wait 2s] Read the Story Challenge Unlock badge in one sentence and end with one concrete next-time invitation.'
    screen: Recap badge lists title, mechanic `imagine`, focal attribute `story_challenge_unlock`, and next-step hint.
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Fox story path with moon door, owl bridge, and star word locks"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Fox Path"
    animation_label: "Gate glow"
  - widget: character_display
    widget_params:
      description: "Moon door opens with silver, white, or blue"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Moon Door"
    animation_label: "Color unlock"
  - widget: character_display
    widget_params:
      description: "Sleepy owl bridge wakes with a quiet hoo-hoo"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Owl Bridge"
    animation_label: "Sound unlock"
  - widget: character_display
    widget_params:
      description: "Star page glows after the child echoes bonjour"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Star Word"
    animation_label: "Word unlock"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Story Gate Opener
    concepts: [Form, Perspective]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Story Challenge Unlock

Backend activity definition converted from `concept_story_unlock_probe`.
