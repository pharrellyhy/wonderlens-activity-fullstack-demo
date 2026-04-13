---
# =============================================================================
# CAT1 (In-Device Verbal) game template
# =============================================================================
# Fill every <ANGLE_BRACKET> placeholder and delete comments you don't need.
# Cat1 games are verbal roleplay activities where the child never leaves the
# device — they watch the entity photo on screen and speak/act out responses
# to scenarios the AI narrates.
#
# Before you start:
# 1. Pick a `game_mechanic` from the list at backend/schemas/creative_slots.py
#    (Cat1CreativeSlots.game_mechanic Literal). Each mechanic has a matching
#    step-instruction file at
#    backend/skills/step_instructions/cat1_step{2,3}__<mechanic>.md
# 2. Decide the tier (T0=2-4, T1=4-6, T2=6-8). Tier controls sentence limits
#    and scenario complexity — see backend/tier_rules.yaml.
# 3. Save this file as `backend/games/<activity_type>.md` where
#    <activity_type> matches the `activity_type` field below.
# =============================================================================

activity_type: <snake_case_id>              # e.g. mood_changer_dog — must be
                                            # unique and match the filename
entity_name: <entity>                       # e.g. dog, cat, dinosaur
category: category_1                        # ALWAYS category_1 for Cat1
display_label: <Human Label>                # e.g. "Stuffed Dog" — shown in UI
tier: <T0|T1|T2>                            # complexity tier
ib_theme: "<IB Theme>"                      # one of the 6 PYP themes
ib_key_concept: <Key Concept>               # main concept earned
concepts_earned: [<Key Concept>]            # list (usually just the key one)
keywords: [<kw1>, <kw2>]                    # vision-tag hints for photo match
feature_keywords: [<kw1>, <kw2>]            # secondary vision hints
photo_features: [<feat1>, <feat2>]          # traits the AI can reference
play_rounds: 3                              # usually 3 for Cat1
plain_description: "<one-sentence summary of what the child does>"
steps_summary:
  - "<step 1 summary>"
  - "<step 2 summary>"
  - "<step 3 summary — ending in badge>"

creative_slots:
  game_mechanic: <mechanic_id>              # voice_acting | mood_guessing |
                                            # true_or_silly | storytelling_chain |
                                            # riddle_game | sound_imitation |
                                            # prediction_game | helper_hotline
  metaphor: "<playful imaginative frame for the entity>"
  role_title: <Title Awarded>               # e.g. "Emotion Translator"
  round_scenarios:                          # 8 scenarios total (3 core + 5 extra)
    - <scenario 1 — easiest, most comfortable>
    - <scenario 2 — unexpected twist>
    - <scenario 3 — peak excitement>
    - <scenario 4>
    - <scenario 5>
    - <scenario 6>
    - <scenario 7>
    - <scenario 8>
  escalation_axis: <from X to Y>            # e.g. "comfortable to excited"
  observation_detail: "<specific visual detail the AI anchors hook to>"

step_instructions:
  hook:
    goal: "<what the AI should notice + the emotional/imaginative question to ask>"
    constraint: "<tier sentence limit>, <hook type>, <must end with question>"
    emotion_tag: <excited|warm|playful|curious|gentle|surprised|proud>
  transition:
    goal: "<introduce the mechanic + one demo round with answer shown>"
    constraint: "<tier sentence limit>, demo round WITH answer included, end with invitation"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "<vivid scene-setting + ask what the entity says/feels/does>"
      scenario: "<one-line trigger description>"
      constraint: "<tier sentence limit>, sensory details, end with a question"
      emotion_tag: <tag>
      acceptable_themes: [<theme1>, <theme2>, <theme3>]
      escalation_note: "<what makes this round feel its level of intensity>"
    - round_number: 2
      goal: "<...>"
      scenario: "<...>"
      constraint: "<...>"
      emotion_tag: <tag>
      acceptable_themes: [<themes>]
      escalation_note: "<...>"
    - round_number: 3
      goal: "<...>"
      scenario: "<...>"
      constraint: "<...>"
      emotion_tag: <tag>
      acceptable_themes: [<themes>]
      escalation_note: "<...>"
    # Add 5 more rounds (4-8) as alternates so the Director can pick per session.
    # Keep the same structure.
  celebrate:
    goal: "<award the role_title ceremonially + recap specific moments from the game>"
    constraint: "<tier sentence limit>, announce title, reference specific rounds"
    emotion_tag: proud
  closing:
    goal: "<teach the IB key concept naturally, connect to what they just experienced, plant curiosity seed>"
    constraint: "<tier sentence limit>, name the concept naturally, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: "<gentle goodbye that validates whatever they did>"
    constraint: "<tier sentence limit>, no pressure"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "<photo composition description>"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "<Short Label>"
    animation_label: "Sparkle highlight"
  - widget: character_display
    widget_params:
      description: "<scene illustration for round 1>"
    animation: gentle_pulse
    trigger: on_round_1
    sfx_cue: scene_woosh
    widget_label: "Round 1: <Label>"
    animation_label: "Gentle glow"
  - widget: character_display
    widget_params:
      description: "<scene illustration for round 2>"
    animation: scene_transition
    trigger: on_round_2
    sfx_cue: scene_woosh
    widget_label: "Round 2: <Label>"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "<scene illustration for round 3>"
    animation: gentle_pulse
    trigger: on_round_3
    sfx_cue: celebration_fanfare
    widget_label: "Round 3: <Label>"
    animation_label: "Gentle glow"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "<Role Title>"
    concepts: [<Key Concept>]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## <Activity Title>

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | <Activity Title> |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | <T0 (ages 2–4) / T1 (ages 4–6) / T2 (ages 6–8)> |
| Core IB Key Concepts | <Key Concept> |
| Related Concepts | <related concept list> |
| ATL Skills Focus | <Communication/Thinking/Self-Management/Research/Social — which and why> |
| Game Style | <game_mechanic> |

### B. Activity Overview

**① Brief Description**: <2-3 sentence overview of the child's experience — what the AI does, what the child becomes (role title), the emotional/learning arc.>

**② Educational Purpose (KUD)**:
- **K (Know)**: <concrete observable facts the child learns about the entity or concept>
- **U (Understand)**: <the conceptual "so what" — how this ties to the IB key concept>
- **D (Do)**: <what skills/behaviors the child practices>

**③ Design Highlight**: <what makes this activity's design special — the metaphor, the escalation, the kind of imagination it invites>

**④ Typical Scenario**: <one-sentence description of the prototypical play session>

### C. Interaction Flow

> Recommended Tier: <tier>

#### Step 1: Transition Bridge

**AI says:** <hook line referencing observation_detail, ending in an emotional question>

**Child responses:**

1. (Ideal) "<expected happy response>"
2. (Unexpected) "<plausible off-script response>"
3. (No response) Child watches silently.

**AI follow-up:**

1. <warm validation of ideal response>
2. <graceful pivot from unexpected response>
3. <gentle re-invitation after 2s wait>

**Screen:** <description of the photo/widget state for this step>

#### Step 2: Rule Introduction + Demo

**AI says:** <explain the game + one full demo round with the answer shown + invitation>

**Child responses:**

1. (Ideal) "<yes/ready response>"
2. (Unexpected) "<tangent>"
3. (No response) Quiet pause.

**AI follow-up:**

1. <celebrate readiness, kick off round 1>
2. <honor the tangent, bridge back to round 1>
3. <gentle encouragement, kick off round 1>

**Screen:** <entity photo + mechanic visual hint>

#### Step 3: Multi-Round Interaction

**Round 1 — "<Label>":**

**AI says:** <vivid scene-setting for round 1 scenario, ending in the mechanic question>

**Child responses:**

1. (Ideal) "<expected themed response>"
2. (Unexpected) "<off-topic or emotional tangent>"
3. (No response) Quiet.

**AI follow-up:**

1. <celebrate the ideal>
2. <graceful acceptance of tangent>
3. <helpful binary choice hint>

**Screen:** <round 1 illustration>

**Round 2 — "<Label>":** <same structure as Round 1>

**Round 3 — "<Label>":** <same structure as Round 1>

#### Step 4: Celebration

**AI says:** <award role_title with ceremony, recap specific moments>

**Child responses:**

1. (Ideal) "<yay response>"
2. (Unexpected) "<attachment to entity>"

**AI follow-up:**

1. <amplify the pride>
2. <honor the attachment>

**Screen:** <badge animation description>

#### Step 5: Closing + IB Concepts

**AI says:** <teach the IB concept naturally, link to specific moments, warm goodbye>

**Child responses:**

1. (Ideal) "<concept echoed or acknowledged>"
2. (Unexpected) "<goodbye or repeat-play request>"

**AI follow-up:**

1. <celebrate the concept connection>
2. <warm send-off + tease next time>

**Screen:** <badge + IB concept lockup>
