#!/usr/bin/env python3
"""Generate character animation video clips using Veo 3.1 via Vertex AI.

Reads prompt templates from tools/character_clip_prompts.yaml and generates
MP4 clips for each character × state combination.

Usage:
    # Preview all prompts without calling the API
    uv run python tools/generate_character_clips.py --dry-run

    # Generate all 24 clips
    uv run python tools/generate_character_clips.py

    # Generate clips for a specific character
    uv run python tools/generate_character_clips.py --character mood_changer_dog

    # Generate a specific state for a specific character
    uv run python tools/generate_character_clips.py --character mood_changer_dog --state excited
"""

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml
from google import genai
from google.genai import types

PROMPTS_FILE = Path(__file__).parent / "character_clip_prompts.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "public" / "video" / "character"
VEO_MODEL = "veo-3.1-fast-generate-001"
ASPECT_RATIO = "16:9"
POLL_INTERVAL_S = 20
MAX_POLL_S = 600
REFERENCE_STATE = "idle"  # Generated first, used as style reference for remaining states


def load_prompts() -> dict:
    """Load prompt templates from YAML."""
    with open(PROMPTS_FILE) as f:
        return yaml.safe_load(f)


def build_prompt(config: dict, character_key: str, state: str) -> str:
    """Build a full prompt from base + state-specific action."""
    char_config = config["characters"][character_key]
    state_config = char_config["states"][state]
    defaults = config["defaults"]

    prompt_parts = [
        char_config["base"].strip(),
        state_config["action"].strip(),
        defaults["style"].strip(),
    ]
    return " ".join(prompt_parts)


def get_duration_seconds(config: dict, state: str, character_key: str) -> int:
    """Get duration in seconds for the state. Veo supports 4, 6, or 8."""
    return 8


def extract_frame(video_path: Path) -> types.Image | None:
    """Extract the first frame from a video as a reference image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vframes", "1", "-q:v", "2", tmp_path],
        capture_output=True,
    )
    if result.returncode != 0 or not Path(tmp_path).exists():
        print(f"    Warning: could not extract frame from {video_path}")
        return None
    image = types.Image.from_file(location=tmp_path)
    Path(tmp_path).unlink(missing_ok=True)
    return image


def generate_clip(
    client: genai.Client, prompt: str, output_path: Path, duration_s: int, ref_image: types.Image | None = None
) -> None:
    """Generate a single video clip using Veo 3.1."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    label = f"{duration_s}s, with style ref" if ref_image else f"{duration_s}s"
    print(f"  Generating ({label})...", end=" ", flush=True)
    start = time.time()

    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=prompt,
        image=ref_image,
        config=types.GenerateVideosConfig(
            aspect_ratio=ASPECT_RATIO,
            number_of_videos=1,
            duration_seconds=duration_s,
            person_generation="dont_allow",
        ),
    )

    # Poll for completion with timeout
    elapsed_poll = 0
    while not operation.done:
        if elapsed_poll >= MAX_POLL_S:
            print(f"TIMEOUT after {MAX_POLL_S}s")
            return
        time.sleep(POLL_INTERVAL_S)
        elapsed_poll += POLL_INTERVAL_S
        operation = client.operations.get(operation)

    if operation.response and operation.response.generated_videos:
        video = operation.response.generated_videos[0].video
        video.save(str(output_path))
        elapsed = time.time() - start
        size_kb = output_path.stat().st_size / 1024
        print(f"done ({elapsed:.1f}s, {size_kb:.0f}KB)")
    else:
        error_msg = getattr(operation, 'error', None)
        print(f"FAILED: {error_msg.get('message', 'unknown') if error_msg else 'no video returned'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate character animation clips with Veo 3.1")
    parser.add_argument("--character", help="Generate only for this character (e.g., mood_changer_dog)")
    parser.add_argument("--state", help="Generate only this state (e.g., excited)")
    parser.add_argument("--scenarios", action="store_true", help="Generate scenario illustration clips instead of character clips")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")
    args = parser.parse_args()

    config = load_prompts()

    if args.scenarios:
        _generate_scenarios(config, args)
    else:
        _generate_character_clips(config, args)


def _generate_character_clips(config: dict, args: argparse.Namespace) -> None:
    """Generate character emotion clips."""
    characters = config["characters"]

    if args.character:
        if args.character not in characters:
            print(f"Unknown character: {args.character}", file=sys.stderr)
            print(f"Available: {', '.join(characters.keys())}", file=sys.stderr)
            sys.exit(1)
        characters = {args.character: characters[args.character]}

    if args.state:
        for char_config in characters.values():
            if args.state not in char_config["states"]:
                print(f"Unknown state: {args.state}", file=sys.stderr)
                print(f"Available: {', '.join(char_config['states'].keys())}", file=sys.stderr)
                sys.exit(1)

    def _get_states(char_config: dict) -> dict:
        return {args.state: char_config["states"][args.state]} if args.state else char_config["states"]

    total = sum(len(_get_states(c)) for c in characters.values())
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Generating {total} character clips\n")

    client = None if args.dry_run else genai.Client(vertexai=True)

    clip_num = 0
    for char_key, char_config in characters.items():
        prefix = char_config["prefix"]
        states = _get_states(char_config)
        print(f"Character: {char_key} (prefix: {prefix})")

        # Load existing idle frame as style reference if available
        ref_image = None
        if not args.dry_run and client is not None:
            idle_path = OUTPUT_DIR / char_key / f"{prefix}_{REFERENCE_STATE}.mp4"
            if idle_path.exists() and REFERENCE_STATE not in states:
                print(f"  Loading style reference from existing {prefix}_{REFERENCE_STATE}.mp4...")
                ref_image = extract_frame(idle_path)

        ordered_states = []
        if REFERENCE_STATE in states:
            ordered_states.append(REFERENCE_STATE)
            ordered_states.extend(s for s in states if s != REFERENCE_STATE)
        else:
            ordered_states = list(states)

        for state in ordered_states:
            clip_num += 1
            prompt = build_prompt(config, char_key, state)
            duration_s = get_duration_seconds(config, state, char_key)
            output_path = OUTPUT_DIR / char_key / f"{prefix}_{state}.mp4"
            is_ref = state == REFERENCE_STATE and ref_image is None

            print(f"  [{clip_num}/{total}] {prefix}_{state}.mp4{' (style reference)' if is_ref else ''}")

            if args.dry_run or client is None:
                print(f"    Duration: {duration_s}s")
                print(f"    Output: {output_path}")
                if ref_image and not is_ref:
                    print(f"    Using style reference from {prefix}_{REFERENCE_STATE}.mp4")
                print(f"    Prompt: {prompt[:120]}...")
            else:
                generate_clip(client, prompt, output_path, duration_s, ref_image if not is_ref else None)

                if is_ref and output_path.exists():
                    print("    Extracting style reference frame...")
                    ref_image = extract_frame(output_path)

        print()

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Done. {clip_num} character clips generated.")


def _generate_scenarios(config: dict, args: argparse.Namespace) -> None:
    """Generate scenario illustration clips."""
    scenarios = config.get("scenarios", {})
    if not scenarios:
        print("No scenarios defined in prompts YAML.", file=sys.stderr)
        sys.exit(1)

    scenario_output = OUTPUT_DIR.parent / "scenario"

    if args.character:
        if args.character not in scenarios:
            print(f"Unknown character: {args.character}", file=sys.stderr)
            print(f"Available: {', '.join(scenarios.keys())}", file=sys.stderr)
            sys.exit(1)
        scenarios = {args.character: scenarios[args.character]}

    total = sum(len(s["clips"]) for s in scenarios.values())
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Generating {total} scenario clips\n")

    client = None if args.dry_run else genai.Client(vertexai=True)
    defaults = config["defaults"]

    clip_num = 0
    for char_key, scenario_config in scenarios.items():
        style = scenario_config["style"].strip()
        clips = scenario_config["clips"]

        # Use the character's idle frame as style reference for visual consistency
        char_config = config["characters"].get(char_key)
        ref_image = None
        if char_config and not args.dry_run and client is not None:
            idle_path = OUTPUT_DIR / char_key / f"{char_config['prefix']}_idle.mp4"
            if idle_path.exists():
                print(f"  Extracting style reference from {char_config['prefix']}_idle.mp4...")
                ref_image = extract_frame(idle_path)

        print(f"Scenarios: {char_key}")

        # Use the character's base description so the same character appears in scenarios
        char_base = char_config["base"].strip() if char_config else ""

        for clip_id, prompt_text in clips.items():
            clip_num += 1
            full_prompt = f"{char_base} {prompt_text.strip()} {style} {defaults['style']}"
            output_path = scenario_output / char_key / f"scenario_{clip_id}.mp4"

            print(f"  [{clip_num}/{total}] scenario_{clip_id}.mp4")

            if args.dry_run or client is None:
                print(f"    Output: {output_path}")
                print(f"    Prompt: {full_prompt[:120]}...")
                if ref_image:
                    print("    Using character idle frame as style reference")
            else:
                generate_clip(client, full_prompt, output_path, 8, ref_image)

        print()

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Done. {clip_num} scenario clips generated.")


if __name__ == "__main__":
    main()
