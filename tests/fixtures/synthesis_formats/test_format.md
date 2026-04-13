---
id: test_format
display_name: TEST FORMAT — do not use in production
scene_count: 2
scene_aspect_ratio: "4:3"
achievement_aspect_ratio: "1:1"
max_tokens: 512
temperature: 0.5
min_sentences_total:
  T0: 3
  T1: 5
  T2: 7
direction_max_sentences:
  T0: 4
  T1: 6
  T2: 8
direction_tier_sentences:
  T0: "2-4"
  T1: "4-6"
  T2: "6-8"
is_naming_game: true
confirm_goes_to: child_try
supports_delegation: false
invite_templates:
  - "[gentle] TEST INVITE A"
  - "[curious] TEST INVITE B"
invite_direction: "TEST INVITE DIRECTION — do not use in production"
---

# system_prompt

TEST SYSTEM PROMPT — do not use in production. This is a fixture file for unit tests only.

# user_prompt

TEST USER PROMPT — do not use in production.
Characters: {characters}
Tier: {tier}

# direction_template

TEST DIRECTION TEMPLATE — do not use in production.
Tell a story about {characters} using {tier} complexity.
