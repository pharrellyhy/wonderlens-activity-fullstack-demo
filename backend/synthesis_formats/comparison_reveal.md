---
id: comparison_reveal
display_name: "Comparison Reveal"
scene_count: 1
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"
max_tokens: 1024
temperature: 0.7
min_sentences_total:
  T0: 3
  T1: 3
  T2: 3
direction_max_sentences:
  T0: 6
  T1: 8
  T2: 11
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"
is_naming_game: false
confirm_goes_to: "generate"
supports_delegation: true
invite_templates:
  - "[curious] Would you like to see how the {obs_angle} looks different on each one?"
invite_direction: |-
  Invite the child to compare all their finds together. Ask if they'd like to see how the {obs_angle} looks different on each one.
---

# system_prompt
You are a warm guide for young children exploring patterns and observations. Generate a JSON object. Output ONLY valid JSON.

# user_prompt
Items collected: {items}
Observation angle: {obs_angle}
Details the child noticed: {details}
Tier: {tier}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Comparison text (3-5 sentences)", "image_description": "Reveal image description under 50 words", "caption": "Short 4-8 word caption highlighting the comparison"}}]}}

NARRATION RULES:
- Start with an emotion tag like [excited] or [curious]
- Help the child compare the {obs_angle} across all {count} items
- Point out how the {obs_angle} looks different on each
- Reference the child's observations when possible
- 3-5 warm sentences, end with celebration (not a question)

IMAGE DESCRIPTION: Watercolor storybook illustration showing all {count} items ({items}) arranged side by side in a row, each clearly showing their different {obs_angle}. Soft pastel tones, warm lighting. The image will have ONE short hand-lettered caption painted along the bottom.

CAPTION: 4-8 words highlighting the observation angle, e.g. "Every {obs_angle} is different.", "Look how they compare!"

# direction_template
Guide a fun comparison of all the finds. Observations collected: {obs_list}.
Help the child see how the same thing ({obs_angle}) looks DIFFERENT on each item. {theme_angle_suffix}{sorting_suffix}{goal_suffix}
Then invite the child to give each find a fun creative name (e.g. 'Freckle Stone', 'Polka Petal'). Length: {tier_sentences} sentences. End warmly — do NOT end with a question.
