"""LLM judge — scores session transcripts against per-step rubrics."""

import json
import logging

import httpx
from openai import AsyncOpenAI

from eval.rubrics import (
    STEP_RUBRICS,
    SessionJudgement,
    SessionTranscript,
    StepScore,
    step_to_rubric_label,
)

logger = logging.getLogger("wonderlens")


def _build_judge_prompt(transcript: SessionTranscript) -> str:
    """Build the judge prompt from a session transcript."""
    age_map = {"T0": "2-4", "T1": "4-6", "T2": "6-8"}
    age = age_map.get(transcript.tier, "2-4")

    steps: dict[str, list[str]] = {}
    for turn in transcript.turns:
        label = step_to_rubric_label(turn.step)
        steps.setdefault(label, []).append(turn.ai_dialogue)

    transcript_lines: list[str] = []
    for turn in transcript.turns:
        transcript_lines.append(f"[{turn.step}] AI: {turn.ai_dialogue}")
        if turn.child_input.text:
            transcript_lines.append(f"[{turn.step}] Child: {turn.child_input.text}")
        elif turn.child_input.photo_id:
            transcript_lines.append(f"[{turn.step}] Child: [selected photo: {turn.child_input.photo_id}]")
        elif turn.child_input.is_silent:
            transcript_lines.append(f"[{turn.step}] Child: [silence]")

    rubric_lines: list[str] = []
    for label, rubric in STEP_RUBRICS.items():
        if label in steps:
            rubric_lines.append(f"- {label}: Score these dimensions 1-5: {', '.join(rubric.dimensions)}")

    return (
        f"You are an expert early childhood education evaluator.\n\n"
        f"Evaluate this Cat5 collection game transcript for a {transcript.tier} child (ages {age}).\n\n"
        f"Transcript:\n" + "\n".join(transcript_lines) + "\n\n"
        "For each step present in the transcript, rate the dimensions 1-5:\n" + "\n".join(rubric_lines) + "\n\n"
        "Also flag critical failures:\n"
        "- AI suggested specific real-world items to find\n"
        "- AI used directive language ('Go find!', 'Look for!')\n"
        "- AI asked knowledge-test questions in the hook\n"
        "- AI used premature completion language\n"
        "- AI didn't celebrate correct photo selections\n\n"
        "Output JSON with this structure:\n"
        '{"step_scores": [{"step": "HOOK", "scores": {"dim": 4}, '
        '"justifications": {"dim": "reason"}, "critical_failures": []}], '
        '"critical_failures": [], "summary": "2-3 sentence assessment"}'
    )


def _compute_weighted_score(step_scores: list[StepScore]) -> float:
    """Compute weighted average 1-5 from step scores."""
    total_weight = 0
    weighted_sum = 0.0
    for ss in step_scores:
        rubric = STEP_RUBRICS.get(ss.step)
        if not rubric or not ss.scores:
            continue
        avg = sum(ss.scores.values()) / len(ss.scores)
        weighted_sum += avg * rubric.weight
        total_weight += rubric.weight
    return weighted_sum / total_weight if total_weight > 0 else 1.0


class EvalJudge:
    """Scores session transcripts via LLM against rubrics."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=1,
            timeout=httpx.Timeout(30.0, connect=5.0),
        )

    def parse_judgement(self, raw: str) -> SessionJudgement:
        """Parse LLM judge output into SessionJudgement."""
        try:
            data = json.loads(raw)
            step_scores = [StepScore(**ss) for ss in data.get("step_scores", [])]
            overall = _compute_weighted_score(step_scores)
            return SessionJudgement(
                step_scores=step_scores,
                overall_score=overall,
                critical_failures=data.get("critical_failures", []),
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Judge output parse failed: %s", exc)
            return SessionJudgement(
                step_scores=[],
                overall_score=1.0,
                critical_failures=[f"Judge parse failed: {exc}"],
                summary="Judge output failed to parse.",
            )

    async def judge_session(self, transcript: SessionTranscript) -> SessionJudgement:
        """Score a full session transcript."""
        prompt = _build_judge_prompt(transcript)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert early childhood education evaluator. Output valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return self.parse_judgement(raw)
        except Exception as exc:
            logger.warning("Judge LLM call failed: %s", exc)
            return SessionJudgement(
                step_scores=[],
                overall_score=1.0,
                critical_failures=[f"Judge LLM failed: {exc}"],
                summary="Judge LLM call failed.",
            )
