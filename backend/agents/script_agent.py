"""Script Agent — generates voice/text content using Gemini 2.0 Flash."""

import asyncio
import time
from functools import lru_cache
from pathlib import Path

import yaml
from google import genai
from google.genai import types

try:
    from ..config import get_settings
    from ..db import log_agent_call
    from ..logger import setup_logger
    from ..schemas import CompositionPlan, VoiceScript
except ImportError:
    from config import get_settings
    from db import log_agent_call
    from logger import setup_logger
    from schemas import CompositionPlan, VoiceScript

logger = setup_logger(__name__)

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "script.md"
_FEW_SHOT_PATH = Path(__file__).parent.parent / "skills" / "few_shot.md"
_TIER_RULES_PATH = Path(__file__).parent.parent / "tier_rules.yaml"


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


def _load_tier_constraints(tier: str) -> str:
    """Format tier rules into a readable string for the prompt."""
    if not _TIER_RULES_PATH.exists():
        return f"Tier: {tier}"

    with open(_TIER_RULES_PATH) as f:
        all_rules = yaml.safe_load(f) or {}

    rules = all_rules.get("tiers", {}).get(tier, {})
    if not rules:
        return f"Tier: {tier}"

    return (
        f"Tier: {tier} ({rules.get('label', '')})\n"
        f"Ages: {rules.get('ages', '')}\n"
        f"Words per sentence: {rules.get('words_per_sentence', '')}\n"
        f"Max sentences per turn: {rules.get('max_sentences', '')}\n"
        f"Hook rule: {rules.get('hook_rule', '')} — {rules.get('hook_description', '')}\n"
        f"Closing: {rules.get('closing_speech', '')} — {rules.get('closing_description', '')}\n"
        f"Tone: {rules.get('tone', '')}\n"
        f"Response style: {rules.get('response_style', '')}\n"
        f"Round count range: {rules.get('pathway_rounds', '')}\n"
        f"Available concepts: {rules.get('available_key_concepts', '')}\n"
        f"Max concept badges: {rules.get('max_concept_badges', '')}\n"
        f"Good hook example: {rules.get('example_good_hook', '')}\n"
        f"Bad hook example: {rules.get('example_bad_hook', '')}"
    )


class ScriptAgent:
    """Generates all voice/text content with branching dialogue paths."""

    def __init__(self) -> None:
        self.skill = _SKILL_PATH.read_text() if _SKILL_PATH.exists() else ""
        self.few_shot = _FEW_SHOT_PATH.read_text() if _FEW_SHOT_PATH.exists() else ""

    async def run(self, plan: CompositionPlan, context: dict, session_id: str = "") -> VoiceScript:
        settings = get_settings()
        start = time.perf_counter()

        # Build system prompt with template injections
        system_prompt = self.skill
        system_prompt = system_prompt.replace("{activity_context}", context.get("activity_context", ""))
        system_prompt = system_prompt.replace("{composition_plan}", plan.model_dump_json(indent=2))
        system_prompt = system_prompt.replace("{tier_constraints}", _load_tier_constraints(context.get("tier", "T0")))
        system_prompt = system_prompt.replace("{few_shot}", self.few_shot)

        user_prompt = (
            f"Generate a complete VoiceScript for a {context.get('activity_type', 'activity')} activity "
            f"about a {context.get('entity', 'object')} at tier {context.get('tier', 'T0')}. "
            f"Follow the composition plan and produce exactly {plan.round_count} rounds."
        )

        try:
            client = _get_client()
            loop = asyncio.get_running_loop()

            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=settings.gemini_model,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=VoiceScript,
                            temperature=0.7,
                            max_output_tokens=settings.script_max_tokens,
                        ),
                    ),
                ),
                timeout=settings.script_timeout_ms / 1000,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            script = VoiceScript.model_validate_json(response.text)
            logger.info(f"Script: {len(script.rounds)} rounds, latency={latency_ms}ms")

            await log_agent_call(session_id, "script", latency_ms, True)
            return script

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Script Agent failed ({latency_ms}ms): {e}")
            await log_agent_call(session_id, "script", latency_ms, False, error_message=str(e))
            raise
