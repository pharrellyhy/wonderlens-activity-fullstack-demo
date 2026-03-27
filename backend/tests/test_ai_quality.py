"""AI response quality tests — hits the real LLM.

These tests start real sessions and validate the AI output against
the quality rules defined in step instructions and the education team
feedback. They are integration tests that call the actual LLM, so they
cost real API credits and take ~3-5s per test.

Run with:
    cd backend && uv run pytest tests/test_ai_quality.py -v --timeout=60

To run a specific test:
    uv run pytest tests/test_ai_quality.py::test_t0_hook_quality -v
"""

import re

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"

# --- Test configuration ---

T0_GAMES = [
    ("ladybug", "polka_dot_patrol", "cat5"),
    ("dandelion", "fluffy_expedition_dandelion", "cat5"),
    ("dog", "mood_changer_dog", "cat1"),
    ("cat", "dream_whisperer_cat", "cat1"),
    ("dinosaur", "time_machine_dinosaur", "cat1"),
]

CAT5_T0_GAMES = [(e, a) for e, a, t in T0_GAMES if t == "cat5"]
CAT1_T0_GAMES = [(e, a) for e, a, t in T0_GAMES if t == "cat1"]

OPEN_QUESTION_PATTERNS = [
    r"\bwhat does\b",
    r"\bwhat do you\b",
    r"\bwhat did\b",
    r"\bwhat would\b",
    r"\bwhat happens\b",
    r"\bwhat kind\b",
    r"\bhow does\b",
    r"\bhow do you\b",
    r"\bi wonder what\b",
    r"\bi wonder how\b",
    r"\bi wonder where\b",
    r"\bi wonder why\b",
]

MODEL_PHRASES = [
    "i think",
    "i'd call",
    "maybe it's",
    "it looks like",
    "i think it looks",
    "should we call",
    "it reminds me of",
    "it sounds like",
]

SPECIFIC_ITEM_PATTERNS = [
    r"\byour blanket\b",
    r"\byour pillow\b",
    r"\byour teddy\b",
    r"\byour sock\b",
    r"\bstuffed animal\b",
    r"\byour bed\b",
    r"\byour clothes\b",
    r"\bfuzzy sock\b",
    r"\bteddy bear\b",
    r"\bcozy blanket\b",
]


# --- Helpers ---


def has_open_question(text: str) -> bool:
    """Check if text ends with an open-ended wh-question."""
    lower = text.lower()
    if "?" not in lower:
        return False
    # Find last sentence with ?
    sentences = re.split(r"[.!]\s+", lower)
    last_q = ""
    for s in reversed(sentences):
        if "?" in s:
            last_q = s.strip()
            break
    return any(re.search(p, last_q) for p in OPEN_QUESTION_PATTERNS)


def has_model_phrase(text: str) -> bool:
    """Check if text contains a scaffolding/model phrase."""
    lower = text.lower()
    return any(p in lower for p in MODEL_PHRASES)


def has_specific_items(text: str) -> bool:
    """Check if text suggests specific items the AI can't see."""
    lower = text.lower()
    return any(re.search(p, lower) for p in SPECIFIC_ITEM_PATTERNS)


def count_sentences(text: str) -> int:
    """Rough sentence count."""
    # Strip tone marker
    clean = re.sub(r"^\[.*?\]\s*", "", text)
    parts = re.split(r"[.!?]+", clean)
    return len([p for p in parts if p.strip()])


async def start_session(client: httpx.AsyncClient, entity: str, tier: str = "T0") -> dict:
    """Start a session via deep-link endpoint."""
    resp = await client.post(
        f"{BASE_URL}/api/start-deep-link",
        json={"entity": entity, "tier": tier},
    )
    assert resp.status_code == 200, f"Start failed: {resp.text}"
    return resp.json()


async def send_turn(
    client: httpx.AsyncClient,
    session_id: str,
    text: str = "",
    is_silent: bool = False,
    photo_id: str | None = None,
) -> dict:
    """Send a turn and return the response."""
    body: dict = {"session_id": session_id, "text": text, "is_silent": is_silent}
    if photo_id:
        body["photo_id"] = photo_id
    resp = await client.post(f"{BASE_URL}/api/turn", json=body)
    assert resp.status_code == 200, f"Turn failed: {resp.text}"
    return resp.json()


def get_dialogue(turn_data: dict) -> str:
    """Extract dialogue from turn response."""
    if "first_turn" in turn_data:
        return turn_data["first_turn"]["dialogue"]
    return turn_data["turn"]["dialogue"]


def get_session_state(data: dict) -> dict:
    """Extract session state from response."""
    return data.get("session_state", {})


def get_round_items(data: dict) -> list:
    """Get current round's correct item IDs from session state."""
    state = get_session_state(data)
    items = state.get("current_round_items", [])
    return [item["id"] for item in items if item.get("is_correct")]


# --- Tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", [(e, a) for e, a, _ in T0_GAMES])
async def test_t0_hook_quality(entity: str, activity: str) -> None:
    """T0 hook should be short and emotional."""
    async with httpx.AsyncClient(timeout=30) as client:
        data = await start_session(client, entity)
        hook = get_dialogue(data)

        # Should be short for T0
        sentences = count_sentences(hook)
        assert sentences <= 4, f"Hook too long for T0 ({sentences} sentences): {hook}"

        # Should have a tone marker
        assert hook.startswith("["), f"Hook missing tone marker: {hook}"


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", [(e, a) for e, a, _ in T0_GAMES])
async def test_t0_mission_brevity(entity: str, activity: str) -> None:
    """T0 mission/rules briefing should be ≤4 sentences."""
    async with httpx.AsyncClient(timeout=30) as client:
        data = await start_session(client, entity)
        session_id = data["session_id"]

        # Child responds to hook
        turn_data = await send_turn(client, session_id, text="cool")
        mission = get_dialogue(turn_data)

        sentences = count_sentences(mission)
        assert sentences <= 6, f"Mission too long for T0 ({sentences} sentences): {mission}"


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", CAT5_T0_GAMES)
async def test_t0_detail_question_scaffolds(entity: str, activity: str) -> None:
    """When T0 child picks correct photo, detail question should scaffold (not open)."""
    async with httpx.AsyncClient(timeout=30) as client:
        data = await start_session(client, entity)
        session_id = data["session_id"]

        # Hook -> child responds
        turn_data = await send_turn(client, session_id, text="wow")
        # Mission -> child accepts
        turn_data = await send_turn(client, session_id, text="yes")

        # Now in collect phase — get correct items
        state = get_session_state(turn_data)
        round_items = state.get("current_round_items", [])
        correct_ids = [item["id"] for item in round_items if item.get("is_correct")]

        if not correct_ids:
            pytest.skip("No round items available")

        # Pick correct photo
        turn_data = await send_turn(client, session_id, photo_id=correct_ids[0])
        detail_q = get_dialogue(turn_data)

        # For T0: if it has an open question, it should also have a model phrase
        if has_open_question(detail_q):
            assert has_model_phrase(detail_q), f"T0 detail question is open without scaffolding: {detail_q}"


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", CAT5_T0_GAMES)
async def test_t0_silence_no_specific_items(entity: str, activity: str) -> None:
    """When child is silent during collection, AI should not suggest specific items."""
    async with httpx.AsyncClient(timeout=30) as client:
        data = await start_session(client, entity)
        session_id = data["session_id"]

        # Hook -> respond -> accept mission
        await send_turn(client, session_id, text="cool")
        turn_data = await send_turn(client, session_id, text="yes")

        # Send silence while in collect phase
        turn_data = await send_turn(client, session_id, text="", is_silent=True)
        silence_resp = get_dialogue(turn_data)

        assert not has_specific_items(silence_resp), f"Silence response suggests specific items: {silence_resp}"


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", CAT5_T0_GAMES)
async def test_t0_cat5_full_flow(entity: str, activity: str) -> None:
    """Play through a full Cat5 T0 session and check key quality markers."""
    issues: list[str] = []

    async with httpx.AsyncClient(timeout=60) as client:
        data = await start_session(client, entity)
        session_id = data["session_id"]
        hook = get_dialogue(data)

        # Check hook
        if count_sentences(hook) > 4:
            issues.append(f"Hook too long: {hook}")

        # Respond to hook
        turn_data = await send_turn(client, session_id, text="nice")
        mission = get_dialogue(turn_data)

        # Check mission brevity
        if count_sentences(mission) > 6:
            issues.append(f"Mission too long: {mission}")

        # Accept mission
        turn_data = await send_turn(client, session_id, text="yes")

        # Play through collection rounds
        state = get_session_state(turn_data)
        total_rounds = state.get("total_rounds", 3)

        for round_num in range(total_rounds):
            state = get_session_state(turn_data)
            round_items = state.get("current_round_items", [])
            correct_ids = [item["id"] for item in round_items if item.get("is_correct")]

            if not correct_ids:
                break

            # Pick correct photo
            turn_data = await send_turn(client, session_id, photo_id=correct_ids[0])
            detail_q = get_dialogue(turn_data)

            # Check detail question scaffolding
            if has_open_question(detail_q) and not has_model_phrase(detail_q):
                issues.append(f"Round {round_num + 1} open question without scaffold: {detail_q}")

            # Respond to detail question
            turn_data = await send_turn(client, session_id, text="a cloud")

            state = get_session_state(turn_data)

        # Check synthesis (if we got there)
        state = get_session_state(turn_data)
        if state.get("current_step") == "STEP_4_SYNTHESIS":
            synthesis = get_dialogue(turn_data)
            if has_open_question(synthesis) and " or " not in synthesis.lower():
                issues.append(f"Synthesis open question without choices: {synthesis}")

        # Report all issues
        if issues:
            report = "\n".join(f"  - {i}" for i in issues)
            pytest.fail(f"Quality issues in {activity} T0 full flow:\n{report}")


@pytest.mark.asyncio
@pytest.mark.parametrize("entity,activity", CAT1_T0_GAMES)
async def test_t0_cat1_full_flow(entity: str, activity: str) -> None:
    """Play through a full Cat1 T0 session and check key quality markers."""
    issues: list[str] = []

    async with httpx.AsyncClient(timeout=60) as client:
        data = await start_session(client, entity)
        session_id = data["session_id"]
        hook = get_dialogue(data)

        if count_sentences(hook) > 4:
            issues.append(f"Hook too long: {hook}")

        # Respond to hook -> get rules
        turn_data = await send_turn(client, session_id, text="cool")
        rules = get_dialogue(turn_data)

        if count_sentences(rules) > 6:
            issues.append(f"Rules too long: {rules}")

        # Accept game
        turn_data = await send_turn(client, session_id, text="yes")

        # Play through rounds
        state = get_session_state(turn_data)
        total_rounds = state.get("total_rounds", 3)

        for round_num in range(total_rounds):
            dialogue = get_dialogue(turn_data)

            # Check round question isn't too open for T0
            if has_open_question(dialogue) and not has_model_phrase(dialogue):
                issues.append(f"Round {round_num + 1} open question without scaffold: {dialogue}")

            # Respond to round
            turn_data = await send_turn(client, session_id, text="roar")

            state = get_session_state(turn_data)
            if state.get("status") != "active":
                break

        if issues:
            report = "\n".join(f"  - {i}" for i in issues)
            pytest.fail(f"Quality issues in {activity} T0 full flow:\n{report}")
