"""Run multiple combinations of child responses across all 5 activities.

Each activity gets 3-5 different "personality" runs:
  - enthusiastic: eager, creative answers
  - shy: short answers, silences, confusion
  - silly: off-topic, goofy, tangential
  - resistant: declines, reluctant, eventually warms up
  - speedrun: minimal answers, fast completion
"""

import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
ICONS_DIR = str(Path(__file__).resolve().parent.parent / "frontend" / "public" / "icons")

issues: list[str] = []
transcripts: list[str] = []


def start_session(filename: str) -> tuple[str, dict]:
    with open(f"{ICONS_DIR}/{filename}", "rb") as f:
        resp = requests.post(f"{BASE}/api/start", files={"photo": (filename, f, "image/png")}, data={"tier": "T0"})
    data = resp.json()
    assert data["status"] == "ok", f"Start failed: {data}"
    return data["session_id"], data


def turn(sid: str, text: str = "", photo_id: str | None = None, silent: bool = False) -> dict:
    payload = {"session_id": sid, "text": text, "is_silent": silent}
    if photo_id:
        payload["photo_id"] = photo_id
    resp = requests.post(f"{BASE}/api/turn", json=payload)
    return resp.json()


def check(data: dict, label: str, activity: str) -> None:
    dialogue = data["turn"]["dialogue"]
    step = data["session_state"]["current_step"]
    if not dialogue.strip():
        issues.append(f"[{activity}] EMPTY dialogue at {step} ({label})")
    if dialogue and not dialogue.startswith("["):
        issues.append(f"[{activity}] Missing emotion tag at {step}: {dialogue[:60]}")
    # Check for directive commands, but skip when embedded in invitational frames
    invitational_prefixes = [
        "would you like to",
        "do you want to",
        "how about we",
        "shall we",
        "could you",
        "can you",
        "maybe you could",
        "what if you",
        "what if we",
        "i wonder if you",
        "i wonder if we",
        "let's play",
        "let's try",
        "where you",
        "where we",
    ]
    dialogue_lower = dialogue.lower()
    for d in ["go find", "tell me", "now do", "you must", "go look", "go get"]:
        if d not in dialogue_lower:
            continue
        # Check each occurrence: is it preceded by an invitational frame?
        idx = 0
        while idx < len(dialogue_lower):
            pos = dialogue_lower.find(d, idx)
            if pos == -1:
                break
            # Look back ~60 chars for an invitational prefix in the same sentence
            lookback = dialogue_lower[max(0, pos - 60) : pos]
            # Find the last sentence boundary before the directive
            for sep in [".", "!", "?"]:
                last_sep = lookback.rfind(sep)
                if last_sep != -1:
                    lookback = lookback[last_sep + 1 :]
                    break
            is_invitational = any(p in lookback for p in invitational_prefixes)
            if not is_invitational:
                issues.append(f"[{activity}] Directive '{d}' at {step}: {dialogue[:80]}")
                break
            idx = pos + len(d)


def T(label: str, data: dict) -> None:
    """Log one turn to transcript."""
    d = data["turn"]["dialogue"]
    step = data["session_state"]["current_step"]
    rtype = data["turn"]["response_type"]
    transcripts.append(f"  {label:35s} | {rtype:15s} | {step}")
    transcripts.append(f"    AI: {d}")


def drain_auto(sid: str, data: dict, activity: str) -> dict:
    """Follow auto-advance chain until interactive step or session ends."""
    while data["turn"].get("auto_advance") and data["session_state"]["status"] == "active":
        data = turn(sid)
        T("(auto)", data)
        check(data, "auto", activity)
    return data


def collect_round(sid: str, data: dict, activity: str) -> dict:
    """Find and pick the correct item for the current collect step."""
    items = data["session_state"].get("current_round_items", [])
    for item in items:
        data = turn(sid, photo_id=item["id"])
        if data["turn"]["response_type"] != "wrong_photo":
            T(f"pick correct: {item['id']}", data)
            check(data, "correct pick", activity)
            return data
        T(f"pick wrong: {item['id']}", data)
        check(data, "wrong pick", activity)
    return data


# ============================================================
# CAT 1 GENERIC RUNNER
# ============================================================


def run_cat1(
    filename: str,
    activity: str,
    personality: str,
    hook_reply: str,
    rules_reply: str,
    round_replies: list[str],
    extra_interactions: dict | None = None,
):
    """Run a Cat1 activity with given personality responses."""
    extra = extra_interactions or {}
    transcripts.append(f"\n{'─' * 70}")
    transcripts.append(f"  {activity} — {personality}")
    transcripts.append(f"{'─' * 70}")

    sid, start = start_session(filename)
    transcripts.append(f"  HOOK: {start['first_turn']['dialogue']}")

    # Hook reply
    if hook_reply == "SILENCE":
        data = turn(sid, silent=True)
        T("(silence)", data)
    else:
        data = turn(sid, hook_reply)
        T(f"child: {hook_reply[:30]}", data)
    check(data, "hook reply", activity)

    # Extra interactions before rules acceptance (e.g. decline)
    for label, text in extra.get("pre_accept", []):
        if text == "SILENCE":
            data = turn(sid, silent=True)
        else:
            data = turn(sid, text)
        T(f"child: {label[:30]}", data)
        check(data, label, activity)

    # Accept rules
    if rules_reply == "SILENCE":
        data = turn(sid, silent=True)
        T("(silence)", data)
    else:
        data = turn(sid, rules_reply)
        T(f"child: {rules_reply[:30]}", data)
    check(data, "accept rules", activity)

    # Play rounds
    for i, reply in enumerate(round_replies):
        status = data["session_state"]["status"]
        if status != "active":
            break

        data = drain_auto(sid, data, activity)
        if data["session_state"]["status"] != "active":
            break

        if reply == "SILENCE":
            data = turn(sid, silent=True)
            T(f"R{i + 1}: (silence)", data)
            check(data, f"R{i + 1} silence", activity)
            # Follow up after silence hint
            if data["session_state"]["status"] == "active" and not data["turn"].get("auto_advance"):
                data = turn(sid, "hmm maybe happy?")
                T(f"R{i + 1}: after hint", data)
                check(data, f"R{i + 1} after hint", activity)
        else:
            data = turn(sid, reply)
            T(f"R{i + 1}: {reply[:30]}", data)
            check(data, f"R{i + 1}", activity)

    # Drain to completion
    for _ in range(8):
        if data["session_state"]["status"] != "active":
            break
        data = drain_auto(sid, data, activity)
        if data["session_state"]["status"] != "active":
            break
        if not data["turn"].get("auto_advance"):
            data = turn(sid, "that was great!")
            T("child: that was great!", data)
            check(data, "followup", activity)

    transcripts.append(f"  RESULT: {data['session_state']['status']} at {data['session_state']['current_step']}")


# ============================================================
# CAT 5 GENERIC RUNNER
# ============================================================


def run_cat5(
    filename: str,
    activity: str,
    personality: str,
    hook_reply: str,
    mission_reply: str,
    round_behaviors: list[str],
    synthesis_reply: str | None = None,
    extra_interactions: dict | None = None,
):
    """Run a Cat5 activity. round_behaviors: 'correct', 'wrong_then_correct', 'silence_then_correct', 'wrong_wrong'."""
    extra = extra_interactions or {}
    transcripts.append(f"\n{'─' * 70}")
    transcripts.append(f"  {activity} — {personality}")
    transcripts.append(f"{'─' * 70}")

    sid, start = start_session(filename)
    transcripts.append(f"  HOOK: {start['first_turn']['dialogue']}")

    # Hook
    data = turn(sid, hook_reply)
    T(f"child: {hook_reply[:30]}", data)
    check(data, "hook", activity)

    # Pre-accept extras (declines etc)
    for label, text in extra.get("pre_accept", []):
        data = turn(sid, text)
        T(f"child: {label[:30]}", data)
        check(data, label, activity)

    # Accept mission
    data = turn(sid, mission_reply)
    T(f"child: {mission_reply[:30]}", data)
    check(data, "accept", activity)

    # Collection rounds
    for i, behavior in enumerate(round_behaviors):
        if data["session_state"]["status"] != "active":
            break
        items = data["session_state"].get("current_round_items", [])
        if not items:
            break

        if behavior == "correct":
            data = collect_round(sid, data, activity)

        elif behavior == "wrong_then_correct":
            # Pick last item (likely wrong), then find correct
            data = turn(sid, photo_id=items[-1]["id"])
            T(f"R{i + 1} wrong: {items[-1]['id']}", data)
            check(data, f"R{i + 1} wrong", activity)
            if data["turn"]["response_type"] == "wrong_photo":
                data = collect_round(sid, data, activity)
            # If it was actually correct, that's fine

        elif behavior == "silence_then_correct":
            data = turn(sid, silent=True)
            T(f"R{i + 1}: (silence)", data)
            check(data, f"R{i + 1} silence", activity)
            data = collect_round(sid, data, activity)

        elif behavior == "offtopic_then_correct":
            data = turn(sid, "i saw a butterfly!")
            T(f"R{i + 1}: off-topic", data)
            check(data, f"R{i + 1} offtopic", activity)
            data = collect_round(sid, data, activity)

        elif behavior == "wrong_wrong":
            # Two wrong picks → should exit
            data = turn(sid, photo_id=items[-1]["id"])
            T(f"R{i + 1} wrong#1: {items[-1]['id']}", data)
            check(data, f"R{i + 1} wrong1", activity)
            if data["session_state"]["status"] == "active" and data["turn"]["response_type"] == "wrong_photo":
                items2 = data["session_state"].get("current_round_items", items)
                wrong2 = items2[-2]["id"] if len(items2) > 1 else items2[-1]["id"]
                data = turn(sid, photo_id=wrong2)
                T(f"R{i + 1} wrong#2: {wrong2}", data)
                check(data, f"R{i + 1} wrong2", activity)
            break

    # Synthesis (if reached)
    if data["session_state"]["current_step"] == "STEP_4_SYNTHESIS" and synthesis_reply:
        data = turn(sid, synthesis_reply)
        T(f"synthesis: {synthesis_reply[:30]}", data)
        check(data, "synthesis", activity)

    # Drain to end
    for _ in range(8):
        if data["session_state"]["status"] != "active":
            break
        data = drain_auto(sid, data, activity)
        if data["session_state"]["status"] != "active":
            break
        if not data["turn"].get("auto_advance"):
            data = turn(sid, "yay!")
            T("child: yay!", data)
            check(data, "followup", activity)

    transcripts.append(f"  RESULT: {data['session_state']['status']} at {data['session_state']['current_step']}")


# ============================================================
# ALL COMBINATIONS
# ============================================================

if __name__ == "__main__":
    start_time = time.time()

    # --- DOG: 4 combos ---
    run_cat1(
        "dog.png",
        "dog",
        "enthusiastic",
        hook_reply="oh wow those ears are so floppy and cute!",
        rules_reply="yes yes yes lets play!",
        round_replies=[
            "the dog says YAY SUNSHINE I LOVE IT!",
            "oh no he says OUCH MY BUTT HURTS!",
            "GIMME GIMME GIMME that treat!",
        ],
    )

    run_cat1(
        "dog.png",
        "dog",
        "shy",
        hook_reply="SILENCE",
        rules_reply="SILENCE",
        round_replies=["SILENCE", "um... sad?", "i think happy"],
    )

    run_cat1(
        "dog.png",
        "dog",
        "silly",
        hook_reply="that dog looks like a potato!",
        rules_reply="only if the dog can fly",
        round_replies=[
            "the dog would eat the sunshine!",
            "he would do a backflip!",
            "the dog says PIZZA PIZZA PIZZA!",
        ],
    )

    run_cat1(
        "dog.png",
        "dog",
        "resistant",
        hook_reply="i dont like dogs",
        rules_reply="no thanks",
        extra_interactions={
            "pre_accept": [
                ("decline", "no thanks"),
            ]
        },
        round_replies=[],
    )

    # --- CAT: 3 combos ---
    run_cat1(
        "cat.png",
        "cat",
        "enthusiastic",
        hook_reply="the cat is dreaming about fish!",
        rules_reply="yes i love dreams!",
        round_replies=[
            "the cat flies through candy clouds!",
            "it finds a golden ball of yarn!",
            "the cat builds a castle of pillows!",
        ],
    )

    run_cat1("cat.png", "cat", "minimal", hook_reply="cool", rules_reply="ok", round_replies=["clouds", "fish", "yarn"])

    run_cat1(
        "cat.png",
        "cat",
        "confused",
        hook_reply="what is this?",
        rules_reply="i dont understand",
        round_replies=["SILENCE", "i dont know", "SILENCE"],
    )

    # --- DINOSAUR: 3 combos ---
    run_cat1(
        "dinosaur.png",
        "dino",
        "enthusiastic",
        hook_reply="RAWR that dinosaur is AMAZING!",
        rules_reply="LETS GO TIME TRAVEL!",
        round_replies=[
            "the dino eats all the prehistoric fruit!",
            "it surfs on the lava like a skateboard!",
            "the dino makes friends with the fish!",
        ],
    )

    run_cat1(
        "dinosaur.png",
        "dino",
        "scared",
        hook_reply="those teeth are scary...",
        rules_reply="ok but will it be safe?",
        round_replies=[
            "the dino hides behind a tree",
            "SILENCE",
            "it tiptoes quietly past",
        ],
    )

    run_cat1(
        "dinosaur.png",
        "dino",
        "creative",
        hook_reply="i think its a friendly vegetarian dino",
        rules_reply="sure but only if we bring snacks",
        round_replies=[
            "it plants a garden in the jungle!",
            "the dino invents a fire extinguisher!",
            "it throws a pool party for all the other dinos!",
        ],
    )

    # --- POLKA DOT: 5 combos ---
    run_cat5(
        "ladybug.png",
        "polka",
        "perfect_run",
        hook_reply="so many dots!",
        mission_reply="yes i love finding dots!",
        round_behaviors=["correct", "correct", "correct"],
        synthesis_reply="lets call them spotty, dotty, and freckles!",
    )

    run_cat5(
        "ladybug.png",
        "polka",
        "struggling",
        hook_reply="whats a polka dot?",
        mission_reply="i guess so",
        round_behaviors=["wrong_then_correct", "silence_then_correct", "wrong_then_correct"],
        synthesis_reply="i dont know what to name them",
    )

    run_cat5(
        "ladybug.png",
        "polka",
        "gives_up",
        hook_reply="its red",
        mission_reply="ok",
        round_behaviors=["correct", "wrong_wrong"],
    )

    run_cat5(
        "ladybug.png",
        "polka",
        "offtopic",
        hook_reply="i had cereal for breakfast!",
        mission_reply="sure why not",
        round_behaviors=["offtopic_then_correct", "offtopic_then_correct", "correct"],
        synthesis_reply="they all look like little planets!",
    )

    run_cat5(
        "ladybug.png",
        "polka",
        "declines_then_plays",
        hook_reply="those dots are interesting",
        mission_reply="yes ok lets go!",
        extra_interactions={
            "pre_accept": [
                ("decline", "no i dont want to"),
            ]
        },
        round_behaviors=["correct", "correct", "correct"],
        synthesis_reply="i want to make a dot museum!",
    )

    # --- DANDELION: 4 combos ---
    run_cat5(
        "dandelion.png",
        "fluffy",
        "enthusiastic",
        hook_reply="its like a cloud on a stick!",
        mission_reply="yes lets find all the fluffy things!",
        round_behaviors=["correct", "correct", "correct"],
        synthesis_reply="this one feels like cotton candy and that one is like a bunny!",
    )

    run_cat5(
        "dandelion.png",
        "fluffy",
        "cautious",
        hook_reply="can i blow on it?",
        mission_reply="ok but what if i cant find any?",
        round_behaviors=["silence_then_correct", "wrong_then_correct", "correct"],
        synthesis_reply="they are all different kinds of soft!",
    )

    run_cat5(
        "dandelion.png",
        "fluffy",
        "two_wrong_exit",
        hook_reply="its white",
        mission_reply="fine",
        round_behaviors=["wrong_wrong"],
    )

    run_cat5(
        "dandelion.png",
        "fluffy",
        "creative",
        hook_reply="the dandelion is sending secret messages to the wind!",
        mission_reply="yes i want to be a fluff detective!",
        round_behaviors=["correct", "correct", "correct"],
        synthesis_reply="lets sort them by how much they tickle!",
    )

    elapsed = time.time() - start_time

    # Print all transcripts
    print("\n".join(transcripts))

    print(f"\n{'=' * 70}")
    print(f"ALL COMBINATIONS COMPLETE  ({elapsed:.1f}s)")
    print("  Cat1: 10 runs  |  Cat5: 9 runs  |  Total: 19 runs")
    print("=" * 70)

    if issues:
        print(f"\n⚠ {len(issues)} ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("\n✓ No issues found across all 19 combinations")
        sys.exit(0)
