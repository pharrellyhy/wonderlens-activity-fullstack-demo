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
keywords: [career, job, role, decision, helper]
feature_keywords: [profession, tool, choice, responsibility]
photo_features: [career portrait, job tool, decision card]
play_rounds: 3
plain_description: "The AI assigns a profession role and the child makes simple expert decisions for pretend situations."
steps_summary:
  - "Become a Helpful Expert."
  - "Make three role-based decisions."
  - "Explain what the expert should do next."
  - "Earn the Helpful Expert badge."
creative_slots:
  game_mechanic: decide
  metaphor: "A pretend work desk where each job role needs one helpful decision."
  role_title: Helpful Expert
  round_scenarios:
    - "A doctor chooses what a patient needs first."
    - "A builder chooses the safest tool for a job."
    - "A teacher chooses how to help a friend learn."
  escalation_axis: "simple role choice to responsibility-based decision"
  observation_detail: "a career portrait or tool that shows what the role does"
step_instructions:
  hook:
    goal: "Open Career Decision Role Play and invite the child into a helper role."
    constraint: "T1 max 3 sentences, end with a choice question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round gives a pretend job moment and asks for one expert decision."
    constraint: "T1 max 3 sentences, include one sample choice."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child what the doctor helper should do first."
      scenario: "doctor helper decision"
      constraint: "T1 max 3 sentences, keep the situation pretend and simple."
      emotion_tag: encouraging
      acceptable_themes: [doctor, help, check, rest, choose]
      escalation_note: "familiar care decision"
    - round_number: 2
      goal: "Ask the child to choose a safe builder tool or action."
      scenario: "builder tool decision"
      constraint: "T1 max 3 sentences, emphasize safe pretend choice."
      emotion_tag: curious
      acceptable_themes: [builder, tool, safe, fix, choose]
      escalation_note: "tool and function"
    - round_number: 3
      goal: "Ask the child how a teacher helper should support a learner."
      scenario: "teacher help decision"
      constraint: "T1 max 3 sentences, connect choice to responsibility."
      emotion_tag: proud
      acceptable_themes: [teacher, help, explain, kind, choose]
      escalation_note: "social responsibility"
  celebrate:
    goal: "Award Helpful Expert and recap the role decisions."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Responsibility through job tools, roles, and helpful choices."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any helpful decision."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Career role cards on a helper desk"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Helper Desk"
    animation_label: "Role cards"
  - widget: character_display
    widget_params:
      description: "Doctor role decision card"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Doctor"
    animation_label: "Choice glow"
  - widget: character_display
    widget_params:
      description: "Builder role decision card"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Builder"
    animation_label: "Tool choice"
  - widget: character_display
    widget_params:
      description: "Teacher role decision card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Teacher"
    animation_label: "Help choice"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Helpful Expert
    concepts: [Form, Responsibility]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Career Decision Role Play

Backend activity definition converted from `concept_career_decision_decide`.
