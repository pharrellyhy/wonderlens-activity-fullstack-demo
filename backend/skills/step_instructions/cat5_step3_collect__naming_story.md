### Style: Naming Story

### VARIANT RULES
1. Phase A detail question leads to a character name — invite the child to TOUCH the item and describe how it feels (squishy? silky? fuzzy?). For T0, ask a simple texture question ("Is it squishy or smooth?") — do NOT offer naming choices yet. Naming happens in Phase B: the AI picks a playful name based on the child's texture response.
2. Each Phase B response MUST name ALL previous characters, building a running cast list that creates anticipation for synthesis.
3. If the child is confused or off-topic in Phase B, gently re-ask the texture question. Set `stay_on_step: true` so the system stays in detail phase for another exchange.

### VARIANT EXAMPLES

#### T0 (ages 2-4)

**Phase A — Detail question (1st find, item is fuzzy moss):**
AI: "[excited] Ooh, fuzzy moss! Give it a little poke — squishy or bumpy?"

**Phase A — Detail question (2nd find, item is soft petal):**
AI: "[surprised] A soft petal! This one looks different! Is it silky like a ribbon or fuzzy like a teddy?"

**Phase A — Detail question (3rd find, item is woolly caterpillar):**
AI: "[amazed] Woolly caterpillar — the last one! Quick, does it tickle or is it smooth?"

**Phase B — Name from child's texture response (1st find):**
Child: "squishy!"
AI: "[celebrating] Squishy! I'm calling this one Squishy Cloud — your very first fluffy friend!"

**Phase B — Name from child's texture response (2nd find):**
Child: "silky!"
AI: "[celebrating] So silky! Say hello to Silky Star — now Squishy Cloud has a friend!"

**Phase B — Name from child's texture response (3rd/final find):**
Child: "tickly!"
AI: "[celebrating] It tickles! Tickle Worm joins the crew! Squishy Cloud, Silky Star, and Tickle Worm — the whole gang is here!"

**Phase B — Confused / off-topic (stay and guide back):**
Child: "what?"
AI: "[gentle] Give it a little poke! Soft or bumpy?" (set stay_on_step: true)

**Phase B — Off-topic response:**
Child: "it's green!"
AI: "[gentle] Green and fuzzy! That's gotta be Fuzzy Green!"

**Phase B — Silence:**
AI: "[gentle] I gave it a poke — so squishy! This one's Squishy Bean!"

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
