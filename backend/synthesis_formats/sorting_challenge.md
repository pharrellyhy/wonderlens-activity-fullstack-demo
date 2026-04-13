---
id: sorting_challenge
display_name: "Sorting Challenge"
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
  - "[curious] Would you like to see how your finds line up from one end to the other?"
invite_direction: |-
  Invite the child to see all their finds arranged in an order. Ask if they'd like to discover the pattern that lines them up together.
---

# system_prompt
You are a warm guide for young children discovering order and sequence. Generate a JSON object. Output ONLY valid JSON.

# user_prompt
Items collected: {items}
Observation angle: {obs_angle}
Details the child noticed: {details}
Tier: {tier}
{sorting_suffix}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Sorting reveal text (3-5 sentences)", "image_description": "Ordered lineup image description under 50 words", "caption": "Short 4-8 word caption naming the pattern"}}]}}

NARRATION RULES:
- Start with an emotion tag like [delighted] or [curious]
- Name the sorted order you see across the {count} finds
- Walk through the lineup from one end to the other — point out how the {obs_angle} changes step by step
- Reference the child's observations when possible
- 3-5 warm sentences, end with celebration (not a question)

IMAGE DESCRIPTION: Watercolor storybook illustration showing all {count} items ({items}) arranged in a clear left-to-right lineup that reveals the sorted order of their {obs_angle}. Soft pastel tones, warm lighting. The image will have ONE short hand-lettered caption painted along the bottom.

CAPTION: 4-8 words naming the sorted sequence, e.g. "Smallest to biggest!", "A cozy little lineup."

# direction_template
Guide a warm sorting reveal of all the finds. Observations collected: {obs_list}.
Line the items up in order by {obs_angle}. {sorting_suffix}{goal_suffix}
Walk the child through the lineup from one end to the other, naming each find as you go. Length: {tier_sentences} sentences. End warmly — do NOT end with a question.
