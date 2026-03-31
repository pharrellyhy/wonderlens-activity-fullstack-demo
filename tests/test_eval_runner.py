"""Integration test for the eval runner — mocked LLMs, real scoring."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.rubrics import ChildSimResponse, EvalConfig
from eval.runner import run_single_session


@pytest.mark.asyncio
async def test_run_single_session_completes() -> None:
    """A mocked session should produce a transcript with turns and scores."""
    config = EvalConfig(
        sessions_per_combo=1,
        entities=["dandelion"],
        tiers=["T0"],
        server_url="http://localhost:8000",
    )

    mock_start_response = {
        "session_id": "eval-test-1",
        "first_turn": {"dialogue": "[excited] Wow fluffy!"},
        "session_state": {
            "current_step": "STEP_1_HOOK",
            "status": "active",
            "collection_phase": "photo",
            "collected_photos": [],
            "total_rounds": 2,
            "current_round_items": [],
        },
    }
    mock_turn_response = {
        "turn": {"dialogue": "[playful] Let's find more!", "auto_advance": False},
        "session_state": {
            "current_step": "STEP_6_CLOSING",
            "status": "completed",
            "collection_phase": "photo",
            "collected_photos": ["fuzzy_moss"],
            "total_rounds": 2,
            "current_round_items": [],
        },
    }

    mock_client = AsyncMock()

    start_resp = MagicMock()
    start_resp.status_code = 200
    start_resp.json.return_value = mock_start_response

    turn_resp = MagicMock()
    turn_resp.status_code = 200
    turn_resp.json.return_value = mock_turn_response

    mock_client.post = AsyncMock(side_effect=[start_resp, turn_resp])

    mock_child_sim = AsyncMock()
    mock_child_sim.generate = AsyncMock(return_value=ChildSimResponse(text="wow"))

    transcript = await run_single_session(
        client=mock_client,
        child_sim=mock_child_sim,
        activity="fluffy_expedition_dandelion",
        tier="T0",
        persona_name="curious_toddler",
        correct_items_by_round=[["fuzzy_moss"], ["fluffy_seed"]],
        config=config,
    )

    assert transcript.session_id == "eval-test-1"
    assert transcript.activity == "fluffy_expedition_dandelion"
    assert len(transcript.turns) >= 1
    assert transcript.final_status == "completed"
