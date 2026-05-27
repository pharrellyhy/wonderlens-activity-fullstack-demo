# Tiny Curator Gallery -- Authoring Spec

> Category 5 (Collection/Tracking Exploration) . Parameterized match pattern . Mechanic: `sort`

## Premise

The child becomes a Tiny Curator. They choose three or four nearby objects, arrange them as a small exhibit, and explain the rule that makes the objects belong together. The AI does not impose a correct category first. It asks the child to choose, place, compare, label, and defend the grouping rule with evidence from the objects.

## Target

- **Primary tier:** T2 (ages 6-8)
- **Activity category:** Cat5, out-of-device collection/tracking
- **Mechanic:** `sort`
- **Parameterized trigger:** a home, classroom, or outdoor setting with several candidate objects
- **Entity role:** catalyst; the starting place or object set launches the child's gallery
- **Progression axis:** Connection, level 3

## Adaptation Rationale

- **Input mode:** parameterized.
- **Core promise:** preserve the source Tiny Curator loop: child-made rule, grouping, arrangement, and explanation.
- **Canonical mechanic:** `sort`; Step 3's repeated child action is choose an object, place it in relation to the group, and explain why it belongs under the child's rule.
- **Readiness:** generate_with_assumptions.
- **Trigger condition:** child is at home or outdoors with several objects that can be grouped or compared.
- **Mapping use:** no entity mapping is required. The package uses runtime placeholders and child-selected objects.
- **Asset dependency:** `no_assets`; no asset brief is needed.
- **Product capability flags:** none.
- **Scaffold fit:** weak but usable. `docs/game_styles.md` says `sort` has no perfect dedicated style. Adventure / `quest_collector` is used only for visible gallery progress and badge payoff; it does not turn the activity into a pre-scored collection hunt.
- **Assumptions:** runtime can show child-taken photos or simple object slots. The AI relies on the child's spoken explanation rather than computer vision to judge whether the rule is correct.

## Selection Trigger

Start this activity when the child is near multiple safe objects that can be grouped or compared: toys, leaves, rocks, household objects, classroom supplies, clothing, or snack packages. The AI can start from a room/table view, a first photographed object, or a verbal "I want to make a gallery" request.

Do not start if the child has only one object available, if the objects are unsafe to handle, or if the task would require the AI to identify a hidden correct category before the child chooses a rule.

## Experience Pillar & Game Style

- **Pillar:** Adventure
- **Game style:** `quest_collector`
- **Why this scaffold:** the child builds a visible path from first object to final exhibit label. The progress frame creates momentum, while the sort mechanic remains the actual learning action.

## Runtime Detail Floor Notes

- **Distinct round design:** The loop progresses from first object clue, to second-object comparison, to full exhibit rule. The child makes and revises a grouping rule rather than collecting against an AI-supplied category.
- **Branch specificity:** Favorite-object or off-rule choices are treated as curator thinking. The AI asks the child to name the reason, move the object to maybe, or revise the rule.
- **Earned magic moment:** The visitor test is passed only when the child gives a one-sentence tour. The final exhibit title comes from the child's rule.
- **Residual risk:** The AI does not prove object membership with computer vision. It accepts and scaffolds the child's spoken grouping evidence.

## Self-Evaluation Scorecard

Evaluated against `prod.md`, `tag_block.yaml`, `program.md` Phase 3, `templates.md` mechanic adapter rules, and `docs/game_styles.md` sort guidance.

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | V1 Technical Compliance | PASS | The activity uses dialogue, child-selected objects, optional photos, and screen labels. It does not require OCR, face/expression/pose detection, IMU sensing, non-speech audio detection, or before/after state comparison. |
| 2 | Hook & Transition | PASS | Step 1 turns nearby objects into a tiny gallery and invites the child to choose the organizing idea. |
| 3 | Edge Case Coverage | PASS | Every dialogue step includes ideal, unexpected, and no-response branches with 2s waits; Step 3 includes rule changes, favorite-object detours, and mixed-object handling. |
| 4 | IB Completeness | PASS | Connection and Form are named, KUD is specific, related concepts and ATL skills are present, and the closing links curation to rule-based grouping. |
| 5 | Tier Appropriateness | PASS | T2 children choose three or four objects, explain a rule, revise the rule if needed, and answer a visitor-style challenge. |
| 6 | Dialogue Specificity | PASS | AI lines are concrete spoken dialogue with tone markers; no runtime beat relies on abstract narrator instructions. |
| 7 | Screen & UI Completeness | PASS | Every step includes concrete screen states: blank shelf, object slots, rule ribbon, maybe shelf, final label, and badge. |
| 8 | Entity Mapping Alignment | N/A | Parameterized match-pattern package with no `mapping=` assignment and no entity-specific mapping claims. |
| 9 | Game Feel | PASS | The gallery shelf, rule reveal, maybe shelf, and visitor question create uncertainty and payoff without making the AI impose the category. |
| 10 | Mechanic Fidelity + Scaffold Honesty | PASS | `sort` is preserved in the Step 3 loop and tag block; the weak Adventure scaffold fit is disclosed and constrained to visible progress framing. |

**Overall**: ALL PASS -- Older Package Reviewer D pass confirmed after reviewing the five-file package against `program.md` Phase 3, `templates.md`, `activities/README.md`, schema constraints, and focal-attribute alignment.
