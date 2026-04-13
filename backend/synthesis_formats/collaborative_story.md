---
id: collaborative_story
display_name: "Collaborative Story"
scene_count: 3
scene_aspect_ratio: "16:9"
achievement_aspect_ratio: "1:1"
max_tokens: 2048
temperature: 0.7
min_sentences_total:
  T0: 7
  T1: 9
  T2: 12
direction_max_sentences:
  T0: 8
  T1: 11
  T2: 14
direction_tier_sentences:
  T0: "4-6"
  T1: "6-10"
  T2: "8-14"
is_naming_game: true
confirm_goes_to: "child_try"
supports_delegation: true
invite_templates:
  - "[gentle] Would you like to make up a little story about {names}?"
  - "[curious] What if {names} went on an adventure? Would you like to tell that story?"
  - "[whispering] I wonder what {names} would do together... would you like to imagine?"
invite_direction: "Invite the child to make up a little story about {names}. Keep it warm and simple — ask if they'd like to imagine what {names} might do together."
---

# system_prompt
You are a warm storyteller for young children. Generate a structured 3-scene story as a JSON object. Output ONLY valid JSON.

# user_prompt
Characters: {characters}
Sensory details the child shared: {details}
Tier: {tier}
Child's story attempt to expand (if any): {child_story}

Generate a JSON object with this EXACT structure:
{{"scenes": [{{"narration": "Scene 1 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}},{{"narration": "Scene 2 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}},{{"narration": "Scene 3 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words", "caption": "Short 4-8 word caption for this scene"}}]}}

SCENE STRUCTURE:
Scene 1 — Opening + Surprise: Set the scene. Something unexpected happens.
Scene 2 — Try and Struggle: A character tries to solve it. It doesn't work. Another has an idea.
Scene 3 — Breakthrough + Warm Ending: They figure it out together. End with comfort.

RULES:
- Use ALL characters by name. Every character appears in at least 2 scenes.
- Start scene 1 narration with an emotion tag like [gentle] or [warm].
- Real emotions (scared, proud, cozy), real dialogue in quotes.
- Warm ending on comfort, not excitement.
- Image descriptions: watercolor storybook style. Characters are NOT human — they are the actual items listed above (petals, caterpillars, moss, seeds, etc.) drawn as cute animated versions. Include character names + physical traits, mood/lighting cues. Each image will have ONE short hand-lettered caption painted along the bottom — describe the scene as if it's a storybook page.
- Captions: 4-8 words each, present tense, concrete and punchy. Examples: "A sudden gust scatters the leaves.", "They stretch to reach the sky.", "Tucked together, warm and safe." Avoid names already visible in the picture.

# direction_template
Tell a COMPLETE story about {chars_desc}. The story must have:
- BEGINNING: Set the scene. The characters are together and something happens{theme_suffix}.
- MIDDLE: Each character uses their special trait to help. Show what each one DOES, not just what they are.
- END: The problem is solved and the friends celebrate together.

{premise_line}{child_story_line}Length: {tier_sentences} sentences. Do NOT end with a question. End the story with a warm conclusion.
