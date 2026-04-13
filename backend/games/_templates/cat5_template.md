---
# =============================================================================
# CAT5 (Out-of-Device Collection) game template
# =============================================================================
# Fill every <ANGLE_BRACKET> placeholder and delete comments you don't need.
# Cat5 games send the child out of the device to physically find 3 items that
# match a collection criterion, then return for a synthesis reveal.
#
# Before you start:
# 1. Pick an `observation_angle` from the list at
#    backend/schemas/creative_slots.py (Cat5CreativeSlots.observation_angle).
#    This drives what the child pays attention to on each find.
# 2. Pick a `synthesis_format` from an existing file in
#    backend/synthesis_formats/*.md (strip the .md):
#      - collaborative_story  → 3-scene story with named characters
#      - comparison_reveal    → 1-scene side-by-side comparison of items
#      - sorting_challenge    → 1-scene sorted lineup of items
#    Typing an unknown id will fail at session start with a clear error.
# 3. Decide the tier (T0=2-4, T1=4-6, T2=6-8).
# 4. Save this file as `backend/games/<activity_type>.md` where
#    <activity_type> matches the `activity_type` field below.
# =============================================================================

activity_type: <snake_case_id>              # e.g. polka_dot_patrol — must be
                                            # unique and match the filename
entity_name: <entity>                       # e.g. ladybug, dandelion
category: category_5                        # ALWAYS category_5 for Cat5
display_label: <Human Label>                # e.g. "Ladybug" — shown in UI
tier: <T0|T1|T2>                            # complexity tier
ib_theme: "<IB Theme>"                      # one of the 6 PYP themes
ib_key_concept: <Key Concept>               # main concept earned
concepts_earned: [<Key Concept>, <Second>]  # Cat5 often earns 2 concepts
keywords: [<kw1>, <kw2>]                    # vision-tag hints for photo match
feature_keywords: [<kw1>, <kw2>]            # secondary vision hints
photo_features: [<feat1>, <feat2>]          # traits the AI can reference
plain_description: "<one-sentence summary of what the child does>"
steps_summary:
  - "<step 1 summary — discovery>"
  - "<step 2 summary — describe/name each find>"
  - "<step 3 summary — synthesis reveal>"
  - "<step 4 summary — ending in badge>"

creative_slots:
  observation_angle: <color|shape|texture|size|pattern|function|habitat|form|movement|smell>
  collection_criterion: "<specific rule for what to find — a sentence fragment>"
  collection_count: 3                       # usually 3 (T0=2, T1=3, T2=3-4)
  mission_metaphor: "<playful framing of the search — You are a X!>"
  role_title: <Title Awarded>               # e.g. "Polka-Dot Patrol Officer"
  # Legacy field — ignored by the refactored synthesis loop but still required
  # by the pydantic schema for older games. Set to a sensible default.
  synthesis_type: <naming_story|comparison_chart|creative_narrative|sorting_game>
  stuck_hint: "<gentle hint for where to look if the child is stuck>"
  naming_prompt: "<prompt for naming/describing each find>"
  detail_question_template: "<question asked each round to harvest the detail>"
  sorting_criterion: ""                     # only used by sorting_challenge games

story_scaffold:
  premise: "<1-sentence narrative conceit tying all finds together>"
  harvest_per_round: <character_talent|comparison_observation|sound_label|...>
  harvest_question_strategy: >
    R1: <how to ask the first round — usually direct>
    R2: <how to vary round 2 — often comparing to R1>
    R3: <how to vary round 3 — often a wider framing>
  synthesis_goal: "<what the synthesis step should accomplish>"
  synthesis_format: <collaborative_story|comparison_reveal|sorting_challenge>
  story_themes:                             # optional — only used by collaborative_story
    - "<theme seed 1 — child can pick this at synthesis>"
    - "<theme seed 2>"

collection_catalog:                         # items the child can photograph
  correct:                                  # 4+ correct items (child picks 3)
    - id: <item_id_1>
      label: <Item Label 1>
      image: /icons/<item_id_1>.png
    - id: <item_id_2>
      label: <Item Label 2>
      image: /icons/<item_id_2>.png
    - id: <item_id_3>
      label: <Item Label 3>
      image: /icons/<item_id_3>.png
    - id: <item_id_4>
      label: <Item Label 4>
      image: /icons/<item_id_4>.png
  distractors:                              # 6-8 items that don't match
    - id: <distractor_1>
      label: <Distractor Label>
      image: /icons/<distractor_1>.png
    # ... add 5-7 more distractors ...

step_instructions:
  hook:
    goal: "<notice the entity + observation_angle, ask an imaginative question about it>"
    constraint: "<tier sentence limit>, end with an imaginative question"
    emotion_tag: excited
  transition:
    goal: "<build on child's response to introduce the mission — use metaphor, frame as invitation>"
    constraint: "<tier sentence limit>, frame as invitation, end with Would you like to be the X?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "<spark curiosity for first find, suggest WHERE to look, ask for name/description>"
      scenario: "first collection find — <hint>"
      constraint: "<tier sentence limit>, invitational phrasing"
      emotion_tag: encouraging
      acceptable_themes: [<theme1>, <theme2>]
      escalation_note: "easy first find"
    - round_number: 2
      goal: "<celebrate previous find, prompt comparison, suggest new location>"
      scenario: "second collection find — <hint>"
      constraint: "<tier sentence limit>, encourage comparison"
      emotion_tag: curious
      acceptable_themes: [<themes>]
      escalation_note: "moderate — requires more looking"
    - round_number: 3
      goal: "<build excitement for the final find, remind they still need to find it>"
      scenario: "third collection find"
      constraint: "<tier sentence limit>, prompt child to go find it"
      emotion_tag: excited
      acceptable_themes: [<themes>]
      escalation_note: "peak energy — final find"
  celebrate:
    goal: "<award the role_title with ceremony, recap the specific discoveries>"
    constraint: "<tier sentence limit>, announce title, reference specific finds"
    emotion_tag: proud
  closing:
    goal: "<teach the IB concepts they experienced, plant curiosity seed>"
    constraint: "<tier sentence limit>, name concepts naturally, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: "<describe what the synthesis step should feel like — usually the creative reveal or naming ritual>"
    constraint: "<tier sentence limit>, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: "<gentle goodbye that validates whatever they collected>"
    constraint: "<tier sentence limit>, no pressure"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "<entity photo composition>"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "<Short Label>"
    animation_label: "Sparkle highlight"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 4
    animation: card_slide_in
    trigger: on_round_1
    sfx_cue: photo_shutter_click
    widget_label: "Find 1: <Label>"
    animation_label: "Card slide in"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 4
    animation: celebration_burst
    trigger: on_round_2
    sfx_cue: photo_shutter_click
    widget_label: "Find 2: <Label>"
    animation_label: "Collection burst"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 4
    animation: celebration_burst
    trigger: on_round_3
    sfx_cue: mission_complete_fanfare
    widget_label: "Find 3: <Label>"
    animation_label: "Collection burst"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "<Role Title>"
    concepts: [<Key Concept>, <Second>]
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
| Activity Category | Collection/Tracking Exploration (Out-of-Device) |
| Recommended Tier | <T0 (ages 2–4) / T1 (ages 4–6) / T2 (ages 6–8)> |
| Core IB Key Concepts | <Key Concept>, <Second> |
| Related Concepts | <related concepts> |
| ATL Skills Focus | <Communication/Thinking/Self-Management/Research/Social — which and why> |
| Game Style | <synthesis_format> |

### B. Activity Overview

**① Brief Description**

<3-5 sentence overview: the AI reaction to the entity, the role the child adopts, what they hunt for, how the synthesis step pays off the collection.>

**② Educational Purpose (KUD)**:
- **K (Know)**: <concrete observable facts about the entity and the observation_angle>
- **U (Understand)**: <how this connects to the IB key concepts — Form, Connection, Function, etc.>
- **D (Do)**: <skills practiced — observation, comparison, naming, pattern recognition>

**③ Design Highlight**: <what makes this activity's design special — the metaphor, the escalation across finds, the synthesis reveal>

**④ Typical Scenario**: <one-sentence description of a prototypical play session from start to badge>

### C. Interaction Flow

> Recommended Tier: <tier>

#### Step 1: Photo Hook

**AI says:** <wonder reaction to the entity + imaginative question about the observation_angle>

**Child responses:**

1. (Ideal) "<expected imaginative response>"
2. (Unexpected) "<off-script reaction>"
3. (No response) Child watches silently.

**AI follow-up:**

1. <validate the imagination>
2. <graceful pivot>
3. <gentle re-invitation after 2s>

**Screen:** <entity photo composition + observation_angle highlighted>

#### Step 2: Mission Invitation

**AI says:** <build on the child's answer to introduce the mission using mission_metaphor, invite them to be the role_title>

**Child responses:**

1. (Ideal) "<yes/ready response>"
2. (Unexpected) "<tangent>"
3. (No response) Quiet pause.

**AI follow-up:**

1. <celebrate and launch round 1>
2. <bridge back to the mission>
3. <gentle encouragement>

**Screen:** <photo + mission metaphor visual>

#### Step 3: Collection Rounds

**Round 1 — First <observation_angle>:**

**AI says:** <suggest where to look, frame as invitation, ask child to photograph and describe>

**Child responses:**

1. (Ideal) "<finds something>" + describes it
2. (Unexpected) <child picks a distractor or describes something irrelevant>
3. (No response) Child hasn't found anything yet.

**AI follow-up:**

1. <celebrate the find + harvest the detail via detail_question_template>
2. <redirect gently using stuck_hint>
3. <encouraging hint>

**Screen:** <progress tracker 1/3 filled>

**Round 2 — Compared <observation_angle>:** <same structure, prompting comparison to round 1>

**Round 3 — Final <observation_angle>:** <same structure, final find>

#### Step 4: Synthesis Reveal

**AI says:** <synthesis_format-specific reveal — collaborative_story tells a 3-scene story, comparison_reveal shows items side by side, sorting_challenge arranges them in order>

**Child responses:**

1. (Ideal) "<delighted reaction>"
2. (Unexpected) "<add their own detail or name>"

**AI follow-up:**

1. <amplify the delight, transition to celebrate>
2. <honor the addition, weave it into the reveal>

**Screen:** <synthesis widget — story_scene for collaborative_story; reveal_grid for comparison_reveal; sorted_lineup for sorting_challenge>

#### Step 5: Celebration

**AI says:** <award role_title with ceremony, recap the specific finds by name/description>

**Screen:** <badge animation>

#### Step 6: Closing + IB Concepts

**AI says:** <teach the IB concepts they just experienced, link to specific finds, warm goodbye>

**Screen:** <badge + IB concept lockup>
