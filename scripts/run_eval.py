#!/usr/bin/env python3
"""CLI entrypoint for the LLM-driven eval system.

Usage:
    uv run python scripts/run_eval.py
    uv run python scripts/run_eval.py --entity dandelion --tier T0
    uv run python scripts/run_eval.py --sessions 3
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_DIR = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import game_loader
import httpx
from config import get_settings

# game_loader populates the entity registry at import time.
# Reference it to satisfy linters that it's not an unused import.
_ = game_loader
from entity_registry import get_collection_catalog, lookup_by_entity_name
from eval.child_sim import ChildSimulator, pick_persona
from eval.judge import EvalJudge
from eval.report import generate_markdown_report, generate_summary_json
from eval.rubrics import EvalConfig, SessionTranscript, load_eval_config
from eval.runner import run_single_session
from scoring import score_cross_session_variety

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_correct_items(activity: str) -> list[list[str]]:
    """Load correct item IDs per round from entity registry."""
    catalog = get_collection_catalog(activity)
    if not catalog:
        return []
    return [[item.id] for item in catalog.correct]


async def run_eval(config: EvalConfig) -> int:
    """Run full eval and return exit code (0=pass, 1=fail)."""
    settings = get_settings()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    output_dir = REPO_ROOT / config.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcripts").mkdir(exist_ok=True)

    # Use the same OpenAI-compatible endpoint the game uses for classification
    api_key = settings.dashscope_api_key or settings.gemini_api_key or settings.openai_api_key
    base_url = (
        settings.dashscope_base_url or settings.openai_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    child_sim = ChildSimulator(
        model=config.child_sim_model,
        api_key=api_key,
        base_url=base_url,
    )
    judge = EvalJudge(
        model=config.judge_model,
        api_key=api_key,
        base_url=base_url,
    )

    all_transcripts: list[SessionTranscript] = []
    all_judgements = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        for entity_name in config.entities:
            entity_cfg = lookup_by_entity_name(entity_name)
            activity_type = entity_cfg.activity_type if entity_cfg else entity_name
            correct_items = _load_correct_items(activity_type)
            for tier in config.tiers:
                session_dialogues: list[list[str]] = []
                for session_n in range(config.sessions_per_combo):
                    persona = pick_persona(tier)
                    print(f"  [{entity_name} ({activity_type}) {tier} #{session_n + 1}] persona={persona.name}")

                    transcript = await run_single_session(
                        client=client,
                        child_sim=child_sim,
                        activity=entity_name,
                        tier=tier,
                        persona_name=persona.name,
                        correct_items_by_round=correct_items,
                        config=config,
                    )

                    t_path = output_dir / "transcripts" / f"{activity_type}_{tier}_{session_n}.json"
                    t_path.write_text(transcript.model_dump_json(indent=2))

                    judgement = await judge.judge_session(transcript)
                    all_transcripts.append(transcript)
                    all_judgements.append(judgement)

                    session_dialogues.append([t.ai_dialogue for t in transcript.turns])

                if len(session_dialogues) >= 2:
                    variety = score_cross_session_variety(session_dialogues)
                    print(f"  [{entity_name} {tier}] cross-session variety: {variety:.0%}")

    summary = generate_summary_json(all_transcripts, all_judgements, config.thresholds)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    md = generate_markdown_report(all_transcripts, all_judgements, config.thresholds)
    (output_dir / "report.md").write_text(md)

    print(f"\nResults saved to {output_dir}/")
    print(f"Status: {summary['status']}")

    return 0 if summary["status"] == "PASS" else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM-driven eval for Cat5 games")
    parser.add_argument("--entity", help="Specific entity to eval (e.g. dandelion, ladybug)")
    parser.add_argument("--tier", help="Specific tier to eval")
    parser.add_argument("--sessions", type=int, help="Sessions per entity/tier combo")
    parser.add_argument("--min-score", type=int, help="Override minimum combined score threshold")
    parser.add_argument("--config", type=Path, help="Path to eval config YAML")
    args = parser.parse_args()

    config = load_eval_config(args.config)

    if args.entity:
        config.entities = [args.entity]
    if args.tier:
        config.tiers = [args.tier]
    if args.sessions:
        config.sessions_per_combo = args.sessions
    if args.min_score:
        config.thresholds.combined_score_min = args.min_score

    print(
        f"Running eval: {len(config.entities)} entities"
        f" x {len(config.tiers)} tiers"
        f" x {config.sessions_per_combo} sessions"
    )
    exit_code = asyncio.run(run_eval(config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
