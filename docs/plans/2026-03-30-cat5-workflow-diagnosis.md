# Cat5 Workflow Diagnosis — Full Mermaid Diagrams

Two known issues in the Cat5 (out-of-device collection) game flow:
1. **Collection phase desync** — AI dialogue references the current round's detail while the screen already shows the next round's photo grid
2. **Synthesis classification too strict** — Short T0 stories (ages 2-4) misclassified as "unrelated" instead of "story_attempt(weak)"

---

## Diagram 1: Full Cat5 Backbone

End-to-end state machine showing all 6 steps, edge cases, and frontend UI switching.

```mermaid
flowchart TD
    classDef bugZone stroke:#e74c3c,stroke-width:3px,color:#e74c3c
    classDef autoStep fill:#ecf0f1,stroke:#95a5a6,stroke-dasharray:5 5
    classDef terminal fill:#2c3e50,color:#fff
    classDef exitNode fill:#e74c3c,color:#fff
    classDef feState fill:#d4e6f1,stroke:#2980b9

    %% ── Backend State Machine ──
    START(["POST /api/start — Director + Visual + Script pipeline"])
    START --> HOOK

    subgraph Backend["Backend State Machine - turn_handler.py"]
        HOOK["STEP_1_HOOK — AI emotional reaction to photo"]
        MISSION["STEP_2_MISSION — Explain collection mission"]

        subgraph CollectLoop["STEP_3_COLLECT 1..N — repeated per round"]
            PHASE_A["Phase A: Photo Selection — collection_phase=photo — Show 1 correct + 2-3 distractors"]
            WRONG_PHOTO["Wrong Photo — consecutive_wrong++ — Shake animation + redirect"]
            CORRECT_PHOTO["Correct Photo — collected_photos.append — collection_phase=detail — consecutive_wrong=0"]
            PHASE_B["Phase B: Detail Question — collection_phase=detail — How does it feel?"]
            DETAIL_DONE["Detail Complete — collected_details.append — collected_names.append"]
            NEXT_ROUND{"remaining_count > 0?"}
        end

        SYNTH["STEP_4_SYNTHESIS — Story loop: invite, evaluate, improve, generate"]
        CELEBRATE["STEP_5_CELEBRATE — Badge award + role title — auto-advance"]:::autoStep
        CLOSING["STEP_6_CLOSING — IB concept goodbye — auto-advance"]:::autoStep
        ENDED["ENDED — status=completed"]:::terminal

        EARLY_EXIT["EARLY EXIT — status=exited"]:::exitNode
    end

    %% ── Main Flow ──
    HOOK -->|"child responds"| MISSION
    MISSION -->|"child accepts"| PHASE_A
    MISSION -->|"declined 1st → re-invite"| MISSION
    MISSION -->|"declined 2nd"| EARLY_EXIT
    MISSION -->|"off-topic → redirect"| MISSION

    PHASE_A -->|"wrong photo_id"| WRONG_PHOTO
    WRONG_PHOTO -->|"consecutive_wrong < 2"| PHASE_A
    WRONG_PHOTO -->|"consecutive_wrong >= 2"| EARLY_EXIT
    PHASE_A -->|"correct photo_id — L967-970"| CORRECT_PHOTO
    CORRECT_PHOTO --> PHASE_B

    PHASE_B -->|"stay_on_step AND detail_exchange < 3"| PHASE_B
    PHASE_B -->|"detail response received"| DETAIL_DONE
    DETAIL_DONE --> NEXT_ROUND

    NEXT_ROUND -->|"Yes → phase=photo + advance_state — BUG: both in same response"| PHASE_A
    NEXT_ROUND -->|"No → round_advance_pending=True — auto_advance into SYNTHESIS"| SYNTH

    SYNTH -->|"story accepted or AI-generated"| CELEBRATE
    CELEBRATE -->|"auto-advance"| CLOSING
    CLOSING -->|"auto-advance"| ENDED

    %% ── Silence from any input step ──
    HOOK -.->|"silence >= 2"| EARLY_EXIT
    MISSION -.->|"silence >= 2"| EARLY_EXIT
    PHASE_A -.->|"silence >= 2"| EARLY_EXIT
    PHASE_B -.->|"silence >= 2"| EARLY_EXIT
    SYNTH -.->|"silence >= 2"| EARLY_EXIT

    %% ── Bug zone highlights ──
    NEXT_ROUND:::bugZone
    SYNTH:::bugZone

    %% ── Frontend UI State ──
    subgraph Frontend["Frontend UI State - App.jsx"]
        FE_MAP_HOOK["ExplorerMap — fog/zones"]:::feState
        FE_MAP_MISSION["ExplorerMap — zone 0 active"]:::feState
        FE_GALLERY["PhotoGallery — 3-4 tappable photos"]:::feState
        FE_MAP_DETAIL["ExplorerMap — character revealed"]:::feState
        FE_MAP_SYNTH["ExplorerMap — all characters visible"]:::feState
        FE_MAP_BADGE["ExplorerMap — badge award"]:::feState
    end

    HOOK -.-> FE_MAP_HOOK
    MISSION -.-> FE_MAP_MISSION
    PHASE_A -.-> FE_GALLERY
    PHASE_B -.-> FE_MAP_DETAIL
    SYNTH -.-> FE_MAP_SYNTH
    CELEBRATE -.-> FE_MAP_BADGE
    CLOSING -.-> FE_MAP_BADGE
```

**Frontend switching condition** (App.jsx:85-88):
```js
showPhotoGallery = templateType === 'cat5'
  && current_step.startsWith('STEP_3_COLLECT_')
  && collection_phase !== 'detail'
  && isActive;
```

---

## Diagram 2: Collection Phase Desync (Issue 1)

Shows the exact race condition when Phase B completes and the backend returns both the naming dialogue AND the next round's state in one response.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BE as Backend
    participant SS as SessionState

    Note over SS: current_step = STEP_3_COLLECT_1<br/>collection_phase = detail<br/>detail_exchange_count = 1<br/>collected_photos = [fuzzy_moss]

    FE->>BE: POST /api/turn-speak {text: It feels soft and fuzzy!}

    Note over BE: Section 7b½ (L1064-1069)<br/>Match: COLLECT_ + phase=detail + has_input + no photo_id

    BE->>SS: detail_exchange_count = 2 (L1071)
    BE->>SS: collected_details.append (L1075)
    BE->>BE: _generate_with_retry() via Script Agent
    Note over BE: AI says: So soft! Like a little cloud!<br/>Lets call it Cloud Puff!

    BE->>SS: _maybe_record_generated_name → Cloud Puff (L1081)
    BE->>BE: remaining_count = 3 - 1 = 2 (L1083)<br/>remaining > 0, not last round

    rect rgb(255,220,220)
        Note over BE,SS: BUG: Both mutations in same response (L1115-1117)
        BE->>SS: collection_phase = photo (L1115)
        BE->>SS: detail_exchange_count = 0 (L1116)
        BE->>SS: _advance_state → STEP_3_COLLECT_2 (L1117)
    end

    BE->>BE: _get_screen_frame(state) → frame for COLLECT_2/photo

    BE-->>FE: Response JSON with dialogue + session_state + OGG audio

    rect rgb(255,220,220)
        Note over FE: DESYNC: applyTurnResponse runs immediately
        FE->>FE: setSessionState collection_phase=photo, step=COLLECT_2
        FE->>FE: showPhotoGallery = TRUE (App.jsx:85-88)
        Note over FE: PhotoGallery renders Round 2 photos<br/>WHILE TTS plays Lets call it Cloud Puff!
    end

    Note over FE: Child sees: photo grid for Round 2<br/>Child hears: AI naming Round 1 character<br/>Visual/audio mismatch
```

**Root cause:** `turn_handler.py:1115-1117` sets `collection_phase = "photo"` and calls `_advance_state()` before returning the response. The frontend applies session state immediately on receipt, before TTS finishes playing.

**Possible fixes (recommended → least disruptive):**
1. **Keep `collection_phase = "detail"`** in this response, return `auto_advance = True`, let the next empty turn flip to photo mode — cleanest separation but adds a round trip
2. **Add a `ui_phase` field** decoupled from the state machine that the frontend uses for rendering — more flexible but adds complexity
3. **Frontend delays `showPhotoGallery`** flip until TTS playback completes via `handleSpeakingDone` — frontend-only fix but fragile if TTS is muted

---

## Diagram 3: Synthesis Loop State Machine (Issue 2)

Shows the full STEP_4_SYNTHESIS sub-state machine with classification routing and the T0 misclassification bug.

```mermaid
stateDiagram-v2
    [*] --> invite : enter STEP_4_SYNTHESIS

    invite --> evaluate : AI generates story invitation, prompt_count++

    state evaluate_fork <<choice>>
    evaluate --> evaluate_fork : child responds, classify via LLM

    evaluate --> generate_silent : child is SILENT, skip classification

    evaluate_fork --> story_good : story_attempt, quality=good
    evaluate_fork --> story_weak : story_attempt, quality=weak
    evaluate_fork --> declined : classification=decline
    evaluate_fork --> ask_ai : classification=ask_ai
    evaluate_fork --> unrelated : classification=unrelated — T0 BUG HERE

    story_good --> advance_celebrate : celebrate story, advance

    state tier_check <<choice>>
    story_weak --> tier_check

    tier_check --> generate_from_seed : tier=T0, AI expands child seed
    tier_check --> improve : tier=T1/T2, ask child to elaborate

    improve --> improve_classify : child elaborates
    improve --> generate_from_seed : child is SILENT

    state improve_result <<choice>>
    improve_classify --> improve_result : reclassify combined story

    improve_result --> advance_celebrate : quality=good
    improve_result --> generate_from_seed : quality not good, AI completes

    declined --> generate_full : AI generates full story
    ask_ai --> generate_full : AI generates full story

    state prompt_check <<choice>>
    unrelated --> prompt_check

    prompt_check --> re_invite : prompt_count < 2, re-invite child
    prompt_check --> generate_full : prompt_count >= 2, max exhausted

    re_invite --> evaluate : stay in evaluate phase

    generate_silent --> advance_celebrate : AI story generated
    generate_from_seed --> advance_celebrate : AI story generated
    generate_full --> advance_celebrate : AI story generated

    advance_celebrate --> [*] : advance to STEP_5_CELEBRATE
```

**Bug zone:** The `unrelated → prompt_check → re_invite` path (highlighted above) is where T0 short stories get trapped.

**Classification prompt** (turn_handler.py:537-552):
```
"story_attempt": ANY narrative content (even single sentence like 'the dog went to sleep').
  quality "good": 2+ story elements (character + action, or action + outcome)
  quality "weak": single sentence with no progression
```

**The bug:** For T0 children (ages 2-4), typical responses are:
- "the fuzzy moss went to sleep" (1 character + 1 action → should be "weak" at minimum)
- "cloud puff is soft" (character + attribute → borderline)

The LLM classifier may see these as too short to be narrative and classify as `"unrelated"` instead of `"story_attempt(weak)"`. This triggers re-invites (up to 2) which confuse a 2-year-old.

Additionally, the **exception fallback** (line 581) defaults to `"unrelated"`, meaning any LLM failure during classification also triggers the re-invite loop.

**Possible fixes (recommended → least disruptive):**
1. **For T0, skip classification entirely** — treat any non-silent/non-decline response as a story seed for AI expansion (line 845-849 already handles T0 weak → generate, so we just need to always reach that path)
2. **Add tier context to prompt:** "For T0 (ages 2-4), even 3-word responses mentioning a character count as story_attempt(weak)"
3. **Change exception fallback** from `"unrelated"` to `"story_attempt"` with `quality="weak"` — fail-safe toward acceptance rather than rejection
