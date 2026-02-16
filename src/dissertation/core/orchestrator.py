from __future__ import annotations

import os
import traceback
import uuid

from dissertation.agents.baseline_generator import generate_baseline
from dissertation.core.semantic_cache import generate_bundle_cached
from dissertation.models.schemas import Epic, QualityReport, RequirementSet, RunMetadata
from dissertation.tools.ambiguity_detector import detect_ambiguities
from dissertation.tools.gherkin_validator import validate_all
from dissertation.tools.invest_scorer import score_story_invest
from dissertation.tools.trace_checker import check_trace

# OpenAI agents (optional imports)
try:
    from dissertation.agents.generator_agent import generate_with_openai
except Exception:
    generate_with_openai = None  # type: ignore

try:
    from dissertation.agents.critic_agent import critique as critic_fn
    from dissertation.agents.refiner_agent import refine as refiner_fn
except Exception:
    critic_fn = None  # type: ignore
    refiner_fn = None  # type: ignore


def build_quality_reports(
    epic: Epic, req: RequirementSet
) -> tuple[list[QualityReport], bool, list[str], float]:
    g_ok, g_violations = validate_all(req.scenarios)
    t_ok, t_violations = check_trace(req)
    hard_ok = g_ok and t_ok
    hard_violations = g_violations + t_violations

    ambiguities = detect_ambiguities(epic, req.stories, req.scenarios)

    reports: list[QualityReport] = []
    overall_scores: list[float] = []

    for story in req.stories:
        scores, invest_issues = score_story_invest(story, req.scenarios)

        invest_avg = (scores.I + scores.N + scores.V + scores.E + scores.S + scores.T) / 6.0
        penalty = 0.0
        penalty += 0.2 * len(invest_issues)
        penalty += 0.3 * len([v for v in hard_violations if story.story_id in v])
        penalty += 0.05 * len([a for a in ambiguities if story.story_id in a])
        overall = max(1.0, min(5.0, invest_avg - penalty))

        violations = []
        violations.extend(invest_issues)
        violations.extend(hard_violations)

        qr = QualityReport(
            story_id=story.story_id,
            invest=scores,
            gherkin_valid=g_ok,
            ambiguities=ambiguities,
            violations=violations,
            overall_score=overall,
        )
        reports.append(qr)
        overall_scores.append(overall)

    req_avg = sum(overall_scores) / max(1, len(overall_scores))
    return reports, hard_ok, hard_violations, req_avg


def _make_req(
    epic: Epic,
    run_id: str,
    mode: str,
    iteration: int,
    model_used: str,
    stories,
    scenarios,
    trace_map,
    temperature: float,
) -> RequirementSet:
    meta = RunMetadata(
        run_id=run_id,
        epic_id=epic.epic_id,
        mode=mode,  # type: ignore
        iteration=iteration,
        model_name=model_used,
        temperature=temperature,
    )
    req = RequirementSet(
        epic_id=epic.epic_id,
        mode=mode,  # type: ignore
        stories=stories,
        scenarios=scenarios,
        quality_reports=[],
        trace_map=trace_map,
        run_metadata=meta,
    )
    reports, _, _, _ = build_quality_reports(epic, req)
    req.quality_reports = reports
    return req


def run_llm_baseline(
    epic: Epic, *, force_openai: bool, model_name: str | None = None, temperature: float = 0.2
) -> tuple[RequirementSet, dict]:

    run_id = str(uuid.uuid4())
    used = "stub"

    if force_openai:
        if not os.getenv("OPENAI_API_KEY") or generate_with_openai is None:
            raise RuntimeError(
                "OpenAI forced, but OPENAI_API_KEY missing or generator_agent not available."
            )
        bundle, cache_meta = generate_bundle_cached(epic)
        print(f"[cache] {cache_meta}")

        used = model_name or os.getenv("OPENAI_MODEL") or "openai"
        req = _make_req(
            epic,
            run_id,
            "llm_baseline",
            0,
            used,
            bundle.stories,
            bundle.scenarios,
            bundle.trace_map,
            temperature,
        )
        return req, cache_meta

    # stub baseline
    stories, scenarios, trace_map = generate_baseline(epic)
    req = _make_req(
        epic, run_id, "llm_baseline", 0, used, stories, scenarios, trace_map, temperature
    )
    return req, {"cache_hit": "disabled", "reason": "stub_baseline"}


def run_agentic(
    epic: Epic,
    *,
    model_name: str | None = None,
    temperature: float = 0.2,
    max_iters: int = 3,
    target_score: float = 4.2,
    out_dir: str = "outputs",
    force_min_iters: int = 1,
) -> tuple[RequirementSet, dict]:
    """
    Agentic loop: generate -> validate/score -> (critique -> refine -> validate/score)*.
    Writes audit_log.jsonl + iteration_scores.csv for dissertation evidence.
    """
    if (
        not os.getenv("OPENAI_API_KEY")
        or generate_with_openai is None
        or critic_fn is None
        or refiner_fn is None
    ):
        raise RuntimeError(
            "Agentic mode requires OpenAI + generator/critic/refiner agents available."
        )

    from dissertation.core.exporter import get_run_folder
    from dissertation.utils.audit import AuditLogger
    from dissertation.utils.iteration_scores import write_iteration_scores

    run_id = str(uuid.uuid4())
    used = model_name or os.getenv("OPENAI_MODEL") or "openai"

    run_folder = get_run_folder(epic.epic_id, "agentic", run_id, out_dir)
    audit = AuditLogger.create(run_folder)

    iteration_rows = []

    # Iteration 0: generate
    bundle, cache_meta = generate_bundle_cached(epic)
    print(f"[cache] {cache_meta}")

    req = _make_req(
        epic,
        run_id,
        "agentic",
        0,
        used,
        bundle.stories,
        bundle.scenarios,
        bundle.trace_map,
        temperature,
    )

    reports, hard_ok, hard_violations, avg_score = build_quality_reports(epic, req)
    g_ok = all(r.gherkin_valid for r in reports)
    t_ok, _ = check_trace(req)

    audit.log(
        "iteration_result",
        {
            "iteration": 0,
            "avg_score": round(avg_score, 3),
            "hard_ok": hard_ok,
            "gherkin_ok": g_ok,
            "trace_ok": t_ok,
            "hard_violations": hard_violations[:20],
            "stories": len(req.stories),
            "scenarios": len(req.scenarios),
            "edits_count": 0,
            "critic_summary": None,
        },
    )

    iteration_rows.append(
        {
            "iteration": 0,
            "avg_score": round(avg_score, 3),
            "hard_ok": hard_ok,
            "gherkin_ok": g_ok,
            "trace_ok": t_ok,
            "edits_count": 0,
        }
    )

    best_req = req
    best_score = avg_score

    # Only stop early if we've satisfied the "minimum iterations" requirement.
    if hard_ok and avg_score >= target_score and force_min_iters <= 0:
        write_iteration_scores(run_folder, iteration_rows)
        return best_req, cache_meta

    for it in range(1, max_iters + 1):
        try:
            crit = critic_fn(epic, req)
            audit.log(
                "critique",
                {
                    "iteration": it,
                    "should_iterate": crit.should_iterate,
                    "summary": crit.summary,
                    "edits_count": len(crit.edits),
                },
            )

            if not crit.should_iterate:
                write_iteration_scores(run_folder, iteration_rows)
                return req, cache_meta

            refined = refiner_fn(epic, req, crit)
            req = _make_req(
                epic,
                run_id,
                "agentic",
                it,
                used,
                refined.stories,
                refined.scenarios,
                refined.trace_map,
                temperature,
            )

            reports, hard_ok, hard_violations, avg_score = build_quality_reports(epic, req)
            g_ok = all(r.gherkin_valid for r in reports)
            t_ok, _ = check_trace(req)

            audit.log(
                "iteration_result",
                {
                    "iteration": it,
                    "avg_score": round(avg_score, 3),
                    "hard_ok": hard_ok,
                    "gherkin_ok": g_ok,
                    "trace_ok": t_ok,
                    "hard_violations": hard_violations[:20],
                    "stories": len(req.stories),
                    "scenarios": len(req.scenarios),
                    "edits_count": len(crit.edits),
                    "critic_summary": crit.summary,
                },
            )

            iteration_rows.append(
                {
                    "iteration": it,
                    "avg_score": round(avg_score, 3),
                    "hard_ok": hard_ok,
                    "gherkin_ok": g_ok,
                    "trace_ok": t_ok,
                    "edits_count": len(crit.edits),
                }
            )

            if hard_ok and avg_score >= best_score:
                best_req, best_score = req, avg_score

            if hard_ok and avg_score >= target_score:
                write_iteration_scores(run_folder, iteration_rows)
                return req, cache_meta

        except Exception as e:
            audit.log(
                "error",
                {
                    "iteration": it,
                    "error": repr(e),
                    "traceback": traceback.format_exc(),
                },
            )
            write_iteration_scores(run_folder, iteration_rows)
            return best_req, cache_meta

    write_iteration_scores(run_folder, iteration_rows)
    return best_req, cache_meta
