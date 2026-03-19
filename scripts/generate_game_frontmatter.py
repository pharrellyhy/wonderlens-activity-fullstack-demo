#!/usr/bin/env python3
"""CLI tool to scaffold YAML frontmatter from a *_prod.md game design doc.

Usage:
    python scripts/generate_game_frontmatter.py backend/games/lion_cat5_prod.md
    python scripts/generate_game_frontmatter.py backend/games/bicycle_cat1_prod.md --output backend/games/wheels_and_feelings_bicycle.md
"""

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# IB concept → theme mapping
# ---------------------------------------------------------------------------
IB_CONCEPT_TO_THEME: dict[str, str] = {
    "Perspective": "Who We Are",
    "Reflection": "Who We Are",
    "Change": "How the World Works",
    "Causation": "How the World Works",
    "Form": "How We Express Ourselves",
    "Connection": "Sharing the Planet",
    "Function": "How the World Works",
    "Responsibility": "Sharing the Planet",
}

# Category text → frontmatter value
CATEGORY_MAP: dict[str, str] = {
    "collection": "category_5",
    "tracking": "category_5",
    "sustained verbal": "category_1",
    "in-device": "category_1",
}

# Tier text → frontmatter value
TIER_MAP: dict[str, str] = {
    "T0": "T0",
    "T1": "T1",
    "T2": "T2",
}

# Tier → max constraint sentences
TIER_CONSTRAINTS: dict[str, str] = {
    "T0": "T0 max 2 sentences",
    "T1": "T1 max 3 sentences",
    "T2": "T2 max 3 sentences",
}

# Tier → collection count default
TIER_COLLECTION_COUNT: dict[str, int] = {
    "T0": 2,
    "T1": 3,
    "T2": 3,
}


@dataclass
class GeneratedFrontmatter:
    """Generated frontmatter text plus extracted summary fields."""

    frontmatter: str
    activity_type: str
    info: dict[str, str]
    category: str
    entity_name: str
    role_title: str
    round_scenarios: list[str]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
def parse_basic_info_table(content: str) -> dict[str, str]:
    """Extract field→value pairs from the Basic Info markdown table."""
    info: dict[str, str] = {}
    for match in re.finditer(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|", content):
        field = match.group(1).strip()
        value = match.group(2).strip()
        if field in ("Field", "-------", "---"):
            continue
        info[field] = value
    return info


def extract_entity_name(filepath: Path) -> str:
    """Derive entity_name from filename: lion_cat5_prod.md → lion."""
    stem = filepath.stem  # e.g. lion_cat5_prod
    # Strip _cat[15]_prod suffix
    entity = re.sub(r"_cat\d+_prod$", "", stem)
    return entity


def extract_category(category_text: str) -> str:
    """Map Activity Category text to category_1 or category_5."""
    lower = category_text.lower()
    for key, value in CATEGORY_MAP.items():
        if key in lower:
            return value
    return "category_1  # TODO: confirm category"


def extract_tier(tier_text: str) -> str:
    """Extract tier from 'T0 (ages 2-4)' style text."""
    for key in TIER_MAP:
        if key in tier_text:
            return key
    return "T0  # TODO: confirm tier"


def extract_concepts(concepts_text: str) -> list[str]:
    """Parse 'Form, Function' into ['Form', 'Function']."""
    return [c.strip() for c in concepts_text.split(",") if c.strip()]


def derive_ib_theme(concepts: list[str]) -> tuple[str, str]:
    """Return (theme, first_concept) from IB concept list."""
    if not concepts:
        return '"Who We Are"  # TODO: confirm theme', "Perspective  # TODO"
    first = concepts[0]
    theme = IB_CONCEPT_TO_THEME.get(first, "")
    if theme:
        return f'"{theme}"  # auto-derived from {first}', first
    return f'"Who We Are"  # TODO: confirm theme (unknown concept: {first})', first


def slugify(text: str) -> str:
    """Convert activity name to a slug: 'The Brave Things Hunt' → 'brave_things_hunt'."""
    # Remove leading articles
    slug = re.sub(r"^(the|a|an)\s+", "", text.lower())
    # Replace non-alphanum with underscores
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def _clean_role_title(title: str) -> str:
    """Normalize an extracted role title."""
    cleaned = re.sub(r"\s+", " ", title).strip(" \"'!.:,;")
    cleaned = re.sub(
        r"^(?:the\s+best\s+|the\s+great\s+|great\s+|best\s+|official\s+|true\s+|real\s+)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.title()


def extract_role_title(content: str) -> str:
    """Try to extract the role title from celebration/closing prose."""
    # Prefer explicit celebration/badge titles over softer closing compliments.
    patterns = [
        r'(?:you are\s+)?officially\s+(?:a|an)?\s*(?:\.\.\.?\s*)?["\']?([A-Za-z][A-Za-z\s\-]+?)["\']?!',
        r'earned (?:your |the )["\']?([A-Za-z][A-Za-z\s\-]+?)["\']?\s+badge',
        r'becomes?\s+(?:a|an)\s+["\']?([A-Za-z][A-Za-z\s\-]+?)["\']?(?:\s+who|\s+on\b|\s+and\b|\s*—|\s*\.)',
        r'"([A-Z][A-Z\s\-]+)".*badge',
    ]
    for pat in patterns:
        match = re.search(pat, content, re.IGNORECASE)
        if match:
            return _clean_role_title(match.group(1))
    return ""


def extract_round_scenarios(content: str) -> list[str]:
    """Extract round scenario labels from Step 3 headings."""
    scenarios = []
    # Match patterns like: **Round 1 — "Zooming Downhill":**, Round 1 — First Find:
    for match in re.finditer(
        r"\*\*Round\s+\d+\s*[—–-]\s*(?:[\"']?(.+?)[\"']?\s*(?::\s*)?\*\*|(.+?):\s*\*\*)",
        content,
    ):
        scenario = (match.group(1) or match.group(2) or "").strip().rstrip(":")
        if scenario:
            scenarios.append(scenario)
    return scenarios


def _collection_search_space(content: str) -> str:
    """Limit collection extraction to the overview and early setup sections."""
    return content.split("#### Step 3", maxsplit=1)[0]


def _clean_collection_phrase(phrase: str) -> str:
    """Trim examples and follow-on instructions from a collection criterion phrase."""
    cleaned = re.sub(r"\s*\([^)]*\)", "", phrase)
    cleaned = re.sub(
        r"\s*(?:,| and )\s*(?:photograph|photo(?:graph)?|take|describe|compare|sort|figure|we\s+compare)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \"'.,;:!?")
    return cleaned


def extract_collection_count(content: str, default_count: int) -> int:
    """Extract the requested number of collection finds from overview or mission text."""
    search_space = _collection_search_space(content)
    match = re.search(r"\b(?:find|for)\s+(\d+)\s+things?\b", search_space, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return default_count


def extract_mission_metaphor(content: str, role_title: str) -> str:
    """Try to extract the mission metaphor from rule introduction prose."""
    match = re.search(r'"(You are (?:a |an ).+?)"', content)
    if match:
        return match.group(1)
    if role_title:
        return f"You are a {role_title}!"
    return ""


def extract_collection_criterion(content: str) -> str:
    """Try to extract what to collect from Step 2 prose."""
    search_space = _collection_search_space(content)
    patterns = [
        r"\bfor\s+\d+\s+things?\s+that\s+(.+?)(?:\.|!|\")",
        r"\bfind\s+\d+\s+things?\s+outside\s+that\s+(.+?)(?:\.|!|\")",
        r"\bfind\s+\d+\s+things?\s+that\s+(.+?)(?:\.|!|\")",
        r"\bfind\s+\d+\s+(.+?)\s+things(?:\.|!|\")",
        r"\bfind\s+\d+\s+(.+?)(?:\.|!|\")",
    ]

    for pattern in patterns:
        match = re.search(pattern, search_space, re.IGNORECASE)
        if not match:
            continue

        phrase = _clean_collection_phrase(match.group(1))
        if not phrase:
            continue

        if phrase.startswith(("look ", "have ", "protect ", "match ", "help ", "make ", "are ")):
            return f"Find things that {phrase}"
        return f"Find {phrase}"
    return ""


# ---------------------------------------------------------------------------
# Frontmatter generation
# ---------------------------------------------------------------------------
def generate_cat1_frontmatter(
    activity_type: str,
    entity_name: str,
    display_label: str,
    tier: str,
    ib_theme: str,
    ib_key_concept: str,
    concepts_earned: list[str],
    game_mechanic: str,
    role_title: str,
    round_scenarios: list[str],
    constraint: str,
) -> str:
    """Generate YAML frontmatter for a Category 1 game."""
    concepts_yaml = "[" + ", ".join(concepts_earned) + "]"
    scenarios_yaml = (
        "\n".join(f"    - {s}" for s in round_scenarios) if round_scenarios else "    - # TODO: add round scenarios"
    )

    rounds_yaml = ""
    for i, scenario in enumerate(round_scenarios or ["# TODO"], start=1):
        rounds_yaml += textwrap.dedent(f"""\
    - round_number: {i}
      goal: ""  # TODO: write round {i} goal
      scenario: "{scenario}"
      constraint: "{constraint}"
      emotion_tag: {"warm" if i == 1 else "curious" if i == 2 else "excited"}  # TODO: confirm
      acceptable_themes: []  # TODO: add acceptable themes
      escalation_note: ""  # TODO: describe escalation
""")

    return textwrap.dedent(f"""\
---
activity_type: {activity_type}  # TODO: confirm activity_type
entity_name: {entity_name}
category: category_1
display_label: {display_label}
tier: {tier}
ib_theme: {ib_theme}
ib_key_concept: {ib_key_concept}
concepts_earned: {concepts_yaml}
keywords: [{entity_name}]  # TODO: add more keywords for vision matching
feature_keywords: []  # TODO: add feature keywords
photo_features: []  # TODO: add visible features from photo

creative_slots:
  game_mechanic: {game_mechanic}
  metaphor: ""  # TODO: write playful imaginative frame
  role_title: {role_title or "# TODO: extract role title"}
  round_scenarios:
{scenarios_yaml}
  escalation_axis: ""  # TODO: describe how rounds escalate
  observation_detail: ""  # TODO: specific visual detail from the photo

step_instructions:
  hook:
    goal: ""  # TODO: write hook goal
    constraint: "{constraint}, personal feeling hook, MUST end with an emotional question"
    emotion_tag: excited
  transition:
    goal: ""  # TODO: write transition goal introducing the {game_mechanic} game
    constraint: "{constraint}, demo round WITH answer included, end with Would you like to try?"
    emotion_tag: playful
  rounds:
{textwrap.indent(rounds_yaml, "    ")}  celebrate:
    goal: ""  # TODO: write celebration goal awarding "{role_title}" title
    constraint: "{constraint}, announce role title ceremonially, reference specific moments"
    emotion_tag: proud
  closing:
    goal: ""  # TODO: teach IB concepts ({", ".join(concepts_earned)}) naturally connected to experience
    constraint: "{constraint}, name concepts naturally, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: ""  # TODO: gentle goodbye validating whatever they did
    constraint: "{constraint}, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: ""  # TODO: describe entity photo display
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: ""  # TODO: add widget label
    animation_label: "Sparkle highlight"
  # TODO: add character_display frames for each round

celebration_frame:
  widget: badge_award
  widget_params:
    title: "{role_title}"
    concepts: {concepts_yaml}
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---
""")


def generate_cat5_frontmatter(
    activity_type: str,
    entity_name: str,
    display_label: str,
    tier: str,
    ib_theme: str,
    ib_key_concept: str,
    concepts_earned: list[str],
    synthesis_type: str,
    role_title: str,
    round_scenarios: list[str],
    collection_count: int,
    constraint: str,
    mission_metaphor: str,
    collection_criterion: str,
) -> str:
    """Generate YAML frontmatter for a Category 5 game."""
    concepts_yaml = "[" + ", ".join(concepts_earned) + "]"

    rounds_yaml = ""
    for i in range(1, collection_count + 1):
        scenario = round_scenarios[i - 1] if i <= len(round_scenarios) else f"collection find {i}"
        rounds_yaml += textwrap.dedent(f"""\
    - round_number: {i}
      goal: ""  # TODO: write round {i} goal
      scenario: "{scenario}"
      constraint: "{constraint}, invitational phrasing"
      emotion_tag: {"encouraging" if i == 1 else "curious" if i == 2 else "excited"}
      acceptable_themes: []  # TODO: add acceptable themes
      escalation_note: ""  # TODO: describe escalation
""")

    return textwrap.dedent(f"""\
---
activity_type: {activity_type}  # TODO: confirm activity_type
entity_name: {entity_name}
category: category_5
display_label: {display_label}
tier: {tier}
ib_theme: {ib_theme}
ib_key_concept: {ib_key_concept}
concepts_earned: {concepts_yaml}
keywords: [{entity_name}]  # TODO: add more keywords for vision matching
feature_keywords: []  # TODO: add feature keywords
photo_features: []  # TODO: add visible features from photo

creative_slots:
  observation_angle: form  # TODO: confirm observation angle (color/shape/texture/size/pattern/function/habitat/form/movement/smell)
  collection_criterion: "{collection_criterion or "# TODO: describe what to collect"}"
  collection_count: {collection_count}
  mission_metaphor: "{mission_metaphor or "# TODO: write mission metaphor"}"
  role_title: {role_title or "# TODO: extract role title"}
  synthesis_type: {synthesis_type}
  stuck_hint: ""  # TODO: write stuck hint
  naming_prompt: ""  # TODO: write naming prompt

collection_catalog:
  correct:
    - id: # TODO: add correct collection items
      label: ""
      image: /icons/.png
  distractors:
    - id: # TODO: add distractor items
      label: ""
      image: /icons/.png

step_instructions:
  hook:
    goal: ""  # TODO: write hook goal
    constraint: "{constraint}, experience/preference hook"
    emotion_tag: excited
  transition:
    goal: ""  # TODO: write transition goal introducing the collection mission
    constraint: "{constraint}, build mission from child's response, frame as invitation"
    emotion_tag: playful
  rounds:
{textwrap.indent(rounds_yaml, "    ")}  celebrate:
    goal: ""  # TODO: write celebration goal awarding "{role_title}" title
    constraint: "{constraint}, announce role title ceremonially, reference specific finds"
    emotion_tag: proud
  closing:
    goal: ""  # TODO: teach IB concepts ({", ".join(concepts_earned)}) naturally connected to discoveries
    constraint: "{constraint}, name concepts naturally, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: ""  # TODO: write synthesis goal (compare collected items)
    constraint: "{constraint}, comparison + creative naming, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: ""  # TODO: gentle goodbye validating patrol work
    constraint: "{constraint}, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: ""  # TODO: describe entity photo display
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: ""  # TODO: add widget label
    animation_label: "Sparkle highlight"
  # TODO: add progress_tracker frames for each round

celebration_frame:
  widget: badge_award
  widget_params:
    title: "{role_title}"
    concepts: {concepts_yaml}
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_frontmatter(input_path: Path, content: str) -> GeneratedFrontmatter:
    """Build generated frontmatter and extracted summary data for a prod doc."""
    info = parse_basic_info_table(content)

    entity_name = extract_entity_name(input_path)
    activity_name = info.get("Activity Name", "")
    category_text = info.get("Activity Category", "")
    tier_text = info.get("Recommended Tier", "")
    concepts_text = info.get("Core IB Key Concepts", "")
    game_style = info.get("Game Style", "")

    category = extract_category(category_text)
    tier = extract_tier(tier_text)
    concepts = extract_concepts(concepts_text)
    ib_theme, ib_key_concept = derive_ib_theme(concepts)
    display_label = entity_name.replace("_", " ").title()
    role_title = extract_role_title(content)
    round_scenarios = extract_round_scenarios(content)

    activity_slug = slugify(activity_name)
    activity_type = f"{activity_slug}_{entity_name}" if entity_name not in activity_slug else activity_slug
    constraint = TIER_CONSTRAINTS.get(tier, "T1 max 3 sentences")

    if category == "category_5":
        default_count = TIER_COLLECTION_COUNT.get(tier, 3)
        collection_count = extract_collection_count(content, default_count)
        frontmatter = generate_cat5_frontmatter(
            activity_type=activity_type,
            entity_name=entity_name,
            display_label=display_label,
            tier=tier,
            ib_theme=ib_theme,
            ib_key_concept=ib_key_concept,
            concepts_earned=concepts,
            synthesis_type=game_style,
            role_title=role_title,
            round_scenarios=round_scenarios,
            collection_count=collection_count,
            constraint=constraint,
            mission_metaphor=extract_mission_metaphor(content, role_title),
            collection_criterion=extract_collection_criterion(content),
        )
    else:
        frontmatter = generate_cat1_frontmatter(
            activity_type=activity_type,
            entity_name=entity_name,
            display_label=display_label,
            tier=tier,
            ib_theme=ib_theme,
            ib_key_concept=ib_key_concept,
            concepts_earned=concepts,
            game_mechanic=game_style,
            role_title=role_title,
            round_scenarios=round_scenarios,
            constraint=constraint,
        )

    return GeneratedFrontmatter(
        frontmatter=frontmatter,
        activity_type=activity_type,
        info=info,
        category=category,
        entity_name=entity_name,
        role_title=role_title,
        round_scenarios=round_scenarios,
    )


def process_prod_file(input_path: Path, output_path: Path | None = None) -> Path:
    """Read a prod MD file, generate frontmatter, write output."""
    content = input_path.read_text(encoding="utf-8")
    generated = build_frontmatter(input_path, content)

    # Determine output path
    if output_path is None:
        output_path = input_path.parent / f"{generated.activity_type}.md"

    # Write output: frontmatter + original prose
    output_content = generated.frontmatter + content
    output_path.write_text(output_content, encoding="utf-8")

    return output_path


def print_summary(
    output_path: Path,
    info: dict[str, str],
    category: str,
    entity_name: str,
    role_title: str,
    round_scenarios: list[str],
) -> None:
    """Print a summary of extracted vs TODO fields."""
    is_cat5 = category == "category_5"

    print("\n" + "=" * 60)
    print(f"  Generated: {output_path}")
    print("=" * 60)

    print("\n  EXTRACTED (auto-filled):")
    print(f"    entity_name:      {entity_name}")
    print(f"    category:         {category}")
    print(f"    tier:             {info.get('Recommended Tier', '?')}")
    print(f"    ib_key_concept:   {info.get('Core IB Key Concepts', '?')}")
    print(f"    game_style:       {info.get('Game Style', '?')}")
    if role_title:
        print(f"    role_title:       {role_title}")
    if round_scenarios:
        print(f"    round_scenarios:  {round_scenarios}")

    print("\n  TODO (needs manual authoring):")
    print("    - keywords, feature_keywords, photo_features")
    if is_cat5:
        print("    - collection_catalog (correct items + distractors)")
        print("    - observation_angle, collection_criterion, stuck_hint, naming_prompt")
    else:
        print("    - metaphor, observation_detail, escalation_axis")
    print("    - step_instructions (goals for each step)")
    print("    - screen_frames (widget/animation choices)")
    if not role_title:
        print("    - role_title (could not auto-extract)")
    if not round_scenarios:
        print("    - round_scenarios (could not auto-extract)")

    print("\n  NEXT STEPS:")
    print(f"    1. Review and fill in all # TODO fields in {output_path}")
    print(f"    2. Place entity icon at frontend/public/icons/{entity_name}.png")
    print("    3. Add entity to FALLBACK_CATEGORIES in frontend/src/components/PhotoSelector.jsx")
    print("    4. (Optional) Create React SVG icon in frontend/src/icons/")

    if is_cat5:
        print("\n  Cat5 game detected! After filling in the collection_catalog, you'll need to:")
        print("    1. Add collection item prompts to scripts/generate_cat5_icons_openai.py ASSETS")
        print("    2. Run: python scripts/generate_cat5_icons_gemini.py --mode auto --overwrite")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate YAML frontmatter for a prod game design doc",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a *_prod.md game design file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: auto-derived from activity name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print frontmatter to stdout without writing a file",
    )
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        print(f"Error: {input_path} does not exist", file=sys.stderr)
        sys.exit(1)

    if not input_path.name.endswith("_prod.md"):
        print(f"Warning: {input_path.name} does not match *_prod.md pattern", file=sys.stderr)

    content = input_path.read_text(encoding="utf-8")
    generated = build_frontmatter(input_path, content)

    if args.dry_run:
        print(generated.frontmatter)
        return

    output_path = process_prod_file(input_path, args.output)
    print_summary(
        output_path,
        generated.info,
        generated.category,
        generated.entity_name,
        generated.role_title,
        generated.round_scenarios,
    )


if __name__ == "__main__":
    main()
