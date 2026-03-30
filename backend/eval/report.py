"""Report generator — JSON summary + markdown."""

from eval.rubrics import SessionJudgement, SessionTranscript, Thresholds


def _combined_score(rule: float, judge: float) -> float:
    """Blend rule-based (0-100) and judge (1-5) into 0-100."""
    judge_normalized = (judge - 1) / 4 * 100
    return rule * 0.6 + judge_normalized * 0.4


def generate_summary_json(
    transcripts: list[SessionTranscript],
    judgements: list[SessionJudgement],
    thresholds: Thresholds,
) -> dict:
    """Generate machine-readable summary."""
    combos: dict[str, dict] = {}
    all_pass = True

    for t, j in zip(transcripts, judgements):
        key = f"{t.activity}_{t.tier}"
        if key not in combos:
            combos[key] = {
                "activity": t.activity,
                "tier": t.tier,
                "sessions": 0,
                "rule_scores": [],
                "judge_scores": [],
                "critical_failures": [],
            }
        combos[key]["sessions"] += 1
        combos[key]["rule_scores"].append(t.rule_score)
        combos[key]["judge_scores"].append(j.overall_score)
        combos[key]["critical_failures"].extend(j.critical_failures)

    for combo in combos.values():
        avg_rule = sum(combo["rule_scores"]) / len(combo["rule_scores"]) if combo["rule_scores"] else 0
        avg_judge = sum(combo["judge_scores"]) / len(combo["judge_scores"]) if combo["judge_scores"] else 1
        combo["avg_rule"] = round(avg_rule, 1)
        combo["avg_judge"] = round(avg_judge, 2)
        combo["combined"] = round(_combined_score(avg_rule, avg_judge), 1)
        combo["failure_count"] = len(combo["critical_failures"])

        if combo["combined"] < thresholds.combined_score_min:
            all_pass = False
        if combo["failure_count"] > thresholds.critical_failures_max:
            all_pass = False

    return {"status": "PASS" if all_pass else "FAIL", "combos": combos}


def generate_markdown_report(
    transcripts: list[SessionTranscript],
    judgements: list[SessionJudgement],
    thresholds: Thresholds,
) -> str:
    """Generate human-readable markdown report."""
    summary = generate_summary_json(transcripts, judgements, thresholds)
    lines: list[str] = [
        "# Eval Report",
        f"Status: **{summary['status']}**\n",
        "## Summary",
        "| Activity | Tier | Sessions | Rule | Judge | Combined | Status |",
        "|----------|------|----------|------|-------|----------|--------|",
    ]

    for combo in summary["combos"].values():
        status = (
            "PASS"
            if combo["combined"] >= thresholds.combined_score_min
            and combo["failure_count"] <= thresholds.critical_failures_max
            else "FAIL"
        )
        lines.append(
            f"| {combo['activity']} | {combo['tier']} | {combo['sessions']} | "
            f"{combo['avg_rule']} | {combo['avg_judge']}/5 | {combo['combined']}% | {status} |"
        )

    all_failures = []
    for t, j in zip(transcripts, judgements):
        for f in j.critical_failures:
            all_failures.append(f"- {t.session_id} ({t.activity} {t.tier}): {f}")

    if all_failures:
        lines.extend(["", "## Critical Failures"] + all_failures)
    else:
        lines.extend(["", "## Critical Failures", "None."])

    return "\n".join(lines) + "\n"
