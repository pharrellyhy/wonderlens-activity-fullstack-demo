"""Convert a *_prod.md game design doc into a loadable game .md with YAML frontmatter.

Uses Gemini 2.0 Flash in JSON mode to extract structured data from the rich
markdown design document, then validates the output via game_parser.

Usage:
    uv run python scripts/convert_game.py backend/games/bicycle_cat1_prod.md
    uv run python scripts/convert_game.py backend/games/bicycle_cat1_prod.md --dry-run
    uv run python scripts/convert_game.py --all
    uv run python scripts/convert_game.py --all --dry-run
"""

import argparse
import importlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal

import httpx
import yaml
from generate_cat5_icons_gemini import (
    RETRY_DELAY,
    get_api_key_client,
    get_vertex_client,
)
from generate_cat5_icons_openai import load_env_file
from generate_game_frontmatter import (
    IB_CONCEPT_TO_THEME,
    TIER_COLLECTION_COUNT,
    TIER_CONSTRAINTS,
    extract_category,
    extract_concepts,
    extract_entity_name,
    extract_tier,
    parse_basic_info_table,
    slugify,
)
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
GAMES_DIR = ROOT / "backend" / "games"
MODEL = "gemini-3.1-pro-preview"

# Reference game files for few-shot prompting
CAT1_REFERENCE = GAMES_DIR / "mood_changer_dog.md"
CAT5_REFERENCE = GAMES_DIR / "polka_dot_patrol.md"


# ---------------------------------------------------------------------------
# Pydantic output models for Gemini JSON mode
# ---------------------------------------------------------------------------


class StepGoalOutput(BaseModel):
    goal: str = Field(description="What the AI should accomplish in this step")
    constraint: str = Field(description="Tier-appropriate constraints (sentence count, tone)")
    emotion_tag: str = Field(description="Suggested emotion tag for TTS")


class RoundInstructionOutput(BaseModel):
    round_number: int = Field(description="1-based round number")
    goal: str = Field(description="What the round explores")
    scenario: str = Field(description="The scenario presented to the child")
    constraint: str = Field(description="Tier-appropriate constraints for this round")
    emotion_tag: str = Field(description="Suggested emotion tag for this round")
    acceptable_themes: list[str] = Field(description="Loose thematic validation for child responses")
    escalation_note: str = Field(description="How this round fits the escalation arc")


class StepInstructionsOutput(BaseModel):
    hook: StepGoalOutput
    transition: StepGoalOutput
    rounds: list[RoundInstructionOutput]
    celebrate: StepGoalOutput
    closing: StepGoalOutput
    early_exit: StepGoalOutput


class Cat5StepInstructionsOutput(StepInstructionsOutput):
    synthesis: StepGoalOutput


class ScreenFrameOutput(BaseModel):
    widget: str = Field(description="Widget primitive ID: photo_display, character_display, or progress_tracker")
    widget_params: dict = Field(description="Widget-specific parameters")
    animation: str = Field(description="Animation preset")
    trigger: str = Field(description="on_enter | on_round_N | on_correct")
    sfx_cue: str = Field(description="Sound effect ID")
    widget_label: str = Field(description="Human-readable widget description")
    animation_label: str = Field(description="Human-readable animation description")


class CelebrationFrameOutput(BaseModel):
    widget: str = Field(description="Always badge_award")
    widget_params: dict = Field(description="title and concepts")
    animation: str = Field(description="Always badge_reveal")
    trigger: str = Field(description="Always on_correct")
    sfx_cue: str = Field(description="Always badge_awarded")
    widget_label: str = Field(description="Always 'Badge Earned!'")
    animation_label: str = Field(description="Always 'Badge reveal'")


class Cat1CreativeSlotsOutput(BaseModel):
    game_mechanic: Literal[
        "mood_guessing",
        "true_or_silly",
        "voice_acting",
        "storytelling_chain",
        "riddle_game",
        "sound_imitation",
        "prediction_game",
        "helper_hotline",
    ] = Field(description="Game mechanic chosen based on entity category")
    metaphor: str = Field(description="Playful imaginative frame for the entity")
    role_title: str = Field(description="Fun title awarded to the child at the end")
    round_scenarios: list[str] = Field(description="One scenario per dialogue round, escalating in complexity")
    escalation_axis: str = Field(description="How rounds increase in difficulty")
    observation_detail: str = Field(description="Specific visual detail from the photo to anchor the hook")


class Cat5CreativeSlotsOutput(BaseModel):
    observation_angle: Literal[
        "color",
        "shape",
        "texture",
        "size",
        "pattern",
        "function",
        "habitat",
        "form",
        "movement",
        "smell",
    ] = Field(description="Visual/sensory feature to anchor the collection mission")
    collection_criterion: str = Field(description="Specific rule for what to collect")
    collection_count: int = Field(ge=2, le=4, description="Number of items to find")
    mission_metaphor: str = Field(description="Playful frame for the collection mission")
    role_title: str = Field(description="Fun title awarded at the end")
    synthesis_type: Literal[
        "naming_story",
        "comparison_chart",
        "creative_narrative",
        "sorting_game",
    ] = Field(description="Creative activity for the collected items")
    stuck_hint: str = Field(description="Hint for where to look if the child is stuck")
    naming_prompt: str = Field(description="Prompt for child to name/characterize each collected item")
    detail_question_template: str = Field(
        description="Detail-harvesting question asked after each correct photo pick (Phase B of 2-phase collection loop)"
    )
    sorting_criterion: str = Field(
        default="",
        description="For comparison_chart synthesis: criterion to sort/rank finds by (e.g. 'dot size'). Empty for naming_story.",
    )


class CollectionItemOutput(BaseModel):
    id: str = Field(description="Snake_case item ID")
    label: str = Field(description="Human-readable label")
    image: str = Field(description="Icon path like /icons/spotted_mushroom.png")


class CollectionCatalogOutput(BaseModel):
    correct: list[CollectionItemOutput] = Field(description="4 correct collection items")
    distractors: list[CollectionItemOutput] = Field(description="8 distractor items")


class Cat1GameFrontmatter(BaseModel):
    activity_type: str
    entity_name: str
    category: Literal["category_1"]
    display_label: str
    tier: Literal["T0", "T1", "T2"]
    ib_theme: str
    ib_key_concept: str
    concepts_earned: list[str]
    keywords: list[str]
    feature_keywords: list[str]
    photo_features: list[str]
    creative_slots: Cat1CreativeSlotsOutput
    step_instructions: StepInstructionsOutput
    screen_frames: list[ScreenFrameOutput]
    celebration_frame: CelebrationFrameOutput


class Cat5GameFrontmatter(BaseModel):
    activity_type: str
    entity_name: str
    category: Literal["category_5"]
    display_label: str
    tier: Literal["T0", "T1", "T2"]
    ib_theme: str
    ib_key_concept: str
    concepts_earned: list[str]
    keywords: list[str]
    feature_keywords: list[str]
    photo_features: list[str]
    creative_slots: Cat5CreativeSlotsOutput
    collection_catalog: CollectionCatalogOutput
    step_instructions: Cat5StepInstructionsOutput
    screen_frames: list[ScreenFrameOutput]
    celebration_frame: CelebrationFrameOutput


# ---------------------------------------------------------------------------
# Reference YAML extraction
# ---------------------------------------------------------------------------


def _extract_yaml_frontmatter(path: Path) -> str:
    """Extract raw YAML frontmatter text from a game .md file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError(f"No YAML frontmatter in {path}")
    return match.group(1)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_prompt(
    prod_content: str,
    category: str,
    entity_name: str,
    info: dict[str, str],
    reference_yaml: str,
    schema_json: str,
    tier: str,
) -> str:
    """Build the system + user prompt for Gemini JSON mode extraction."""
    activity_name = info.get("Activity Name", "")
    activity_slug = slugify(activity_name)
    activity_type = f"{activity_slug}_{entity_name}" if entity_name not in activity_slug else activity_slug
    concepts = extract_concepts(info.get("Core IB Key Concepts", ""))
    first_concept = concepts[0] if concepts else "Perspective"
    ib_theme = IB_CONCEPT_TO_THEME.get(first_concept, "Who We Are")
    constraint = TIER_CONSTRAINTS.get(tier, "T1 max 3 sentences")

    cat_specific = ""
    if category == "category_5":
        default_count = TIER_COLLECTION_COUNT.get(tier, 3)
        cat_specific = f"""
Category 5 specific rules:
- collection_catalog must have exactly 4 correct items and exactly 8 distractors
- Each item needs id (snake_case), label, and image path as /icons/{{snake_case_id}}.png
- Items should be things a child could find outdoors that match the collection_criterion
- step_instructions MUST include a 'synthesis' step (comparison of collected items)
- screen_frames: 1 photo_display (trigger: on_enter) + 1 progress_tracker per round
- progress_tracker widget_params: filled (1-based) and total (collection_count + 1 for the photo)
- collection_count default for this tier: {default_count}
"""
    else:
        cat_specific = """
Category 1 specific rules:
- step_instructions does NOT have a 'synthesis' step
- screen_frames: 1 photo_display (trigger: on_enter) + 1 character_display per round
- character_display widget_params should include a 'description' field
"""

    # Map game_mechanic and observation_angle literals for reference
    game_mechanic_values = (
        "mood_guessing, true_or_silly, voice_acting, storytelling_chain, "
        "riddle_game, sound_imitation, prediction_game, helper_hotline"
    )
    observation_angle_values = "color, shape, texture, size, pattern, function, habitat, form, movement, smell"
    synthesis_type_values = "naming_story, comparison_chart, creative_narrative, sorting_game"

    return f"""You are a game design structured data extractor for WonderLens Activity Demo.

Your task: extract structured YAML frontmatter data from a game design document.
Output MUST be valid JSON matching the provided schema exactly.

CRITICAL RULES:
- entity_name: "{entity_name}" (derived from filename)
- activity_type: "{activity_type}" (slugified activity name + entity)
- category: "{category}"
- tier: "{tier}"
- ib_theme: "{ib_theme}" (derived from first concept "{first_concept}")
- ib_key_concept: "{first_concept}"
- concepts_earned: {json.dumps(concepts)}
- Tier constraint: "{constraint}"
- game_mechanic must be one of: {game_mechanic_values}
- observation_angle must be one of: {observation_angle_values}
- synthesis_type must be one of: {synthesis_type_values}
- Use invitational language in goals: "Would you like to...?" not "Go find!"
- All goals and constraints should be substantive, not placeholder text
- acceptable_themes should contain 5-8 relevant keywords per round
- screen_frames animation values: sparkle_highlight, gentle_pulse, scene_transition, card_slide_in, celebration_burst
- screen_frames sfx_cue values: wonder_chime, scene_woosh, photo_shutter_click, celebration_fanfare, mission_complete_fanfare
- celebration_frame is always: widget=badge_award, animation=badge_reveal, trigger=on_correct, sfx_cue=badge_awarded
{cat_specific}

REFERENCE EXAMPLE (same category game, use as a structural template):
```yaml
{reference_yaml}
```

JSON SCHEMA to follow:
```json
{schema_json}
```

GAME DESIGN DOCUMENT TO CONVERT:
```markdown
{prod_content}
```

Extract ALL structured data from the design document. Fill in every field with appropriate content derived from the document. Do NOT use placeholder or TODO text."""


# ---------------------------------------------------------------------------
# Gemini call with retry
# ---------------------------------------------------------------------------


def _call_gemini(
    client,
    prompt: str,
    model_class: type[BaseModel],
    max_attempts: int = 3,
) -> BaseModel:
    """Call Gemini in JSON mode, validate with Pydantic, retry on failure."""
    full_prompt = prompt

    delay = RETRY_DELAY
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            raw_text = response.text
            data = json.loads(raw_text)
            result = model_class.model_validate(data)
            return result

        except json.JSONDecodeError as exc:
            last_error = exc
            print(f"  JSON parse error (attempt {attempt + 1}/{max_attempts}): {exc}")
            if attempt < max_attempts - 1:
                time.sleep(2)

        except Exception as exc:
            if isinstance(exc, (genai_errors.ClientError, genai_errors.APIError, httpx.ConnectError)):
                is_retryable = (
                    "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc) or isinstance(exc, httpx.ConnectError)
                )
                if is_retryable and attempt < max_attempts - 1:
                    print(f"  rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})...")
                    time.sleep(delay)
                    delay = min(delay * 2, 120)
                    continue

            # Pydantic validation error — retry with error context appended
            last_error = exc
            error_msg = str(exc)
            print(f"  validation error (attempt {attempt + 1}/{max_attempts}): {error_msg[:200]}")
            if attempt < max_attempts - 1:
                full_prompt = (
                    prompt
                    + f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR:\n{error_msg}\n\nPlease fix the issues and try again."
                )
                time.sleep(2)

    raise RuntimeError(f"Failed after {max_attempts} attempts. Last error: {last_error}")


# ---------------------------------------------------------------------------
# YAML serialization
# ---------------------------------------------------------------------------


def _represent_short_list(dumper: yaml.Dumper, data: list) -> yaml.Node:
    """Represent short lists (all scalars, ≤8 items) inline."""
    if len(data) <= 8 and all(isinstance(item, (str, int, float, bool)) for item in data):
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=False)


def _model_to_yaml(model: BaseModel) -> str:
    """Convert a Pydantic model to YAML frontmatter string."""
    data = model.model_dump()

    dumper = yaml.Dumper
    dumper.add_representer(list, _represent_short_list)

    yaml_text = yaml.dump(
        data,
        Dumper=dumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
    return f"---\n{yaml_text}---\n"


# ---------------------------------------------------------------------------
# Validation via game_parser
# ---------------------------------------------------------------------------


def _parse_game_file(path: Path) -> None:
    """Call backend game_parser.parse_game_file via importlib to avoid static import issues."""
    if str(ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend"))
    module = importlib.import_module("game_parser")
    module.parse_game_file(path)


def _validate_output(output_path: Path) -> bool:
    """Validate the generated game file via game_parser."""
    try:
        _parse_game_file(output_path)
        return True
    except Exception as exc:
        print(f"  validation failed: {exc}", file=sys.stderr)
        return False


def _validate_rendered_output(content: str, filename: str) -> bool:
    """Validate rendered markdown content via a temporary game file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / filename
        output_path.write_text(content, encoding="utf-8")
        return _validate_output(output_path)


# ---------------------------------------------------------------------------
# Core conversion logic
# ---------------------------------------------------------------------------


def convert_prod_file(
    input_path: Path,
    output_path: Path | None,
    client,
    dry_run: bool = False,
) -> Path | None:
    """Convert a single prod.md file to a game .md with YAML frontmatter."""
    content = input_path.read_text(encoding="utf-8")
    info = parse_basic_info_table(content)

    entity_name = extract_entity_name(input_path)
    category_text = info.get("Activity Category", "")
    tier_text = info.get("Recommended Tier", "")
    category = extract_category(category_text)
    tier = extract_tier(tier_text)

    activity_name = info.get("Activity Name", "")
    activity_slug = slugify(activity_name)
    activity_type = f"{activity_slug}_{entity_name}" if entity_name not in activity_slug else activity_slug

    # Choose reference and model class
    if category == "category_5":
        reference_path = CAT5_REFERENCE
        model_class = Cat5GameFrontmatter
    else:
        reference_path = CAT1_REFERENCE
        model_class = Cat1GameFrontmatter

    reference_yaml = _extract_yaml_frontmatter(reference_path)
    schema_json = json.dumps(model_class.model_json_schema(), indent=2)
    prompt = _build_prompt(
        prod_content=content,
        category=category,
        entity_name=entity_name,
        info=info,
        reference_yaml=reference_yaml,
        schema_json=schema_json,
        tier=tier,
    )

    print(f"Converting {input_path.name} → {category} ({entity_name})...")
    result = _call_gemini(client, prompt, model_class)

    yaml_text = _model_to_yaml(result)
    full_output = yaml_text + "\n" + content

    if dry_run:
        if _validate_rendered_output(full_output, f"{activity_type}.md"):
            print("  validation passed (dry run)", file=sys.stderr)
        else:
            print("  WARNING: validation failed during dry run", file=sys.stderr)
        print(full_output)
        return None

    if output_path is None:
        output_path = GAMES_DIR / f"{activity_type}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_output, encoding="utf-8")
    print(f"  wrote {output_path.name}")

    if _validate_output(output_path):
        print("  validation passed")
    else:
        print("  WARNING: validation failed — review the output file", file=sys.stderr)

    return output_path


# ---------------------------------------------------------------------------
# Client creation
# ---------------------------------------------------------------------------


def _get_client(env: dict[str, str], mode: str):
    """Create a Gemini client based on mode."""
    if mode == "vertex":
        return get_vertex_client(env)
    if mode == "api-key":
        return get_api_key_client(env)
    # auto: try vertex first
    try:
        return get_vertex_client(env)
    except RuntimeError:
        return get_api_key_client(env)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a *_prod.md game design doc into a loadable game file with YAML frontmatter.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=None,
        help="Path to a *_prod.md game design file",
    )
    parser.add_argument("--output", type=Path, default=None, help="Custom output path")
    parser.add_argument("--all", action="store_true", help="Process all *_prod.md files in backend/games/")
    parser.add_argument("--dry-run", action="store_true", help="Print output to stdout, don't write files")
    parser.add_argument("--mode", default="auto", choices=("auto", "vertex", "api-key"), help="Gemini client mode")
    args = parser.parse_args()

    if not args.all and args.input is None:
        parser.error("Either provide an input file or use --all")

    if not ENV_PATH.exists():
        print(f"Error: {ENV_PATH} not found", file=sys.stderr)
        sys.exit(1)

    env = load_env_file(ENV_PATH)
    client = _get_client(env, args.mode)

    if args.all:
        prod_files = sorted(GAMES_DIR.glob("*_prod.md"))
        if not prod_files:
            print("No *_prod.md files found in backend/games/", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(prod_files)} prod files to convert\n")
        for i, prod_file in enumerate(prod_files):
            convert_prod_file(prod_file, output_path=None, client=client, dry_run=args.dry_run)
            if i < len(prod_files) - 1:
                print()
    else:
        input_path = args.input.resolve()
        if not input_path.exists():
            print(f"Error: {input_path} does not exist", file=sys.stderr)
            sys.exit(1)
        convert_prod_file(input_path, output_path=args.output, client=client, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
