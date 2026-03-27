"""Full integration test for all 5 activities with realistic child interactions.

Mimics real user behavior: correct answers, wrong answers, off-topic responses,
"I don't know", silence, and proper step flow.
"""

import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
ICONS_DIR = str(Path(__file__).resolve().parent.parent / "frontend" / "public" / "icons")

# Track issues
issues: list[str] = []


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


def pick_until_correct(sid: str, items: list[dict], label: str, activity: str) -> dict:
    """Pick items one at a time until we find the correct one. Max 1 wrong pick to stay safe."""
    for i, item in enumerate(items):
        data = turn(sid, photo_id=item["id"])
        rtype = data.get("turn", {}).get("response_type", "")
        if rtype == "wrong_photo":
            log(f"{label} wrong: {item['id']}", data)
            check_response(data, f"{label} wrong", activity)
        else:
            log(f"{label} correct: {item['id']}", data)
            check_response(data, f"{label} correct", activity)
            return data
    return data


def pick_and_detail(
    sid: str,
    items: list[dict],
    detail_response: str,
    label: str,
    activity: str,
) -> dict:
    """Cat5 2-phase: pick correct photo (Phase A), then respond to detail question (Phase B).

    Returns the data from the Phase B response (which advances to the next round).
    """
    # Phase A: pick until we find the correct photo
    data = pick_until_correct(sid, items, label, activity)

    # Verify we entered detail phase
    phase = data.get("session_state", {}).get("collection_phase", "photo")
    if phase != "detail":
        log(f"{label} WARN: expected detail phase, got {phase}", data)
        return data

    # Phase B: respond to the detail-harvesting question
    data = turn(sid, detail_response)
    log(f"{label} detail: {detail_response[:40]}", data)
    check_response(data, f"{label} detail", activity)

    # Auto-advance if flagged (e.g. final round → synthesis)
    if data["turn"].get("auto_advance"):
        data = turn(sid)
        log(f"auto→{data['session_state']['current_step']}", data)
        check_response(data, f"{label} auto-advance", activity)

    return data


def check_response(data: dict, label: str, activity: str) -> None:
    """Flag any suspicious LLM responses."""
    dialogue = data["turn"]["dialogue"]
    step = data["session_state"]["current_step"]
    rtype = data["turn"]["response_type"]
    session = data["session_state"]

    # Check for empty dialogue
    if not dialogue.strip():
        issues.append(f"[{activity}] EMPTY dialogue at {step} ({label})")

    # Check for missing emotion tag
    if dialogue and not dialogue.startswith("["):
        issues.append(f"[{activity}] Missing emotion tag at {step}: {dialogue[:60]}")

    # Cat5 2-phase: verify phase transitions are consistent
    if step.startswith("STEP_3_COLLECT_"):
        phase = session.get("collection_phase", "photo")
        collected = len(session.get("collected_photos", []))
        total = session.get("total_rounds", 0)
        remaining = total - collected

        # After correct photo: should be in detail phase
        if "correct" in label.lower() and rtype != "wrong_photo":
            if phase != "detail":
                issues.append(f"[{activity}] Expected detail phase after correct pick at {step}, got {phase} ({label})")

        # Premature completion language during collection
        if remaining > 0:
            for bad_word in ["all done", "mission complete", "collection complete", "found them all"]:
                if bad_word in dialogue.lower():
                    issues.append(
                        f"[{activity}] Premature completion '{bad_word}' at {step} "
                        f"(collected {collected}/{total}): {dialogue[:80]}"
                    )

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
        idx = 0
        while idx < len(dialogue_lower):
            pos = dialogue_lower.find(d, idx)
            if pos == -1:
                break
            lookback = dialogue_lower[max(0, pos - 60) : pos]
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


def log(label: str, data: dict) -> None:
    d = data["turn"]["dialogue"]
    step = data["session_state"]["current_step"]
    rtype = data["turn"]["response_type"]
    status = data["session_state"]["status"]
    auto = data["turn"].get("auto_advance", False)
    print(f"  {label:30s} → [{rtype:15s}] {step:20s} auto={auto} status={status}")
    print(f"    AI: {d[:120]}{'...' if len(d) > 120 else ''}")


# ============================================================
# CAT 1: mood_changer_dog
# ============================================================
def test_mood_changer_dog():
    print("\n{'='*60}")
    print("ACTIVITY 1: mood_changer_dog (Cat1)")
    print("=" * 60)
    sid, start = start_session("dog.png")
    print(f"  Hook: {start['first_turn']['dialogue'][:120]}")

    # Off-topic response to hook
    data = turn(sid, "i like pizza")
    log("off-topic to hook", data)
    check_response(data, "off-topic to hook", "dog")

    # Accept invitation
    data = turn(sid, "ok sure lets play!")
    log("accept invitation", data)
    check_response(data, "accept invitation", "dog")

    # Round 1: good answer
    data = turn(sid, "the dog would say woof woof im so happy!")
    log("R1 good answer", data)
    check_response(data, "R1 good answer", "dog")

    # Auto-advance to R2
    if data["turn"].get("auto_advance"):
        data = turn(sid)
        log("auto→R2", data)

    # Round 2: "I don't know"
    data = turn(sid, "i dont know what it would say")
    log("R2 confused", data)
    check_response(data, "R2 confused", "dog")

    # Round 2: answer after hint
    data = turn(sid, "maybe it says ouch that hurt!")
    log("R2 after hint", data)
    check_response(data, "R2 after hint", "dog")

    # Auto-advance to R3
    if data["turn"].get("auto_advance"):
        data = turn(sid)
        log("auto→R3", data)

    # Round 3: answer
    data = turn(sid, "the dog says YUM YUM GIMME MORE TREATS!")
    log("R3 answer", data)
    check_response(data, "R3 answer", "dog")

    # Follow through to completion
    for i in range(6):
        step = data["session_state"]["current_step"]
        status = data["session_state"]["status"]
        if status != "active":
            break
        auto = data["turn"].get("auto_advance", False)
        if auto:
            data = turn(sid)
            log(f"auto→{data['session_state']['current_step']}", data)
        else:
            data = turn(sid, "that was really fun!")
            log(f"reply at {step}", data)
        check_response(data, f"followup-{i}", "dog")

    print(f"  FINAL: status={data['session_state']['status']}, step={data['session_state']['current_step']}")


# ============================================================
# CAT 1: dream_whisperer_cat
# ============================================================
def test_dream_whisperer_cat():
    print(f"\n{'=' * 60}")
    print("ACTIVITY 2: dream_whisperer_cat (Cat1)")
    print("=" * 60)
    sid, start = start_session("cat.png")
    print(f"  Hook: {start['first_turn']['dialogue'][:120]}")

    # Respond to hook
    data = turn(sid, "oh the cat looks so sleepy and cute!")
    log("hook reply", data)
    check_response(data, "hook reply", "cat")

    # Decline invitation first time
    data = turn(sid, "no i dont want to play right now")
    log("decline #1", data)
    check_response(data, "decline #1", "cat")

    # Accept on re-invite
    data = turn(sid, "actually ok lets try it")
    log("accept after decline", data)
    check_response(data, "accept after decline", "cat")

    # Play through rounds
    child_responses = [
        "the cat dreams about flying over rainbows!",
        "it dreams about a giant fish",
        "maybe the cat dreams about playing with yarn",
    ]
    for i, resp_text in enumerate(child_responses):
        if data["session_state"]["status"] != "active":
            break
        if data["turn"].get("auto_advance"):
            data = turn(sid)
            log("auto-advance", data)
        data = turn(sid, resp_text)
        log(f"R{i + 1}: {resp_text[:30]}", data)
        check_response(data, f"R{i + 1}", "cat")

    # Follow through to completion
    for i in range(6):
        if data["session_state"]["status"] != "active":
            break
        if data["turn"].get("auto_advance"):
            data = turn(sid)
            log(f"auto→{data['session_state']['current_step']}", data)
        else:
            data = turn(sid, "that was fun!")
            log("reply", data)
        check_response(data, f"cat-end-{i}", "cat")

    print(f"  FINAL: status={data['session_state']['status']}, step={data['session_state']['current_step']}")


# ============================================================
# CAT 1: time_machine_dinosaur
# ============================================================
def test_time_machine_dinosaur():
    print(f"\n{'=' * 60}")
    print("ACTIVITY 3: time_machine_dinosaur (Cat1)")
    print("=" * 60)
    sid, start = start_session("dinosaur.png")
    print(f"  Hook: {start['first_turn']['dialogue'][:120]}")

    # Quick accept
    data = turn(sid, "wow a dinosaur! yes!")
    log("accept", data)
    check_response(data, "accept", "dino")

    # Accept rules
    data = turn(sid, "yeah lets go!")
    log("accept rules", data)
    check_response(data, "accept rules", "dino")

    # R1: answer
    data = turn(sid, "the dinosaur says ROARRRR watch out!")
    log("R1 answer", data)
    check_response(data, "R1", "dino")

    if data["turn"].get("auto_advance"):
        data = turn(sid)
        log("auto→R2", data)

    # R2: silence
    data = turn(sid, silent=True)
    log("R2 silence", data)
    check_response(data, "R2 silence", "dino")

    # R2: answer after silence hint
    data = turn(sid, "the volcano is scary! run away!")
    log("R2 answer", data)
    check_response(data, "R2 answer", "dino")

    if data["turn"].get("auto_advance"):
        data = turn(sid)
        log("auto→R3", data)

    # R3: answer
    data = turn(sid, "the dino is swimming and splashing")
    log("R3 answer", data)
    check_response(data, "R3 answer", "dino")

    # Follow through
    for i in range(6):
        if data["session_state"]["status"] != "active":
            break
        if data["turn"].get("auto_advance"):
            data = turn(sid)
            log(f"auto→{data['session_state']['current_step']}", data)
        else:
            data = turn(sid, "cool!")
            log("reply", data)
        check_response(data, f"dino-end-{i}", "dino")

    print(f"  FINAL: status={data['session_state']['status']}, step={data['session_state']['current_step']}")


# ============================================================
# CAT 5: polka_dot_patrol
# ============================================================
def test_polka_dot_patrol():
    print(f"\n{'=' * 60}")
    print("ACTIVITY 4: polka_dot_patrol (Cat5) — 2-phase collection")
    print("=" * 60)
    sid, start = start_session("ladybug.png")
    print(f"  Hook: {start['first_turn']['dialogue'][:120]}")

    # Engage with hook
    data = turn(sid, "the dots look like little eyes!")
    log("hook reply", data)
    check_response(data, "hook reply", "polka")

    # Accept mission
    data = turn(sid, "yes i want to find dots!")
    log("accept mission", data)
    check_response(data, "accept mission", "polka")

    # R1: Phase A (pick correct photo) → Phase B (describe observation)
    items = data["session_state"].get("current_round_items", [])
    data = pick_and_detail(sid, items, "the dots on this are really big and round!", "R1", "polka")

    # R2: Phase A → Phase B
    items = data["session_state"].get("current_round_items", [])
    if items:
        data = pick_and_detail(sid, items, "these are tiny speckles not big dots!", "R2", "polka")

    # R3: Phase A → Phase B (last round — auto-advances to synthesis)
    items = data["session_state"].get("current_round_items", [])
    if items:
        data = pick_and_detail(sid, items, "perfect little circles like polka dots!", "R3", "polka")

    # Verify collected details made it through
    details = data.get("session_state", {}).get("collected_details", [])
    print(f"  Collected details: {details}")

    # Synthesis: compare finds using observations from collection (comparison_chart style)
    if data["session_state"]["current_step"] == "STEP_4_SYNTHESIS":
        data = turn(sid, "the mushroom dots are the biggest and the leaf speckles are the tiniest!")
        log("synthesis: comparison", data)
        check_response(data, "synthesis comparison", "polka")

    # Follow through to completion
    for i in range(6):
        if data["session_state"]["status"] != "active":
            break
        if data["turn"].get("auto_advance"):
            data = turn(sid)
            log(f"auto→{data['session_state']['current_step']}", data)
        else:
            data = turn(sid, "yay!")
            log("reply", data)
        check_response(data, f"polka-end-{i}", "polka")

    print(f"  FINAL: status={data['session_state']['status']}, step={data['session_state']['current_step']}")


# ============================================================
# CAT 5: fluffy_expedition_dandelion
# ============================================================
def test_fluffy_expedition_dandelion():
    print(f"\n{'=' * 60}")
    print("ACTIVITY 5: fluffy_expedition_dandelion (Cat5) — 2-phase collection")
    print("=" * 60)
    sid, start = start_session("dandelion.png")
    print(f"  Hook: {start['first_turn']['dialogue'][:120]}")

    # Respond to hook
    data = turn(sid, "its so fluffy and white!")
    log("hook reply", data)
    check_response(data, "hook reply", "fluffy")

    # Decline first
    data = turn(sid, "nah i dont feel like it")
    log("decline #1", data)
    check_response(data, "decline #1", "fluffy")

    # Accept on re-invite
    data = turn(sid, "ok fine lets try it")
    log("accept after decline", data)
    check_response(data, "accept", "fluffy")

    # R1: Phase A (pick correct photo) → Phase B (name character from detail)
    items = data["session_state"].get("current_round_items", [])
    data = pick_and_detail(sid, items, "it reminds me of a little cloud!", "R1", "fluffy")

    # R2: Phase A → Phase B
    items = data["session_state"].get("current_round_items", [])
    if items:
        data = pick_and_detail(sid, items, "like a tiny pillow for a fairy!", "R2", "fluffy")

    # R3: Phase A → Phase B (last round — auto-advances to synthesis)
    items = data["session_state"].get("current_round_items", [])
    if items:
        data = pick_and_detail(sid, items, "it tickles like a fuzzy caterpillar!", "R3", "fluffy")

    # Verify collected details and names made it through
    details = data.get("session_state", {}).get("collected_details", [])
    names = data.get("session_state", {}).get("collected_names", [])
    print(f"  Collected details: {details}")
    print(f"  Collected names: {names}")

    # Synthesis: naming_story — create a story using the named characters from collection
    if data["session_state"]["current_step"] == "STEP_4_SYNTHESIS":
        data = turn(sid, "Cloud Puff and Fairy Pillow go on a fluffy adventure together!")
        log("synthesis: naming story", data)
        check_response(data, "synthesis naming story", "fluffy")

    # Follow through to completion
    for i in range(6):
        if data["session_state"]["status"] != "active":
            break
        if data["turn"].get("auto_advance"):
            data = turn(sid)
            log(f"auto→{data['session_state']['current_step']}", data)
        else:
            data = turn(sid, "bye bye!")
            log("reply", data)
        check_response(data, f"fluffy-end-{i}", "fluffy")

    print(f"  FINAL: status={data['session_state']['status']}, step={data['session_state']['current_step']}")


# ============================================================
# RUN ALL
# ============================================================
if __name__ == "__main__":
    start_time = time.time()

    test_mood_changer_dog()
    test_dream_whisperer_cat()
    test_time_machine_dinosaur()
    test_polka_dot_patrol()
    test_fluffy_expedition_dandelion()

    elapsed = time.time() - start_time

    print(f"\n{'=' * 60}")
    print(f"ALL 5 ACTIVITIES COMPLETE  ({elapsed:.1f}s)")
    print("=" * 60)

    if issues:
        print(f"\n⚠ {len(issues)} ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("\n✓ No issues found in LLM responses")
        sys.exit(0)
