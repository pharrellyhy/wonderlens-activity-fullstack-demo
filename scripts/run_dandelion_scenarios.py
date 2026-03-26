"""Run dandelion scenario YAML files against the live backend server.

Usage:
    uv run python scripts/run_dandelion_scenarios.py [scenario_name]

If no scenario name given, runs all dandelion scenarios.
Requires the backend running on localhost:8000.
"""

import sys
from pathlib import Path

import httpx
import yaml

BASE_URL = "http://localhost:8000"
SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "backend" / "scenarios"

# Correct photo IDs from the fluffy_expedition_dandelion game catalog
CORRECT_PHOTO_IDS = {"fuzzy_moss", "fluffy_seed", "soft_petal", "woolly_caterpillar"}


def load_scenario(name: str) -> dict:
    path = SCENARIOS_DIR / f"{name}.yaml"
    if not path.exists():
        print(f"  ERROR: {path} not found")
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
        print(f"  ERROR: turn failed {resp.status_code}: {resp.text[:80]}")
        return None
    return resp.json()


def print_ai(turn_data: dict) -> str:
    """Print AI response and return the dialogue."""
    t = turn_data.get("turn", {})
    ss = turn_data.get("session_state", {})
    dialogue = t.get("dialogue", "")
    step = ss.get("current_step", "?")
    status = ss.get("status", "?")
    phase = ss.get("collection_phase", "")
    collected = len(ss.get("collected_photos", []))
    names = ss.get("collected_names", [])

    parts = [f"[{step}]"]
    if phase:
        parts.append(f"phase={phase}")
    parts.append(f"collected={collected}")
    if names:
        parts.append(f"names={names}")
    parts.append(f"status={status}")
    print(f"  {' '.join(parts)}")
    print(f"  AI: {dialogue}")
    return dialogue


def run_scenario(name: str) -> dict:
    """Run a single scenario. Returns {passed: int, failed: int, errors: list}."""
    scenario = load_scenario(name)
    if not scenario:
        return {"passed": 0, "failed": 0, "errors": ["scenario not found"]}

    entity = scenario["entity"]
    tier = scenario.get("tier", "T0")
    results: dict = {"passed": 0, "failed": 0, "errors": []}

    with httpx.Client(timeout=30) as client:
        # Start session
        resp = client.post(f"{BASE_URL}/api/start-deep-link", json={"entity": entity, "tier": tier})
        if resp.status_code != 200:
            results["errors"].append(f"Start failed: {resp.status_code} {resp.text[:100]}")
            return results

        data = resp.json()
        session_id = data["session_id"]
        last_dialogue = data["first_turn"]["dialogue"]
        last_session_state = data.get("session_state", {})

        print(f"  [{last_session_state.get('current_step', '?')}] AI: {last_dialogue}")

        # Track round items from the last response (avoids peek-silence bug)
        cached_round_items: list[dict] = last_session_state.get("current_round_items", [])

        # Process turns
        turns = scenario.get("turns", [])
        session_ended = False

        for turn in turns:
            if session_ended:
                break

            role = turn["role"]

            if role == "system":
                continue

            if role == "ai":
                # Validate the last AI response
                must_contain = turn.get("must_contain", [])
                must_not_contain = turn.get("must_not_contain", [])
                step_label = turn.get("step", "?")
                dialogue_lower = last_dialogue.lower() if last_dialogue else ""

                for word in must_contain:
                    if word.lower() not in dialogue_lower:
                        msg = f"  FAIL [{step_label}]: expected '{word}' in: {last_dialogue[:80]}"
                        print(msg)
                        results["errors"].append(msg)
                        results["failed"] += 1
                    else:
                        results["passed"] += 1

                for word in must_not_contain:
                    if word.lower() in dialogue_lower:
                        msg = f"  FAIL [{step_label}]: forbidden '{word}' found in: {last_dialogue[:80]}"
                        print(msg)
                        results["errors"].append(msg)
                        results["failed"] += 1
                    else:
                        results["passed"] += 1

                continue

            if role == "child":
                child_type = turn.get("type", "ideal")
                child_text = turn.get("text", "")

                payload: dict = {"session_id": session_id}

                if child_type == "silent":
                    payload["text"] = ""
                    payload["is_silent"] = True
                    print("  Child: [silence]")
                elif "[collected correct item:" in child_text:
                    correct_id = find_correct_item(cached_round_items)
                    if correct_id:
                        payload["photo_id"] = correct_id
                        print(f"  Child: [photo: {correct_id}]")
                    else:
                        payload["text"] = child_text
                        print(f"  Child: {child_text} (no round items cached)")
                elif "[selected wrong photo:" in child_text:
                    wrong_id = find_wrong_item(cached_round_items)
                    if wrong_id:
                        payload["photo_id"] = wrong_id
                        print(f"  Child: [wrong photo: {wrong_id}]")
                    else:
                        payload["text"] = child_text
                        print(f"  Child: {child_text} (no distractors cached)")
                else:
                    payload["text"] = child_text
                    print(f"  Child: {child_text}")

                turn_data = send_turn(client, payload)
                if not turn_data:
                    results["errors"].append("turn API returned error")
                    continue

                last_dialogue = print_ai(turn_data)
                last_session_state = turn_data.get("session_state", {})
                cached_round_items = last_session_state.get("current_round_items", [])
                status = last_session_state.get("status", "?")

                if status in ("completed", "exited", "error"):
                    print(f"  Session ended: {status}")
                    session_ended = True
                    continue

                # Auto-advance for celebrate/closing steps
                step = last_session_state.get("current_step", "")
                auto = turn_data.get("turn", {}).get("auto_advance", False)
                while auto or (
                    status == "active"
                    and step
                    and any(step.startswith(p) for p in ("STEP_4_CELEBRATE", "STEP_5_", "STEP_6_"))
                    and last_dialogue
                ):
                    turn_data = send_turn(client, {"session_id": session_id, "text": ""})
                    if not turn_data:
                        break
                    new_step = turn_data.get("session_state", {}).get("current_step", "")
                    new_dialogue = turn_data.get("turn", {}).get("dialogue", "")
                    status = turn_data.get("session_state", {}).get("status", "?")

                    if new_step == step and not new_dialogue:
                        break

                    step = new_step
                    if new_dialogue:
                        last_dialogue = print_ai(turn_data)
                    last_session_state = turn_data.get("session_state", {})
                    cached_round_items = last_session_state.get("current_round_items", [])
                    auto = turn_data.get("turn", {}).get("auto_advance", False)

                    if status in ("completed", "exited", "error"):
                        print(f"  Session ended: {status}")
                        session_ended = True
                        break

    return results


def main() -> None:
    scenarios = [
        "fluffy_expedition_dandelion",
        "fluffy_expedition_dandelion_decline",
        "fluffy_expedition_dandelion_silent",
        "fluffy_expedition_dandelion_wrong_photos",
        "fluffy_expedition_dandelion_offtopic",
        "fluffy_expedition_dandelion_t1",
    ]

    if len(sys.argv) > 1:
        scenarios = [sys.argv[1]]

    total_passed = 0
    total_failed = 0
    all_errors: list[str] = []

    for name in scenarios:
        print(f"\n{'=' * 60}")
        print(f"SCENARIO: {name}")
        print(f"{'=' * 60}")
        results = run_scenario(name)
        total_passed += results["passed"]
        total_failed += results["failed"]
        all_errors.extend(results["errors"])

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {total_passed} checks passed, {total_failed} failed")
    if all_errors:
        print("\nFailed checks:")
        for err in all_errors:
            print(f"  {err}")
    print(f"{'=' * 60}")

    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
