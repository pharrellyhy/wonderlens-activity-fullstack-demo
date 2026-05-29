#!/usr/bin/env python3
"""Run live smoke checks for standalone activity text-game sessions.

Usage:
    uv run python scripts/run_activity_text_smoke.py
    uv run python scripts/run_activity_text_smoke.py activity_career_decision_role_play
    uv run python scripts/run_activity_text_smoke.py --base-url http://localhost:8000 --no-turn

The backend must already be running with its environment sourced. This script
only calls the local HTTP API and does not read credentials.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TURN_TEXT = "yes"
TEXT_CHOICE_TERMS = (
    "type the matching picture",
    "name the matching picture",
    "describe the matching picture",
    "which picture",
    "what matches",
    "short description",
)


@dataclass(frozen=True)
class DialogueContract:
    """Source-fidelity checks for one activity's live dialogue."""

    all_of: tuple[str, ...] = ()
    any_of: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()
    typed_choice_required: bool = False


@dataclass(frozen=True)
class SmokeResult:
    """Single activity smoke result."""

    activity_id: str
    start_status: int
    turn_status: int | None
    session_id: str
    template_type: str
    session_status: str
    current_step: str
    dialogues: list[str]
    failures: list[str]

    @property
    def ok(self) -> bool:
        """Return whether the activity passed the smoke checks."""
        return not self.failures


SMOKE_CONTRACTS = {
    "activity_animal_sound_imitation": DialogueContract(any_of=("animal", "sound", "voice")),
    "activity_career_decision_role_play": DialogueContract(
        all_of=("firefighter",),
        any_of=("smoke alarm", "water hose", "cooking oil", "ringing alarm", "safe choices", "first decision"),
        forbidden=("doctor", "builder", "teacher"),
    ),
    "activity_constellation_star_count": DialogueContract(any_of=("constellation", "star", "count")),
    "activity_emotion_reader": DialogueContract(any_of=("feeling", "cue", "emotion", "help")),
    "activity_guided_drawing": DialogueContract(any_of=("paper", "pencil", "drawing", "caregiver")),
    "activity_partial_reveal_guess": DialogueContract(
        any_of=("distinctive part", "visible clue", "guess", "clue", "peek", "mystery", "hiding"),
    ),
    "activity_phoneme_treasure_hunt": DialogueContract(
        any_of=("letter b", "b word", "b words", "starts with b", "words that start with b"),
        forbidden=("smooth like", "bumpy like", "trace", "traced", "finger"),
    ),
    "activity_recognition_pop_challenge": DialogueContract(
        any_of=("target", "match", "distractor", "picture", "choice"),
        forbidden=("point", "tap", "click", "touch", "left, right", "this, that", "target card", "cards"),
    ),
    "activity_story_challenge_unlock": DialogueContract(
        all_of=("fox",),
        any_of=("moon door", "owl", "hoo hoo", "star page", "bonjour", "silver", "white", "blue"),
    ),
    "activity_travel_planner": DialogueContract(any_of=("travel", "pack", "vehicle", "how to travel")),
    "activity_vegetable_sort": DialogueContract(any_of=("vegetable", "sort", "edible part", "cooking use")),
    "activity_word_echo_practice": DialogueContract(any_of=("word", "echo", "repeat")),
}


def _normalize(text: str) -> str:
    """Normalize text for resilient term checks."""
    return text.lower().replace("-", " ")


def _contains_term(text: str, term: str) -> bool:
    """Return whether text contains a term with word boundaries for single tokens."""
    normalized_text = _normalize(text)
    normalized_term = _normalize(term)
    if " " in normalized_term:
        return normalized_term in normalized_text
    return re.search(rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])", normalized_text) is not None


def check_dialogue_contract(activity_id: str, dialogues: list[str]) -> list[str]:
    """Return source-fidelity failures for the activity's combined live dialogue."""
    contract = SMOKE_CONTRACTS.get(activity_id)
    if contract is None:
        return []

    combined = "\n".join(dialogues)
    failures: list[str] = []

    for term in contract.all_of:
        if not _contains_term(combined, term):
            failures.append(f"missing required term: {term}")

    if contract.any_of and not any(_contains_term(combined, term) for term in contract.any_of):
        failures.append(f"missing any source term: {' | '.join(contract.any_of)}")

    for term in contract.forbidden:
        if _contains_term(combined, term):
            failures.append(f"found forbidden term: {term}")

    if contract.typed_choice_required and not any(_contains_term(combined, term) for term in TEXT_CHOICE_TERMS):
        failures.append("missing typed-choice prompt for text-only recognition")

    return failures


def resolve_activity_ids(activities: list[dict[str, Any]], requested_ids: list[str]) -> list[str]:
    """Resolve activity IDs from catalog data, preserving catalog order."""
    catalog_ids = [activity["id"] for activity in activities]
    if not requested_ids:
        return catalog_ids

    missing = sorted(set(requested_ids) - set(catalog_ids))
    if missing:
        raise ValueError(f"unknown activity id(s): {', '.join(missing)}")

    requested = set(requested_ids)
    return [activity_id for activity_id in catalog_ids if activity_id in requested]


def fetch_activity_catalog(client: httpx.Client, base_url: str) -> list[dict[str, Any]]:
    """Fetch the live activity catalog."""
    response = client.get(f"{base_url}/api/activities")
    response.raise_for_status()
    payload = response.json()
    activities = payload.get("activities", [])
    if not isinstance(activities, list):
        raise ValueError("/api/activities returned no activities list")
    return activities


def _dialogue_from_start(payload: dict[str, Any]) -> str:
    """Extract dialogue from a start-activity response."""
    first_turn = payload.get("first_turn", {})
    if isinstance(first_turn, dict):
        dialogue = first_turn.get("dialogue", "")
        if isinstance(dialogue, str):
            return dialogue
    return ""


def _dialogue_from_turn(payload: dict[str, Any]) -> str:
    """Extract dialogue from a turn response."""
    turn = payload.get("turn", {})
    if isinstance(turn, dict):
        dialogue = turn.get("dialogue", "")
        if isinstance(dialogue, str):
            return dialogue
    return ""


def _session_field(payload: dict[str, Any], field: str) -> str:
    """Extract a string field from session_state."""
    session_state = payload.get("session_state", {})
    if isinstance(session_state, dict):
        value = session_state.get(field, "")
        if isinstance(value, str):
            return value
    return ""


def check_start_payload(activity_id: str, payload: dict[str, Any]) -> list[str]:
    """Return failures for the start-activity response contract."""
    failures: list[str] = []
    session_state = payload.get("session_state", {})
    first_turn = payload.get("first_turn", {})

    if payload.get("status") != "ok":
        failures.append(f"start payload status is not ok: {payload.get('status')}")
    if not payload.get("session_id"):
        failures.append("start response missing session_id")
    if payload.get("activity_type") != activity_id:
        failures.append(f"start payload activity_type mismatch: {payload.get('activity_type')}")
    if not payload.get("template_type"):
        failures.append("start response missing template_type")
    if not isinstance(first_turn, dict) or not first_turn.get("dialogue"):
        failures.append("start response missing first_turn dialogue")
    if not isinstance(session_state, dict):
        failures.append("start response missing session_state")
    else:
        if session_state.get("status") != "active":
            failures.append(f"unexpected start session status: {session_state.get('status')}")
        if session_state.get("interaction_mode") != "text":
            failures.append("session_state.interaction_mode is not text")

    return failures


def run_activity_smoke(
    client: httpx.Client,
    base_url: str,
    activity_id: str,
    tier: str,
    turn_text: str | None,
) -> SmokeResult:
    """Start one activity and optionally send one text turn."""
    failures: list[str] = []
    dialogues: list[str] = []
    turn_status: int | None = None

    start_response = client.post(
        f"{base_url}/api/start-activity",
        json={"activity_type": activity_id, "tier": tier, "interaction_mode": "text"},
    )
    start_status = start_response.status_code
    if start_status != 200:
        return SmokeResult(
            activity_id=activity_id,
            start_status=start_status,
            turn_status=turn_status,
            session_id="",
            template_type="",
            session_status="",
            current_step="",
            dialogues=dialogues,
            failures=[f"start failed: {start_status} {start_response.text[:160]}"],
        )

    start_payload = start_response.json()
    session_id = str(start_payload.get("session_id", ""))
    template_type = str(start_payload.get("template_type", ""))
    session_status = _session_field(start_payload, "status")
    current_step = _session_field(start_payload, "current_step")
    start_dialogue = _dialogue_from_start(start_payload)

    failures.extend(check_start_payload(activity_id, start_payload))
    dialogues.append(start_dialogue)

    if session_id and turn_text:
        turn_response = client.post(
            f"{base_url}/api/turn",
            json={"session_id": session_id, "text": turn_text, "is_silent": False},
        )
        turn_status = turn_response.status_code
        if turn_status != 200:
            failures.append(f"turn failed: {turn_status} {turn_response.text[:160]}")
        else:
            turn_payload = turn_response.json()
            turn_dialogue = _dialogue_from_turn(turn_payload)
            if not turn_dialogue:
                failures.append("turn response missing dialogue")
            dialogues.append(turn_dialogue)
            session_status = _session_field(turn_payload, "status") or session_status
            current_step = _session_field(turn_payload, "current_step") or current_step

    failures.extend(check_dialogue_contract(activity_id, dialogues))

    return SmokeResult(
        activity_id=activity_id,
        start_status=start_status,
        turn_status=turn_status,
        session_id=session_id,
        template_type=template_type,
        session_status=session_status,
        current_step=current_step,
        dialogues=dialogues,
        failures=failures,
    )


def print_result(result: SmokeResult) -> None:
    """Print a concise human-readable smoke result."""
    mark = "PASS" if result.ok else "FAIL"
    turn_status = result.turn_status if result.turn_status is not None else "-"
    print(f"{mark} {result.activity_id}")
    print(
        f"  start={result.start_status} turn={turn_status} "
        f"template={result.template_type or '-'} "
        f"status={result.session_status or '-'} step={result.current_step or '-'}"
    )
    for failure in result.failures:
        print(f"  - {failure}")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Run live smoke checks for standalone activity text-game sessions.")
    parser.add_argument("activity_ids", nargs="*", help="Optional activity IDs. Defaults to every catalog activity.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("WONDERLENS_API_BASE_URL", DEFAULT_BASE_URL),
        help=f"Backend base URL. Defaults to {DEFAULT_BASE_URL} or WONDERLENS_API_BASE_URL.",
    )
    parser.add_argument("--tier", default="T1", help="Tier to start for each activity.")
    parser.add_argument("--turn", default=DEFAULT_TURN_TEXT, help="One child text turn to send after start.")
    parser.add_argument("--no-turn", action="store_true", help="Only start activities; do not send a child turn.")
    parser.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout in seconds.")
    parser.add_argument("--list", action="store_true", help="List live catalog activity IDs and exit.")
    return parser


def build_http_client(timeout: float) -> httpx.Client:
    """Build an HTTP client for local smoke checks."""
    return httpx.Client(timeout=httpx.Timeout(timeout, connect=min(timeout, 10.0)), trust_env=False)


def main() -> None:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    turn_text = None if args.no_turn else args.turn

    try:
        with build_http_client(args.timeout) as client:
            activities = fetch_activity_catalog(client, base_url)
            if args.list:
                for activity in activities:
                    print(activity["id"])
                return

            activity_ids = resolve_activity_ids(activities, args.activity_ids)
            results = [
                run_activity_smoke(client, base_url, activity_id, args.tier, turn_text)
                for activity_id in activity_ids
            ]
    except (httpx.HTTPError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    for result in results:
        print_result(result)

    failed = [result for result in results if not result.ok]
    print(f"SUMMARY: {len(results) - len(failed)} passed, {len(failed)} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
