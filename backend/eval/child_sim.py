"""Child simulator — generates realistic child inputs using an LLM."""

import json
import logging
import random

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

from eval.rubrics import PERSONAS, ChildSimResponse, Persona

logger = logging.getLogger("wonderlens")


class ChildSimContext(BaseModel):
    """Context passed to the child simulator for each turn."""

    persona: str
    tier: str
    activity_name: str
    collection_criterion: str
    current_step: str
    collection_phase: str | None = None
    round_items: list[dict] | None = None
    last_ai_dialogue: str = ""
    collected_names: list[str] = []
    turn_number: int = 0


def _persona_by_name(name: str) -> Persona:
    for p in PERSONAS:
        if p.name == name:
            return p
    return PERSONAS[0]


def pick_persona(tier: str) -> Persona:
    """Randomly select a persona for the given tier."""
    candidates = [p for p in PERSONAS if p.tier == tier]
    return random.choice(candidates)


def _should_pick_photo(ctx: ChildSimContext) -> bool:
    """Check if this turn is a photo selection turn (Phase A)."""
    return (
        ctx.current_step.startswith("STEP_3_COLLECT_")
        and ctx.collection_phase == "photo"
        and ctx.round_items is not None
    )


def _pick_photo(ctx: ChildSimContext, persona: Persona) -> ChildSimResponse:
    """Use persona probability table to pick correct, wrong, or silence."""
    roll = random.randint(1, 100)
    items = ctx.round_items or []
    correct = [i for i in items if i.get("correct")]
    wrong = [i for i in items if not i.get("correct")]

    if roll <= persona.correct_pct and correct:
        return ChildSimResponse(photo_id=correct[0]["id"])
    if roll <= persona.correct_pct + persona.wrong_pct and wrong:
        return ChildSimResponse(photo_id=random.choice(wrong)["id"])
    return ChildSimResponse(is_silent=True)


class ChildSimulator:
    """Generates child responses via LLM with persona-based photo selection."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=1,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )

    def parse_response(self, raw: str) -> ChildSimResponse:
        """Parse LLM output into ChildSimResponse."""
        try:
            data = json.loads(raw)
            return ChildSimResponse(**data)
        except (json.JSONDecodeError, TypeError):
            return ChildSimResponse(text=raw.strip())

    async def generate(self, ctx: ChildSimContext) -> ChildSimResponse:
        """Generate a child response for the given context."""
        persona = _persona_by_name(ctx.persona)

        if _should_pick_photo(ctx):
            return _pick_photo(ctx, persona)

        if random.randint(1, 100) <= persona.silence_pct:
            return ChildSimResponse(is_silent=True)

        prompt = self._build_prompt(ctx, persona)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt(persona)},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=60,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or '{"text": ""}'
            return self.parse_response(raw)
        except Exception:
            logger.warning("Child sim LLM failed, returning silence")
            return ChildSimResponse(is_silent=True)

    def _system_prompt(self, persona: Persona) -> str:
        age_map = {"T0": "2-4", "T1": "4-6", "T2": "6-8"}
        age = age_map.get(persona.tier, "2-4")
        return (
            f"You are role-playing as a {age}-year-old child. "
            f"Personality: {persona.description}. "
            f"Respond with SHORT, realistic child speech. "
            f'Output JSON: {{"text": "your response"}}'
        )

    def _build_prompt(self, ctx: ChildSimContext, persona: Persona) -> str:
        parts = [
            f"Activity: {ctx.activity_name} ({ctx.collection_criterion})",
            f"Step: {ctx.current_step}",
            f'The AI just said: "{ctx.last_ai_dialogue}"',
        ]
        if ctx.collected_names:
            parts.append(f"Items collected so far: {', '.join(ctx.collected_names)}")
        parts.append(f"Turn number: {ctx.turn_number}")
        return "\n".join(parts)
