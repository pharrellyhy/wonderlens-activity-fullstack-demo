## Few-Shot Examples for Script Agent

These examples demonstrate the expected VoiceScript JSON output for different activity types and
tiers. Use these as reference when generating new scripts.

---

### Example 1: Mood Changer Dog (Category 1, T0)

**Entity**: stuffed toy dog
**Activity**: Mood Changer (Category 1 — Sustained Verbal Interaction)
**Tier**: T0 (ages 2-4)
**Key Concept**: Perspective
**Role Title**: Dog's Emotion Translator

```json
{
  "hook_line": "(gasping with delight) Oh WOW! A fluffy doggy! It's so soft and cuddly! Woof woof!",
  "transition_line": "(warm, building to magical) Your doggy looks so happy right now! I bet it has SO many feelings inside. What if we could hear what it's thinking? I'll tell you something that happens, and YOU tell me what the doggy says! Like this — if the doggy lost its ball, it might go 'ohh no, my ball!' Your turn — ready?",
  "rounds": [
    {
      "prompt": "(storytelling, cozy) Okay! It's morning time. The sun is warm on the doggy's belly. It's lying on the bed, nice and comfy. What does your doggy say?",
      "correct_responses": ["so warm", "comfy", "nice", "ahh", "mmm", "happy", "cozy", "sleepy", "yawn", "good morning", "woof"],
      "on_correct": "(mirroring warmth) Aww, yes! The doggy feels SO warm and cozy! Like a big fluffy hug!",
      "on_incorrect": "(validating) Ooh, that's a fun idea! I think the doggy is feeling really warm and snuggly right now — maybe it says 'so comfy!'",
      "on_silence": "(gentle) Maybe the doggy says 'so warm!' or just goes 'hmmm'... which one do you think?",
      "hint": "The sun is making the doggy feel nice! Does it say 'so warm' or 'ahh'?",
      "sfx_cue": "scene_woosh"
    },
    {
      "prompt": "(dramatic, playful) Oh no! The doggy just slipped off the bed — BUMP! It fell right on its bottom! What does your doggy say?",
      "correct_responses": ["ow", "ouch", "oh no", "whoa", "bump", "woof", "uh oh", "oopsie", "yikes"],
      "on_correct": "(excited) Ha! Yes! The doggy went BUMP and it's so surprised! That was a big tumble!",
      "on_incorrect": "(playful) That's a silly one! I think the doggy might say 'whoa!' or 'oopsie!' after that big bump!",
      "on_silence": "(encouraging) That was a big bump! Maybe the doggy says 'ouch!' or 'whoa!' — what do you think?",
      "hint": "The doggy fell — bump! Does it say 'ow' or 'whoa'?",
      "sfx_cue": "scene_woosh"
    },
    {
      "prompt": "(building excitement) GUESS WHAT! The owner is coming with the doggy's favorite treat! The doggy can smell it! What does your doggy do?",
      "correct_responses": ["yay", "treats", "yum", "woof woof", "bark", "happy", "excited", "jump", "run", "wag tail", "gimme"],
      "on_correct": "(celebrating) YES! The doggy is SO excited! Tail wagging, jumping up and down! Treats are the BEST!",
      "on_incorrect": "(validating with joy) Ooh I love that! I bet the doggy also goes 'YAY! TREATS!' and wags its tail super fast!",
      "on_silence": "(warm, gentle exit) That's okay! I think the doggy would go 'YAY! Treats!' and wag its whole body! We had so much fun hearing what your doggy thinks! Your doggy is lucky to have you. We can play again anytime!",
      "hint": "The doggy LOVES treats! Does it jump up and say 'yay!' or wag its tail?",
      "sfx_cue": "scene_woosh"
    }
  ],
  "closing_speech": "(proud, warm) You are AMAZING! You heard your doggy being cozy, surprised, and excited — you understood ALL its feelings! You are now the Dog's Emotion Translator! Your doggy is so lucky to have someone who listens to its heart.",
  "tomorrow_hook": "Next time, I wonder what your doggy dreams about at night..."
}
```

---

### Example 2: Polka-Dot Patrol (Category 5, T1)

**Entity**: ladybug
**Activity**: The Polka-Dot Patrol (Category 5 — Collection/Tracking Exploration)
**Tier**: T1 (ages 4-6)
**Key Concepts**: Form, Connection
**Role Title**: Polka-Dot Patrol Officer

```json
{
  "hook_line": "(gasping with wonder) Oh WOW — a ladybug! Look at those beautiful little spots! They're like tiny polka-dots painted right on its back!",
  "transition_line": "(amazed, building excitement) So many perfect little dots! I bet this ladybug isn't the only spotty thing in this park. What if we went on a mission to find MORE things with dots and spots? You could be a Polka-Dot Patrol Officer! Your mission: find 3 more things with dots, spots, or circles, and photograph each one. Ready, Officer?",
  "rounds": [
    {
      "prompt": "(official, playful) Alright, Polka-Dot Patrol Officer! Look around you — can you find something nearby that has dots, spots, or circles on it? When you find one, take a photo and tell me about it!",
      "correct_responses": ["flower", "dots", "spots", "circles", "found one", "look", "this one", "here", "I see one", "a flower with dots"],
      "on_correct": "(excited) Patrol report received! Wow, what a find! Look at those little dots — they're like nature's polka-dots! That's 1 down, 2 more to go!",
      "on_incorrect": "(encouraging) That's a cool find! You know what, I can see something a little bit spotty about it if I look really closely. Let's count it! 1 down, 2 more to go!",
      "on_silence": "(gentle, helpful) Hmm, sometimes the dots are hiding! Would you like to look around for something with tiny spots on it?",
      "hint": "Something with dots or circles might be closer than you think!",
      "sfx_cue": "photo_shutter_click"
    },
    {
      "prompt": "(encouraging) Great work, Officer! Can you find another dotty thing? Remember — dots, spots, circles, anything round and repeating counts!",
      "correct_responses": ["rock", "spots", "bark", "leaf", "found it", "this", "here", "another one", "I found", "look at this", "dots on it"],
      "on_correct": "(impressed) Another incredible find! Those spots are so cool — nature really does love making patterns! That's 2 down, just 1 more to go!",
      "on_incorrect": "(validating) Ooh, interesting choice! If I squint a little, I can see some roundish shapes on there. I'll count it — great eye! 2 down, 1 more!",
      "on_silence": "(supportive) Taking your time is totally fine! Something with spots might be waiting right where you are!",
      "hint": "Spots and circles show up in the most surprising places!",
      "sfx_cue": "photo_shutter_click"
    },
    {
      "prompt": "(building anticipation) Last one, Officer! One more spotty thing and your collection is COMPLETE! Can you find it?",
      "correct_responses": ["tree bark", "dots", "found it", "here", "last one", "this", "look", "spotted", "circles", "I found it"],
      "on_correct": "(triumphant) YOU DID IT! Collection COMPLETE! Three amazing spotted things plus your ladybug — FOUR polka-dot discoveries! Officer, you are incredible!",
      "on_incorrect": "(celebrating anyway) You know what? That absolutely counts! I can see the spots! Collection COMPLETE! Four polka-dot discoveries — you are an amazing officer!",
      "on_silence": "(warm, supportive) That's okay — finding spots takes patience! You already found TWO amazing dotty things, and that's pretty awesome. Want to try one more, or should we celebrate what we found?",
      "hint": "One more spotty thing — it could be anywhere around you!",
      "sfx_cue": "mission_complete_fanfare"
    }
  ],
  "closing_speech": "(warm celebration) Congratulations, Polka-Dot Patrol Officer! You found dots on a flower, a rock, and tree bark — all COMPLETELY different things, but they ALL have something in common! You noticed the beautiful Form of spots and patterns everywhere you looked, and you found a surprising Connection between all these different spotted things. That's what real explorers do! Here is your official Polka-Dot Patrol Badge!",
  "tomorrow_hook": "Next time you're outside, keep those patrol eyes open — I bet you'll spot dots and circles EVERYWHERE now!"
}
```
