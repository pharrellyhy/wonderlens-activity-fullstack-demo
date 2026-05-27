# Star Pattern Counter -- Authoring Spec

> CAT1 concept package . Concept source: `source_constellation_star_count` . Mechanic: `enumerate`

## Premise

The child counts visible stars in a constellation card or simplified star pattern. The activity turns that source promise into a cat1 runtime package where the child becomes the Star Count Scout. The repeated action is `enumerate`, and the payoff is visible progress tied to the child's own responses.

## Target

- **Primary tier:** T1
- **Activity category:** cat1
- **Mechanic:** `enumerate`
- **Entity role:** reference
- **Progression axis:** form, level 2

## Adaptation Rationale

- **Input mode:** concept_only.
- **Core promise:** The child counts visible stars in a constellation card or simplified star pattern.
- **Canonical mechanic:** `enumerate`; Step 3's repeated child action preserves this mechanic.
- **Readiness:** generate_with_assumptions.
- **Trigger condition:** Child chooses a space theme or the screen can show an approved constellation card.
- **Mapping use:** no required mapping for this package; runtime parameters avoid entity-specific facts unless runtime supplies them.
- **Asset dependency:** Asset dependency: `constellation_count_cards_01` is required card_set support; fallback behavior is documented.
- **Product capability flags:** requires_asset_display.
- **Scaffold fit:** acceptable. Discovery / `field_experiment` supplies the emotional payoff while `enumerate` remains the child-action contract.
- **Assumptions:** Keep the counting task concrete and avoid astronomy claims unless asset metadata supplies them.

## Selection Trigger

Start when Child chooses a space theme or the screen can show an approved constellation card. If the required visual support is unavailable, use the fallback behavior from the Asset Brief or keep the interaction voice-only.

## Experience Pillar & Game Style

- **Pillar:** Discovery
- **Game style:** `field_experiment`
- **Why this scaffold:** The activity uses approved star cards or simplified fictional patterns and avoids unsupported astronomy claims.

## Runtime Detail Floor Notes

- **Distinct round design:** Round 1 -- Quick Estimate, Round 2 -- Count Together, and Round 3 -- Check the Pattern each ask for a different child contribution and update a different progress token.
- **Branch specificity:** Unexpected answers are validated, then redirected to the current objective without pretending the runtime can verify unsupported facts.
- **Earned magic moment:** The estimate flips into a counted star map, showing how careful counting checks a first guess.
- **Residual risk:** The package stays within the current Cat1/Cat5 and asset-display contract; any richer UI, material workflow, or stateful display beyond the documented fallback remains a product decision.

## Asset Brief

| Field | Value |
|---|---|
| asset_id | constellation_count_cards_01 |
| asset_type | card_set |
| requiredness | required |
| generation_timing | pre_generated |
| use_step | prod.step_2; prod.step_3.round_1-3 |
| purpose | Provide clear star patterns for counting and simple constellation talk. |
| prompt_en | Create a set of child-friendly constellation counting cards. Each card shows 4 to 10 bright stars connected by simple thin lines on a dark blue sky background, one pattern per card, no text, no real astronomy labels, no clutter, and high contrast for counting. |
| source | new_ai_generated_asset_or_approved_constellation_set |
| display_behavior | Show one card each round so the child can count visible stars. |
| fallback_behavior | If cards are unavailable, use a voice-only imaginary star-counting riddle and do not claim a constellation is displayed. |
| safety_constraints | No scientific claims unless backed by approved metadata, no scary space imagery, and no dense star fields. |
## Self-Evaluation Scorecard

Evaluated against `prod.md`, `tag_block.yaml`, `program.md` Phase 3, `templates.md`, and the Phase 0 adaptation brief.

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | V1 Technical Compliance | PASS | The package uses voice dialogue, simple screen state, and documented asset fallback behavior; it does not require unsupported sensing or material verification. |
| 2 | Hook & Transition | PASS | Step 1 bridges from the trigger into a playful role without testing the child. |
| 3 | Edge Case Coverage | PASS | Each step includes ideal, unexpected, and no-response handling with concrete redirects. |
| 4 | IB Completeness | PASS | Key Concepts, related concepts, KUD, ATL skills, recap, and dashboard fragments align. |
| 5 | Tier Appropriateness | PASS | Language and task load match T1 expectations. |
| 6 | Dialogue Specificity | PASS | Runtime lines include concrete prompts, child branches, and follow-ups instead of abstract encouragement. |
| 7 | Screen & UI Completeness | PASS | Screen states identify visible progress, token changes, and fallback behavior where assets are optional or required. |
| 8 | Entity Mapping Alignment | N/A | This is a concept-led package with no required mapping source and no entity-specific claims. |
| 9 | Game Feel | PASS | The loop has escalating rounds and a visible payoff earned from the child's repeated action. |
| 10 | Mechanic Fidelity + Scaffold Honesty | PASS | Step 3, tag metadata, and adaptation rationale preserve `enumerate` while disclosing scaffold assumptions. |

**Overall**: ALL PASS -- reviewer-agent pass by Dalton after package-quality edits.
