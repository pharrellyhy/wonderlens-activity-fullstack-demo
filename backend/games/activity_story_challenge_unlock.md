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
keywords: [story, challenge, unlock, imagine, gate]
feature_keywords: [story gate, choice, character, unlock]
photo_features: [story path, locked gates, character card]
play_rounds: 3
plain_description: "The child moves through a short story by solving simple imagination challenges that unlock the next scene."
steps_summary:
  - "Become a Story Gate Opener."
  - "Solve three imagination gates in sequence."
  - "Choose how the character moves forward."
  - "Earn the Story Gate Opener badge."
creative_slots:
  game_mechanic: imagine
  metaphor: "A story path with tiny gates that open when the child adds an idea."
  role_title: Story Gate Opener
  round_scenarios:
    - "Unlock the first gate by naming a friendly character."
    - "Unlock the second gate by choosing what the character sees."
    - "Unlock the final gate by deciding how the character helps."
  escalation_axis: "character idea to scene detail to helpful perspective"
  observation_detail: "a locked story gate waiting for one imagination key"
step_instructions:
  hook:
    goal: "Open Story Challenge Unlock and invite the child to unlock a tiny story."
    constraint: "T1 max 3 sentences, end with an imagination question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round needs one typed idea to open the next story gate."
    constraint: "T1 max 3 sentences, include one sample key idea."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to name or choose the story character."
      scenario: "first story gate character"
      constraint: "T1 max 3 sentences, accept any safe character idea."
      emotion_tag: encouraging
      acceptable_themes: [character, friend, name, story, gate]
      escalation_note: "character setup"
    - round_number: 2
      goal: "Ask what the character sees after the gate opens."
      scenario: "second story gate scene detail"
      constraint: "T1 max 3 sentences, invite one visible detail."
      emotion_tag: curious
      acceptable_themes: [see, place, tree, door, path]
      escalation_note: "scene detail"
    - round_number: 3
      goal: "Ask how the character helps or solves the final challenge."
      scenario: "final story gate helpful choice"
      constraint: "T1 max 3 sentences, connect the idea to perspective."
      emotion_tag: proud
      acceptable_themes: [help, choose, solve, friend, open]
      escalation_note: "perspective choice"
  celebrate:
    goal: "Award Story Gate Opener and recap the unlocked story path."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through story details and character choices."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and save the story idea for next time."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Story path with three small locked gates"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Story Path"
    animation_label: "Gate glow"
  - widget: character_display
    widget_params:
      description: "First gate opens for a character idea"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Gate 1"
    animation_label: "First unlock"
  - widget: character_display
    widget_params:
      description: "Second gate opens to reveal a scene detail"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Gate 2"
    animation_label: "Scene unlock"
  - widget: character_display
    widget_params:
      description: "Final gate opens after a helpful choice"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Gate 3"
    animation_label: "Final unlock"
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
