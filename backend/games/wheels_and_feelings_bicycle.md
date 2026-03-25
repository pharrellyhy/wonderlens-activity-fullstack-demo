---
activity_type: wheels_and_feelings_bicycle
entity_name: bicycle
category: category_1
display_label: Bicycle
tier: T1
ib_theme: How the World Works
ib_key_concept: Function
concepts_earned: [Function, Connection]
keywords: [bicycle, bike, wheels, spokes, pedals, chain, ride]
feature_keywords: [shiny, strong, round, fast]
photo_features: [shiny wheels, thin spokes, strong frame, pedals]
plain_description: "Use your voice to speak as a bicycle and act out what the bike says or feels during 3 different adventures."
steps_summary:
  - "Learn the voice acting game with a quick demo round"
  - "Act out what the bike says while zooming downhill, how it feels when the tire goes flat, and what it thinks when it discovers a new path"
  - "Talk about how every part of the bike has a job and how the bike connects the rider to new places"
  - "Earn the Bike Whisperer badge!"

creative_slots:
  game_mechanic: voice_acting
  metaphor: The child becomes a 'Bike Whisperer' who can hear what the bicycle feels and says on different adventures.
  role_title: Bike Whisperer
  round_scenarios: [zooming downhill, getting a flat tire, discovering a new path]
  escalation_axis: from pure physical excitement to facing a problem, to exploring the unknown
  observation_detail: those shiny wheels and thin spokes that look like a spiderweb
step_instructions:
  hook:
    goal: React with wonder to the bicycle photo — notice its shiny wheels and thin spokes, then ask the child an imaginative
      question about what the bike would say if it could talk.
    constraint: T1 max 3 sentences, personal feeling hook, MUST end with an emotional/imaginative question.
    emotion_tag: excited
  transition:
    goal: 'Introduce the voice_acting game — explain that you will describe an adventure and the child speaks AS the bike.
      Include ONE demo round with the answer shown (e.g., waiting in the garage). End with a genuine invitation: ''Would you
      like to try?'''
    constraint: T1 max 3 sentences, demo round WITH answer included, end with Would you like to try?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: 'Set the scene vividly: riding down a big hill, wheels spinning faster, wind rushing past — then ask what the bike
      says or feels.'
    scenario: Adventure number one! Imagine you hop on your bike and ride down a big hill. The wheels spin faster and faster,
      and the wind rushes past!
    constraint: T1 max 3 sentences, paint the scene with sensory details, then ask what the bike would say.
    emotion_tag: excited
    acceptable_themes: [fast, whee, fun, zoom, spinning, wind, happy]
    escalation_note: pure physical excitement — easiest round
  - round_number: 2
    goal: 'Set the scene vividly: riding along when suddenly the front tire goes flat with a psssshh — then ask how the bike
      feels or what it says.'
    scenario: Oh no! You are riding along when suddenly... psssshh! The front tire goes flat!
    constraint: T1 max 3 sentences, use onomatopoeia (psssshh, oh no), then ask what the bike would say.
    emotion_tag: surprised
    acceptable_themes: [ouch, flat, stuck, oh no, help, sad, tired, stop]
    escalation_note: facing a problem — moderate intensity
  - round_number: 3
    goal: 'Set the scene vividly: riding the usual way but spotting a brand new path through the trees and around a pond —
      then ask what the bike says about this new adventure.'
    scenario: Wow! You are riding to the park but spot a brand new path through the trees and around a pond. You've never
      been here before!
    constraint: T1 max 3 sentences, build curiosity with sensory details, then ask what the bike does or says.
    emotion_tag: curious
    acceptable_themes: [wow, cool, new, explore, curious, pretty, adventure, let's go]
    escalation_note: exploring the unknown — peak imagination
  celebrate:
    goal: Award the child the title 'Bike Whisperer' with fanfare — recap the specific emotions explored (excitement downhill,
      ouchie with a flat, curiosity on a new path). Make the child feel like a champion.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific moments from the game.
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: every part has a job (Function) and the bike takes you to new places (Connection). Then
      plant a curiosity seed for next time.'
    constraint: T1 max 3 sentences, name Function and Connection naturally connected to what they experienced, warm goodbye.
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye that validates whatever they did — they are a great friend to the bicycle.
    constraint: T1 max 3 sentences, no pressure to continue.
    emotion_tag: gentle
screen_frames:
- widget: photo_display
  widget_params:
    description: Photo of the bicycle with gentle silver sparkle radiating from the wheel spokes.
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Your Bicycle
  animation_label: Sparkle highlight
- widget: character_display
  widget_params:
    description: Illustration of the bicycle rolling down a gentle green hill with wind lines and blurred spokes.
  animation: scene_transition
  trigger: on_round_1
  sfx_cue: scene_woosh
  widget_label: 'Round 1: Zooming Downhill'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of the bicycle with a flat front tire looking surprised or stuck.
  animation: scene_transition
  trigger: on_round_2
  sfx_cue: scene_woosh
  widget_label: 'Round 2: A Flat Tire'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of the bicycle discovering a beautiful new path through the trees.
  animation: gentle_pulse
  trigger: on_round_3
  sfx_cue: celebration_fanfare
  widget_label: 'Round 3: A New Path'
  animation_label: Gentle glow
celebration_frame:
  widget: badge_award
  widget_params:
    title: Bike Whisperer
    concepts: [Function, Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## Wheels and Feelings

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | Wheels and Feelings |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Function, Connection |
| Related Concepts | Rules, Community, Change Over Time, Discovery |
| ATL Skills Focus | Communication Skills (expressing, listening), Thinking Skills (creative thinking), Self-Management Skills (emotional regulation) |
| Game Style | voice_acting |

### B. Activity Overview

**① Brief Description**: After the child photographs their bicycle in the garage, the AI marvels at the shiny wheels and strong frame. The child becomes a "Bike Whisperer" — someone who can hear what the bicycle feels and says on different adventures. AI presents scenarios — riding fast downhill, getting a flat tire, waiting in the rain, discovering a new path — and the child speaks AS the bicycle, voicing its feelings and thoughts. Each scenario reveals how the bike's parts work (Function) and how the bike connects the rider to places and people (Connection).

**② Educational Purpose (KUD)**:
- **K (Know)**: A bicycle has a triangle-shaped frame like a strong stick puzzle; thin spokes spread out like a wheel spiderweb; pedaling makes the bike move forward; squeezing brakes slows the bike down with hand levers that pull cables; the chain makes a soft clicking sound as it turns
- **U (Understand)**: Every part of a bicycle has a special job — pedals for pushing, brakes for stopping, wheels for rolling. That is Function (how things work). A bicycle connects the rider to the park, the school, and the neighborhood — linking people and places together. That is Connection (how things are linked).
- **D (Do)**: Practice expressing emotions and ideas through voice acting, imagine how something non-human might feel, recognize and name different feelings

**③ Design Highlight**: The "Bike Whisperer" metaphor transforms a parked bicycle into a character with feelings and a voice. The child does not answer questions ABOUT the bike — they speak AS the bike, giving it personality, emotions, and thoughts. Each scenario puts the bicycle in a different situation that naturally reveals how its parts work and what it connects the rider to. The child earns the title by showing they can truly understand and voice a bicycle's inner world.

**④ Typical Scenario**: Child photographs their bicycle in the garage, AI notices the wheels and frame, and the child becomes a Bike Whisperer who voices what the bicycle feels during different adventures.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Ohhh wow, a bicycle! Look at those shiny wheels and all those thin spokes — they look like a spiderweb! I bet this bike goes on so many adventures. If your bike could talk right now, what do you think it would say?"

**Child responses:**

1. (Ideal) "Let's go ride!" / "I'm fast!" / "Take me outside!"
2. (Unexpected) "It's my bike!" / "The tire is flat." / "I can ride it!"
3. (No response) Child watches the screen silently.

**AI follow-up:**

1. (warm, impressed) "Ha! 'Let's go ride!' I love it! Your bike sounds like it is ready for action. You really understand what it is thinking. I bet you can hear even MORE of what it says."
2. (enthusiastic) "It IS your bike! And you know it so well. I bet if your bike could talk, it would have SO much to say about all the places you have been together. Want to find out?"
3. (wait 2s) (soft, wondering) "This bike looks like it has great stories to tell. What if you had a magic power to hear it talk? Want to be a Bike Whisperer with me?"

**Screen:** Bicycle photo centered with gentle silver sparkle radiating from the wheel spokes and tiny motion lines pulsing behind the rear wheel.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful, conspiratorial) "Okay, here is how the Bike Whisperer game works! I tell you something that happens to your bike. And YOU talk like the bike — you say what it FEELS and what it SAYS! Watch — I will show you!"

(demo) "If I say... 'your bike is parked in the garage all day, waiting' — hmm, what would the bike say? I think the bike would say... 'I am SO bored in here! When is my rider coming? I want to feel the wind in my spokes!' See? Now YOUR turn. Ready, Whisperer?"

**Child responses:**

1. (Ideal) "Ready!" / "Yeah!" / "Let's go!"
2. (Unexpected) "My bike is in the garage!" / child giggles / "That's funny!"
3. (No response) Child is quiet, possibly processing.

**AI follow-up:**

1. (excited) "Okay, Bike Whisperer — here comes the first adventure! Listen carefully..."
2. (delighted) "It IS funny — a talking bike! And you are the only one who can hear it. Here comes the first adventure!"
3. (wait 2s) (encouraging) "It is easy — I say what happens, and you talk like the bike. Say whatever you want! Here is the first one..."

**Screen:** Bicycle photo on the left; on the right, a cartoon speech-bubble icon with "Bike Whisperer" in playful letters and a simple animation of the bike in a garage with a thought bubble ("I'm bored!").

#### Step 3: Multi-Round Interaction

**Round 1 — "Zooming Downhill":**

**AI says:** (bright narrator) "Adventure number one! Imagine... you hop on your bike and ride down a big hill. The wheels spin faster and faster. The wind rushes past. What does the bike say? Talk like the bike!"

**Child responses:**

1. (Ideal) "Wheee! I'm going so fast!" / "My wheels are spinning!" / "This is fun!"
2. (Unexpected) "Vroom vroom!" / "I like going fast!" (speaks as self, not bike) / "Zoom!"
3. (No response) Child is quiet or looking at the photo.

**AI follow-up:**

1. (thrilled) "'Wheee!' — I KNEW it! The bike is loving that speed! Those wheels are spinning so fast, and the chain goes click-click-click. Going downhill makes the bike feel FREE and excited! You are a great Bike Whisperer!"
2. (warm) "Vroom vroom — yes! The bike is zooming! And I bet the bike is saying, 'My wheels are spinning so fast! I love going downhill — click click click goes my chain!' The hill makes the bike feel excited. Great job!"
3. (wait 2s) (helpful) "The bike is flying downhill — wind rushing past, wheels spinning fast! Is the bike feeling happy or scared? What would it shout?"

**Screen:** Animation of the bicycle rolling down a gentle green hill with wind lines, blurred spokes, and a big speech bubble when the child responds; "RIDE 1" stamp with golden star.

**Round 2 — "A Flat Tire":** The front tire goes flat with a psssshh while riding along. The child voices how the bike feels — stuck, hurt, or needing help. AI reveals that the tire's Function is to stay round and full of air so the wheel can spin.

**Round 3 — "Discovering a New Path":** The child is riding the usual way to the park but spots a path never taken before, through trees and around a pond. The child voices the bike's feelings about the new adventure. AI highlights how bikes connect riders to brand new places.

**Round 4 (if child is engaged) — "Waiting in the Rain":** It starts raining and the child runs inside, leaving the bike parked outside getting wet. The child voices the bike's mixed feelings — lonely but maybe brave. AI connects the rider caring about the bike to Connection.

#### Step 4: Celebration

**AI says:** (proud, warm) "WOW! You heard your bike on every single adventure! You felt its excitement going downhill, its ouchie with a flat tire, its curiosity on a new path, and its loneliness in the rain. You are officially a... BIKE WHISPERER! You gave your bike a voice, and that takes real heart!"

**Child responses:**

1. (Ideal) "Yay!" / "I'm a Bike Whisperer!" / giggles or cheers.
2. (Unexpected) "Can we ride for real?" / "I want more adventures!" / "My bike is the best."

**AI follow-up:**

1. (beaming) "The BEST Bike Whisperer! Your bike is so lucky to have someone who really listens to it."
2. (delighted) "You want more adventures? That means you REALLY love your bike! We can play again another day."

**Screen:** Golden badge animation with "BIKE WHISPERER" in bold playful letters, bicycle photo inside the badge, confetti in silver and blue, and a cheerful chime.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what you did today? You showed me that every part of your bike has a job — the wheels roll, the pedals push, the brakes stop, the chain clicks. That is called Function — how each part works! And you showed me that your bike takes you to the park, down new paths, and through the neighborhood — it connects you to all those places and people. That is called Connection — how things are linked together! You are not just a whisperer. You are a true bike friend."

**Child responses:**

1. (Ideal) "Function!" / "Connection!" / "I'm a bike friend!" / repeats a word happily.
2. (Unexpected) "Can I go ride now?" / "Bye bike!"

**AI follow-up:**

1. (celebrating) "That is right — Function and Connection! You earned your badge, Bike Whisperer. Next time you ride, listen close — maybe you will hear what your bike is saying!"
2. (warm) "Go ride! Your bike has been waiting all day. And now you know all its secrets. See you next time, Bike Whisperer!"

**Screen:** Bike Whisperer badge centered with "Function" and "Connection" in silver-blue lettering below; a gear icon for Function, a chain-link icon for Connection; bicycle photo glowing warmly behind the text with soft sparkle animations.
