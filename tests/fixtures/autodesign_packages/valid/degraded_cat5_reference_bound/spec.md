# B-Sound Treasure Hunt -- Authoring Spec

> Category 5 (Collection/Tracking Exploration) . Parameterized language match pattern . Mechanic: `collect`

## Premise

The AI introduces the target sound `/b/` and invites the child to become a Sound Treasure Scout. The child searches nearby for three everyday "treasures" whose spoken names begin with `/b/`, such as ball, book, block, bear, bottle, or banana. Each photo is treated as a possible sound treasure. When recognition is uncertain, the AI asks the child to name the object and sound out the first part.

## Target

- **Primary tier:** T1 (ages 4-6)
- **Activity category:** Cat5, out-of-device collection/tracking in an indoor-safe space
- **Mechanic:** `collect`
- **Target sound:** `/b/`
- **Entity role:** catalyst; the starting object or mode starts a language hunt
- **Progression axis:** Form, level 2

## Adaptation Rationale

- **Input mode:** parameterized.
- **Core promise:** preserve the source concept's beginning-sound treasure hunt while keeping it playful and low-pressure.
- **Canonical mechanic:** `collect`; Step 3's repeated child action is find, photograph, and add an item whose name starts with `/b/`.
- **Readiness:** generate_with_assumptions.
- **Trigger condition:** child enters language treasure-hunt mode or photographs an everyday object suitable for sound play.
- **Mapping use:** no entity mapping is required. The package does not claim entity-specific facts.
- **Asset dependency:** optional support. `phoneme_letter_card_01` may be shown as a visual reminder, but the activity works by voice if the card is unavailable.
- **Product capability flags:** `requires_assets` only for optional display support.
- **Scaffold fit:** acceptable. Adventure / `quest_collector` fits the treasure-hunt mission, but the closed observation-angle enum has no phoneme value. The package uses `pattern` to represent the repeated beginning-sound pattern.
- **Assumptions:** the optional source card is authored for `/b/`, so this package uses `/b/` as the concrete target sound. The source row says one treasure; this Cat5 runtime expands to three short treasure rounds so the `collect` mechanic is repeated and reviewable.

## Selection Trigger

Start this activity when the child enters a language hunt mode, or when a photographed everyday object can safely catalyze sound play. The runtime does not need OCR. It may use object classification, child naming, and dialogue to decide whether a treasure's spoken name begins with `/b/`.

## Experience Pillar & Game Style

- **Pillar:** Adventure
- **Game style:** `quest_collector`
- **Why this scaffold:** the sound criterion becomes a quest rule, each find fills a treasure slot, and the final map reveals a team of `/b/` treasures.

## Asset Brief

| asset_id | asset_type | requiredness | generation_timing | use_step | purpose | prompt_en/source | display_behavior | fallback_behavior | safety_constraints |
|---|---|---|---|---|---|---|---|---|---|
| phoneme_letter_card_01 | card_set | optional | pre_generated | prod.step_1; prod.step_3.round_1 | Give the child a visual reminder of the target `/b/` sound and letter. | prompt_en: Create a simple child-friendly phonics card for the /b/ sound. Show uppercase B and lowercase b in large rounded letters, include one small friendly picture of a ball and one banana, use a clean light background, no extra words, suitable for children ages 4-6. Source: new_ai_generated_asset. | Show the card at task start and briefly again if the child forgets the target sound. | If the card is unavailable, the AI repeats the target sound by voice only and must not claim the screen is showing a letter. | No real child photos, no brands, no complex text, and no cluttered composition. |

## Runtime Detail Floor Notes

- **Distinct round design:** The child builds a three-photo sound map. Each accepted treasure adds a slot, a path segment, and another chance to compare the spoken beginning sound.
- **Branch specificity:** The AI handles nonmatches without rejecting the child personally: it can ask for the object name, model the first sound, or place a find in the "different sound" basket.
- **Earned magic moment:** The `/b/` treasure map appears only after three collected examples. The payoff is the visible sound team, not just a phonics badge.
- **Residual risk:** The runtime may need child naming or caregiver help when object classification is uncertain; the activity avoids OCR and does not require reading letters.

## Self-Evaluation Scorecard

Evaluated against `prod.md`, `tag_block.yaml`, `program.md` Phase 3, `templates.md` Adventure + Cat5 rules, and the Phase 0 adaptation brief.

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | V1 Technical Compliance | PASS | The activity uses independent object photos, object labels, child naming, and dialogue. It does not require OCR, face/expression/pose detection, IMU sensing, non-speech audio detection, or before/after state comparison. |
| 2 | Hook & Transition | PASS | Step 1 opens with playful sound resonance and an optional card/fallback, then naturally pivots into finding `/b/` treasures. |
| 3 | Edge Case Coverage | PASS | Every dialogue step includes ideal, unexpected, and no-response branches with 2s waits; Step 3 includes non-match and stuck handling. |
| 4 | IB Completeness | PASS | Form and Connection are named, KUD is specific, related concepts and ATL skills are present, and the closing ties sound pattern and collected items to the concepts. |
| 5 | Tier Appropriateness | PASS | T1 children hear one target sound, find three familiar items, and answer short sound prompts with caregiver support available. |
| 6 | Dialogue Specificity | PASS | AI lines are concrete spoken dialogue with tone markers and no abstract runtime instructions. |
| 7 | Screen & UI Completeness | PASS | Every step includes concrete screen states, optional `phoneme_letter_card_01` display, voice-only fallback, treasure slots, and a badge. |
| 8 | Entity Mapping Alignment | N/A | Parameterized concept package with no `mapping=` assignment and no entity-specific mapping claims. |
| 9 | Game Feel | PASS | Sound verdicts, treasure-slot progress, a maybe basket, and the final `/b/` treasure map create stakes and payoff. |
| 10 | Mechanic Fidelity + Scaffold Honesty | PASS | `collect` is preserved in Step 3 and tag metadata; the phoneme-to-`pattern` enum compromise and one-treasure-to-three-round expansion are disclosed. |

**Overall**: ALL PASS -- Older Package Reviewer C pass completed; optional asset fallback, sound-pattern compromise, and `collect` loop remain explicit after review.
