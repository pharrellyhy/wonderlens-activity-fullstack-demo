---
activity_type: safety_solver_stop_sign
entity_name: stop_sign
category: category_1
display_label: Stop Sign
tier: T1
ib_theme: Sharing the Planet
ib_key_concept: Responsibility
concepts_earned: [Responsibility, Function]
keywords: [stop sign, traffic sign, red sign, octagon, safety sign, street sign]
feature_keywords: [red, white border, octagon, eight sides, shiny]
photo_features: [bold red color, eight sides, white border, white letters]
creative_slots:
  game_mechanic: helper_hotline
  metaphor: The stop sign is a superhero for the street, and you are the dispatcher helping people figure out what to do.
  role_title: Safety Solver
  round_scenarios: [A driver in a big hurry wants to go fast past the sign., 'A driver is stopped, but a little kid is still
      walking slowly across the street.', Two cars arrive at the stop sign at the exact same time.]
  escalation_axis: simple rule following to complex social turn-taking and empathy
  observation_detail: that bright red color and special eight-sided shape
step_instructions:
  hook:
    goal: React with wonder to the stop sign — notice its bright red color and eight-sided shape, then ask the child what
      they would do if they saw this sign while walking to the park.
    constraint: T1 max 3 sentences, MUST end with an invitational question about what they would do.
    emotion_tag: excited
  transition:
    goal: Introduce the helper_hotline game — explain that people will call because they are confused at crossings, and the
      child will decide what they should do. Include ONE demo round with a bike rider. End with an invitation to play, like
      'Would you like to try?'
    constraint: T1 max 3 sentences, demo round WITH answer included, end with Would you like to try?
    emotion_tag: playful
  rounds:
  - round_number: 1
    goal: Present a call from a driver who is in a hurry and wants to go fast past the stop sign. Ask the child what to tell
      the driver.
    scenario: Ring ring! 'Help! I am driving and I am in a hurry. I see a stop sign but I want to go fast.' What should we
      tell this driver?
    constraint: T1 max 3 sentences, use a ringing sound effect word, ask what the driver should do.
    emotion_tag: urgent
    acceptable_themes: [stop, wait, slow down, brakes, look, danger, 'no']
    escalation_note: Basic rule application - stopping despite wanting to go.
  - round_number: 2
    goal: Present a call from a stopped driver who sees a little kid walking slowly across the street. Ask the child if the
      driver should go or keep waiting.
    scenario: Ring ring! 'Hello! I stopped my car, but there is a little kid walking slowly across the street.' Should the
      driver go now, or keep waiting?
    constraint: T1 max 3 sentences, emphasize the slow walker, ask for a decision.
    emotion_tag: curious
    acceptable_themes: [wait, stay, let them cross, stop, patient, kid first]
    escalation_note: Adding empathy and responsibility for vulnerable pedestrians.
  - round_number: 3
    goal: Present a call where two cars arrive at the stop sign at the exact same time and both want to go. Ask the child
      how to solve it.
    scenario: Ring ring! 'Oh my! Two cars just got to the stop sign at the exact same time, and both want to go!' How can
      we help them share the road?
    constraint: T1 max 3 sentences, highlight the conflict of simultaneous arrival, ask how to solve it.
    emotion_tag: surprised
    acceptable_themes: [take turns, one first, wait, share, go next, wave, polite]
    escalation_note: Complex social negotiation and fairness (turn-taking).
  celebrate:
    goal: Award the child the title 'Safety Solver' with fanfare — recap how they helped the rushing driver, protected the
      walking kid, and taught cars to take turns.
    constraint: T1 max 3 sentences, announce role title ceremonially, reference specific moments from the game.
    emotion_tag: proud
  closing:
    goal: 'Teach the IB concepts: the stop sign''s Function is to make everyone take turns, and our Responsibility is to follow
      the rules to keep the community safe. Plant a curiosity seed for next time.'
    constraint: T1 max 3 sentences, name Function and Responsibility naturally, warm goodbye.
    emotion_tag: warm
  early_exit:
    goal: Gentle goodbye that validates their helpfulness — they are already great at knowing how to stay safe.
    constraint: T1 max 3 sentences, no pressure to continue.
    emotion_tag: gentle
screen_frames:
- widget: photo_display
  widget_params:
    description: Photo of the stop sign with a gentle red pulse radiating outward
  animation: sparkle_highlight
  trigger: on_enter
  sfx_cue: wonder_chime
  widget_label: Stop Sign Superhero
  animation_label: Sparkle highlight
- widget: character_display
  widget_params:
    description: Illustration of a rushing car with speed lines approaching a stop sign
  animation: scene_transition
  trigger: on_round_1
  sfx_cue: scene_woosh
  widget_label: 'Round 1: Rushing Driver'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of a driver waiting while a little kid walks across the crosswalk
  animation: scene_transition
  trigger: on_round_2
  sfx_cue: scene_woosh
  widget_label: 'Round 2: Kid on Crosswalk'
  animation_label: Scene transition
- widget: character_display
  widget_params:
    description: Illustration of two cars stopped at a four-way intersection at the same time
  animation: scene_transition
  trigger: on_round_3
  sfx_cue: scene_woosh
  widget_label: 'Round 3: Two Cars'
  animation_label: Scene transition
celebration_frame:
  widget: badge_award
  widget_params:
    title: Safety Solver
    concepts: [Responsibility, Function]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: Badge Earned!
  animation_label: Badge reveal
---

## The Safety Solver

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Name | The Safety Solver |
| Activity Category | Sustained Verbal Interaction (In-Device) |
| Recommended Tier | T1 (ages 4–6) |
| Core IB Key Concepts | Responsibility, Function |
| Related Concepts | Rules, Community, Safety, Communication |
| ATL Skills Focus | Thinking Skills (critical thinking, transfer), Communication Skills (expressing, listening), Social Skills (empathy) |
| Game Style | helper_hotline |

### B. Activity Overview

**① Brief Description**: After the child photographs a stop sign picture, the AI marvels at the bold red octagon and how it keeps everyone safe. The child becomes a "Safety Solver" who gets pretend calls from people, animals, and vehicles who need help with tricky traffic situations. Each round, the AI presents a safety problem at a crossing, and the child decides what the right thing to do is — building an intuition for rules, turn-taking, and caring about others on the road.

**② Educational Purpose (KUD)**:
- **K (Know)**: A stop sign has a bright white border that frames the red; it has a shiny coating that glows when lights hit it at night; stop signs stand at corners where roads cross each other; the sign tells drivers to stop fully before going; stop signs help cars take turns safely at crossings
- **U (Understand)**: The stop sign has a specific job — to make everyone stop and take turns at crossings. That is Function (how it works). Everyone — drivers, bikers, walkers — has a duty to follow the stop sign rule to keep the community safe. That is Responsibility (what is our responsibility).
- **D (Do)**: Practice deciding what to do in safety scenarios, explain choices in words, consider other people's safety

**③ Design Highlight**: The "Safety Solver" metaphor transforms traffic rules into a dispatch-style problem-solving game. The child is not memorizing rules — they are making decisions about what someone should DO in tricky situations involving crossings, turns, and sharing the road. Each caller presents a scenario with increasing complexity, from a simple "should I stop?" to situations involving helping others and making fair choices.

**④ Typical Scenario**: Child photographs a stop sign picture on the fridge, AI notices its bold red shape and purpose, and the child becomes a Safety Solver who receives calls about tricky traffic situations and decides what to do.

### C. Interaction Flow

> Recommended Tier: T1 (ages 4–6)

#### Step 1: Transition Bridge

**AI says:** (delighted gasp) "Ohhh, a stop sign! Look at that bright red color and that special shape — it has eight sides! This sign is like a superhero for the street. It keeps everyone safe. If you were walking to the park and you saw this sign, what would YOU do?"

**Child responses:**

1. (Ideal) "Stop!" / "I would wait!" / "Look both ways!"
2. (Unexpected) "It's red!" / "I know that sign!" / "My dad stops the car."
3. (No response) Child watches the screen silently.

**AI follow-up:**

1. (warm, impressed) "Yes! You would stop and look — that is exactly right! You already know the stop sign's rule. I bet you could help OTHER people learn it too."
2. (enthusiastic) "You DO know that sign! It is everywhere, keeping everyone safe. But some people get confused at crossings. What if we could help them figure it out?"
3. (wait 2s) (soft, wondering) "This stop sign works SO hard to keep the street safe. What if we helped it out? Want to be a safety helper with me?"

**Screen:** Stop sign photo centered with gentle red pulse animation radiating outward and tiny sparkle animations glinting off the white border.

#### Step 2: Rule Introduction + Demo

**AI says:** (playful, setting up) "Okay, here is how our Safety Solver Hotline works! Someone calls us because they are confused about what to do at a crossing. You decide what they should do! Watch — I will show you."

(demo) "Ring ring! 'Hello, I am riding my bike and I see a stop sign. Should I keep going?' Hmm, what should we tell them? I think... STOP! Put your feet down, look both ways, and THEN go when it is safe. See? Your turn next!"

**Child responses:**

1. (Ideal) "Okay! My turn!" / "I want to help!"
2. (Unexpected) "I ride a bike too!" / "Can I call?"
3. (No response) Child is watching quietly.

**AI follow-up:**

1. (enthusiastic) "Great! Get ready — here comes the first call to our hotline!"
2. (warm, redirecting) "You ride a bike — so you know about stopping! Now let's help other people. Ready for a call?"
3. (wait 2s) (encouraging) "The phone is ringing! Should we pick it up together?"

**Screen:** Stop sign photo in top left; a large colorful phone icon in the center with a "ring ring" wiggle animation; after the demo, a bicycle icon with a checkmark showing the solved problem.

#### Step 3: Multi-Round Interaction

**Round 1 — "The Rushing Driver":**

**AI says:** (phone ring) "Ring ring! 'Help! I am driving and I am in a hurry. I see a stop sign but I want to go fast. What should I do?' Oh! What should we tell this driver?"

**Child responses:**

1. (Ideal) "Stop!" / "You have to stop!" / "Wait your turn!"
2. (Unexpected) "Go fast!" / "Honk the horn!" / "Drive!"
3. (No response) Child is quiet.

**AI follow-up:**

1. (impressed) "Yes! Even if you are in a hurry, you MUST stop at the stop sign. Stop fully, look both ways, and then go when it is your turn. The stop sign's job is to keep everyone safe. That is its Function! Great solving!"
2. (gently guiding) "Going fast sounds fun — but at a stop sign, EVERYONE has to stop, even if they are late. If cars do not take turns, they could crash! The stop sign's job — its Function — is to make sure nobody gets hurt. What should the driver do first?"
3. (wait 2s) (helpful) "The driver is in a hurry. But the stop sign says STOP. Should the driver listen to the sign... or just keep going?"

**Screen:** Cartoon street corner with a stop sign and a rushing car with speed lines; when the child answers, the car slows and stops, a green checkmark appears, and eye icons show the driver looking left and right.

**Round 2 — "The Kid on the Crosswalk":** A driver stopped at the stop sign sees a little kid still walking slowly across the street. The child decides whether the driver should go or keep waiting. AI connects the answer to Responsibility — taking care of walkers.

**Round 3 — "Two Cars at the Same Time":** Two cars arrive at the stop sign at the same time, both stopped, both wanting to go. The child decides who goes first. AI reveals the taking-turns rule and connects it to fairness and community safety.

**Round 4 (if child is engaged) — "The Missing Stop Sign":** A storm knocked the stop sign down and cars are zooming by a confused corner. The child decides what to do. AI connects the answer to community Responsibility — helping when a safety system is broken.

#### Step 4: Celebration

**AI says:** (proud, warm) "WOW! You answered every single call! You helped a rushing driver stop, kept a little kid safe, taught two cars to take turns, and even fixed a missing sign. You are officially a... SAFETY SOLVER! You knew exactly what everyone needed to do."

**Child responses:**

1. (Ideal) "Yay!" / "I did it!" / giggles or cheers.
2. (Unexpected) "Can we play again?" / "I want more calls!" / "I like stop signs now."

**AI follow-up:**

1. (beaming) "The BEST Safety Solver! Every caller got the right help because of you. The whole street is safer now!"
2. (delighted) "You want more calls? That means you are a REAL safety expert — always watching out for people! We can play again another day."

**Screen:** Golden badge animation reading "SAFETY SOLVER" with a small stop-sign icon at top, confetti in red and white, and the stop sign photo surrounded by small icons of each caller with checkmarks.

#### Step 5: Closing + IB Concepts

**AI says:** (warm, reflective) "You know what you showed me today? You figured out that the stop sign has ONE big job — making everyone stop, look, and take turns. That is called Function — everything has a purpose! And you chose to help every single caller, even the tricky ones. You made sure everyone — drivers, walkers, the whole neighborhood — stayed safe. That is called Responsibility — caring about others and doing the right thing. You are a true safety hero!"

**Child responses:**

1. (Ideal) "Function!" / "Responsibility!" / "I'm a hero!" / repeats a word happily.
2. (Unexpected) "Can I go see a real stop sign?" / "Bye stop sign!"

**AI follow-up:**

1. (celebrating) "That is right — Function and Responsibility! You earned your badge, Safety Solver. Next time you see a stop sign, you will know it is working hard — just like you!"
2. (warm) "Go look at a real stop sign — you will see it in a whole new way now! And remember, it is always on duty. See you next time, Safety Solver!"

**Screen:** Safety Solver badge centered with "Function" and "Responsibility" in bold friendly lettering below; a gear icon for Function, a heart-and-hands icon for Responsibility; stop sign photo glowing warmly behind the text with soft sparkle animations.
