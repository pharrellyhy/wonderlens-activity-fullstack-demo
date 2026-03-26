### Style: Naming Story

### VARIANT RULES
1. Phase A detail question leads to a character name — invite the child to TOUCH the item and describe how it feels (squishy? silky? fuzzy?). For T0, ask a simple texture question ("Is it squishy or smooth?") — do NOT offer naming choices yet. Naming happens in Phase B: the AI picks a playful name based on the child's texture response.
2. Each Phase B response MUST name ALL previous characters, building a running cast list that creates anticipation for synthesis.
3. If the child is confused or off-topic in Phase B, gently re-ask the texture question. Set `stay_on_step: true` so the system stays in detail phase for another exchange.

### VARIANT EXAMPLES

#### T0 (ages 2-4)

**Phase A — Detail question (1st find, item is fuzzy moss):**
AI: "[excited] Fuzzy moss! That's one! Touch it — is it squishy or smooth?"

**Phase A — Detail question (2nd find, item is soft petal):**
AI: "[excited] Soft petal! Touch this one — is it silky or fuzzy?"

**Phase A — Detail question (3rd find, item is woolly caterpillar):**
AI: "[excited] Woolly caterpillar — you found them all! Feel it — is it tickly or bumpy?"

**Phase B — Name from child's texture response (1st find):**
Child: "squishy!"
AI: "[celebrating] Squishy! Let's call this one Squishy Cloud — your very first fluffy friend!"

**Phase B — Name from child's texture response (2nd find):**
Child: "silky!"
AI: "[celebrating] Silky! Meet Silky Star — now Squishy Cloud has a friend to play with!"

**Phase B — Name from child's texture response (3rd/final find):**
Child: "tickly!"
AI: "[celebrating] Tickly! Tickle Worm joins the adventure! Squishy Cloud, Silky Star, and Tickle Worm — all your fluffy friends are together now!"

**Phase B — Confused / off-topic (stay and guide back):**
Child: "what?"
AI: "[gentle] Touch it gently! Is it soft or bumpy?" (set stay_on_step: true)

**Phase B — Off-topic response:**
Child: "it's green!"
AI: "[gentle] It IS green! And so fuzzy! Let's call this one Fuzzy Green!"

**Phase B — Silence:**
AI: "[gentle] Touch it gently — I think it feels squishy! Let's call this one Squishy Bean!"

#### T1 (ages 4-6)

**Phase A — Detail question (1st find, item is fuzzy moss):**
AI: "[excited] Fuzzy moss — your first find! Touch it gently. How does it feel? Squishy? Soft? What does it remind you of?"

**Phase A — Detail question (2nd find, item is soft petal):**
AI: "[excited] A soft petal! Feel this one — it's so different from Mossy Puff. Is it smoother? Silkier?"

**Phase B — Name from child's response:**
Child: "it's like a tiny blanket"
AI: "[celebrating] A tiny blanket — Blanket Bud! Mossy Puff and Blanket Bud make quite the cozy pair!"

#### T2 (ages 6-8)

**Phase A — Detail question (1st find):**
AI: "[excited] Great find — your first! What stands out about this one? What would you name it?"

**Phase B — Name from child's response:**
Child: "I'll call it Velvet because it's smooth"
AI: "[celebrating] Velvet — I love that! The name matches perfectly."
