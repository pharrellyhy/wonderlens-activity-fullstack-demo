"""Immutable evaluation harness for prompt quality measurement.

Runs scenario YAML files against the live backend, scores every AI response
on multiple quality dimensions, and outputs a composite score (0-100).

Usage:
    uv run python scripts/evaluate_prompts.py [--repeats N] [--scenario NAME]

Requires the backend running on localhost:8000.
"""

import argparse
import sys
import time
from pathlib import Path

import httpx
import yaml

# Add scripts/ to path for scoring import
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from scoring import (
    compute_composite_score,
    score_completion_language,
    score_item_suggestion_free,
    score_phrasing_variety,
    score_tier_compliance,
    score_validation_pass,
)

BASE_URL = "http://localhost:8000"
SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "backend" / "scenarios"
CORRECT_PHOTO_IDS = {"fuzzy_moss", "fluffy_seed", "soft_petal", "woolly_caterpillar"}

# Scenarios to evaluate — covers Cat5 across tiers and edge cases
EVAL_SCENARIOS: list[tuple[str, str]] = [
    ("fluffy_expedition_dandelion", "T0"),
    ("fluffy_expedition_dandelion_t1", "T1"),
    ("fluffy_expedition_dandelion_decline", "T0"),
    ("fluffy_expedition_dandelion_silent", "T0"),
    ("fluffy_expedition_dandelion_wrong_photos", "T0"),
    ("fluffy_expedition_dandelion_offtopic", "T0"),
]


def load_scenario(name: str) -> dict:
    path = SCENARIOS_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f)


def find_correct_item(round_items: list[dict]) -> str | None:
    for item in round_items:
        if item["id"] in CORRECT_PHOTO_IDS:
            return item["id"]
    return round_items[0]["id"] if round_items else None


def find_wrong_item(round_items: list[dict]) -> str | None:
    for item in round_items:
        if item["id"] not in CORRECT_PHOTO_IDS:
            return item["id"]
    return None


def send_turn(client: httpx.Client, payload: dict) -> dict | None:
    resp = client.post(f"{BASE_URL}/api/turn", json=payload)
    if resp.status_code != 200:
        return None
    return resp.json()


def _extract_state(turn_data: dict) -> dict:
    """Extract session state fields needed for scoring."""
    ss = turn_data.get("session_state", {})
    return {
        "step": ss.get("current_step", ""),
        "status": ss.get("status", ""),
        "collection_phase": ss.get("collection_phase", "photo"),
        "collected_count": len(ss.get("collected_photos", [])),
        "total_rounds": ss.get("total_rounds", 3),
        "round_items": ss.get("current_round_items", []),
    }


def _score_dialogue(
    dialogue: str,
    step: str,
    tier: str,
    collection_phase: str,
    is_first_on_step: bool,
    collected: int,
    total: int,
) -> dict[str, float]:
    """Score a single dialogue turn across all dimensions."""
    return {
        "validation": score_validation_pass(dialogue, step, tier, collection_phase, is_first_on_step),
        "item_suggestion": score_item_suggestion_free(dialogue),
        "completion_language": score_completion_language(dialogue, collected, total),
        "tier_compliance": score_tier_compliance(dialogue, tier),
    }


def run_and_score(scenario_name: str, tier: str, client: httpx.Client) -> dict:
    """Run a single scenario and return per-response scores.

    Returns dict with lists of scores per dimension and progress phrases.
    """
    scenario = load_scenario(scenario_name)
    if not scenario:
        return {"error": f"Scenario {scenario_name} not found"}

    entity = scenario["entity"]
    scores: dict[str, list[float]] = {
        "validation": [],
        "item_suggestion": [],
        "completion_language": [],
        "tier_compliance": [],
    }
    progress_phrases: list[str] = []

    # Start session
    resp = client.post(f"{BASE_URL}/api/start-deep-link", json={"entity": entity, "tier": tier})
    if resp.status_code != 200:
        return {"error": f"Start failed: {resp.status_code}"}

    data = resp.json()
    session_id = data["session_id"]
    last_dialogue = data["first_turn"]["dialogue"]
    last_state = _extract_state(data)
    prev_step = last_state["step"]
    cached_round_items = last_state["round_items"]

    # Score the first turn (hook)
    first_scores = _score_dialogue(
        last_dialogue,
        last_state["step"],
        tier,
        last_state["collection_phase"],
        True,
        last_state["collected_count"],
        last_state["total_rounds"],
    )
    for dim, val in first_scores.items():
        scores[dim].append(val)

    # Process scenario turns
    turns = scenario.get("turns", [])
    session_ended = False

    for turn in turns:
        if session_ended:
            break

        role = turn["role"]
        if role in ("system", "ai"):
            continue

        if role == "child":
            child_text = turn.get("text", "")
            payload: dict = {"session_id": session_id}

            if turn.get("type") == "silent":
                payload["text"] = ""
                payload["is_silent"] = True
            elif "[collected correct item:" in child_text:
                correct_id = find_correct_item(cached_round_items)
                if correct_id:
                    payload["photo_id"] = correct_id
                else:
                    payload["text"] = child_text
            elif "[selected wrong photo:" in child_text:
                wrong_id = find_wrong_item(cached_round_items)
                if wrong_id:
                    payload["photo_id"] = wrong_id
                else:
                    payload["text"] = child_text
            else:
                payload["text"] = child_text

            turn_data = send_turn(client, payload)
            if not turn_data:
                continue

            dialogue = turn_data.get("turn", {}).get("dialogue", "")
            state = _extract_state(turn_data)
            cached_round_items = state["round_items"]
            is_first = state["step"] != prev_step
            prev_step = state["step"]

            if dialogue:
                turn_scores = _score_dialogue(
                    dialogue,
                    state["step"],
                    tier,
                    state["collection_phase"],
                    is_first,
                    state["collected_count"],
                    state["total_rounds"],
                )
                for dim, val in turn_scores.items():
                    scores[dim].append(val)

                # Collect progress phrases from collection steps
                if state["step"].startswith("STEP_3_COLLECT_"):
                    progress_phrases.append(dialogue)

                last_dialogue = dialogue

            if state["status"] in ("completed", "exited", "error"):
                session_ended = True
                continue

            # Auto-advance for celebrate/closing steps
            step = state["step"]
            auto = turn_data.get("turn", {}).get("auto_advance", False)
            while auto or (
                state["status"] == "active"
                and step
                and any(step.startswith(p) for p in ("STEP_4_CELEBRATE", "STEP_5_", "STEP_6_"))
                and last_dialogue
            ):
                turn_data = send_turn(client, {"session_id": session_id, "text": ""})
                if not turn_data:
                    break

                new_step = turn_data.get("session_state", {}).get("current_step", "")
                new_dialogue = turn_data.get("turn", {}).get("dialogue", "")
                state = _extract_state(turn_data)

                if new_step == step and not new_dialogue:
                    break

                step = new_step
                if new_dialogue:
                    is_first = step != prev_step
                    prev_step = step
                    turn_scores = _score_dialogue(
                        new_dialogue,
                        step,
                        tier,
                        state["collection_phase"],
                        is_first,
                        state["collected_count"],
                        state["total_rounds"],
                    )
                    for dim, val in turn_scores.items():
                        scores[dim].append(val)
                    last_dialogue = new_dialogue

                cached_round_items = state["round_items"]
                auto = turn_data.get("turn", {}).get("auto_advance", False)

                if state["status"] in ("completed", "exited", "error"):
                    session_ended = True
                    break

    scores["progress_phrases"] = progress_phrases  # type: ignore[assignment]
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate prompt quality")
    parser.add_argument("--repeats", type=int, default=3, help="Runs per scenario (default: 3)")
    parser.add_argument("--scenario", type=str, default=None, help="Run a single scenario")
    args = parser.parse_args()

    scenarios = EVAL_SCENARIOS
    if args.scenario:
        matching = [(name, tier) for name, tier in EVAL_SCENARIOS if args.scenario in name]
        if not matching:
            print(f"No scenario matching '{args.scenario}'. Available:")
            for name, tier in EVAL_SCENARIOS:
                print(f"  {name} ({tier})")
            sys.exit(1)
        scenarios = matching

    all_validation: list[float] = []
    all_item: list[float] = []
    all_completion: list[float] = []
    all_tier: list[float] = []
    all_progress: list[str] = []
    errors: list[str] = []

    start = time.perf_counter()

    with httpx.Client(timeout=30) as client:
        for repeat in range(args.repeats):
            print(f"--- Repeat {repeat + 1}/{args.repeats} ---")
            for scenario_name, tier in scenarios:
                result = run_and_score(scenario_name, tier, client)

                if "error" in result:
                    errors.append(f"{scenario_name}: {result['error']}")
                    print(f"  {scenario_name} ({tier}): ERROR - {result['error']}")
                    continue

                v_scores = result.get("validation", [])
                all_validation.extend(v_scores)
                all_item.extend(result.get("item_suggestion", []))
                all_completion.extend(result.get("completion_language", []))
                all_tier.extend(result.get("tier_compliance", []))
                all_progress.extend(result.get("progress_phrases", []))

                v_rate = sum(v_scores) / len(v_scores) * 100 if v_scores else 0
                print(f"  {scenario_name} ({tier}): {len(v_scores)} turns scored, validation={v_rate:.0f}%")

    variety = score_phrasing_variety(all_progress)
    composite = compute_composite_score(all_validation, all_item, all_completion, all_tier, variety)
    elapsed = time.perf_counter() - start

    # Structured output for machine parsing
    print(f"\n{'=' * 50}")
    print(f"composite_score: {composite:.2f}")
    print(
        f"validation_pass_rate: {sum(all_validation) / len(all_validation) * 100:.1f}%"
        if all_validation
        else "validation_pass_rate: N/A"
    )
    print(
        f"item_suggestion_free_rate: {sum(all_item) / len(all_item) * 100:.1f}%"
        if all_item
        else "item_suggestion_free_rate: N/A"
    )
    print(
        f"completion_language_rate: {sum(all_completion) / len(all_completion) * 100:.1f}%"
        if all_completion
        else "completion_language_rate: N/A"
    )
    print(
        f"tier_compliance_rate: {sum(all_tier) / len(all_tier) * 100:.1f}%" if all_tier else "tier_compliance_rate: N/A"
    )
    print(f"phrasing_variety: {variety:.3f}")
    print(f"eval_duration_seconds: {elapsed:.1f}")
    print(f"total_responses_scored: {len(all_validation)}")
    if errors:
        print(f"errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")
    print(f"{'=' * 50}")

    sys.exit(0)


if __name__ == "__main__":
    main()
