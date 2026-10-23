"""C3 — UI Recommendation System (owner: Shen, IT23368170).

Pipeline: aggregate C1+C2 → quadrant per screen → rule lookup → Pareto + TOPSIS → report.
Everything up to the report is deterministic; Gemini can optionally rephrase the report.

NOTE: baseline implementation so the app runs end-to-end. Replace the internals with the
port of the existing, tested engine but keep the ``recommend()`` signature and the
Recommendation shape, which app/orchestrator.py and app/main.py rely on.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from components.recommendation.aggregate import aggregate
from components.recommendation.pareto import pareto_front
from components.recommendation.quadrant import THRESHOLD, URGENCY, classify
from components.recommendation.report import ReportPhrasingError, build_report, polish_with_gemini
from components.recommendation.rule_engine import Rule, load_rules, match
from components.recommendation.topsis import topsis
from shared.contracts import ComponentOutput

# MCDM criteria for each fix candidate, in matrix column order.
CRITERIA = ("severity", "impact", "urgency", "effort")
WEIGHTS = np.array([0.3, 0.3, 0.2, 0.2])
BENEFIT = np.array([True, True, True, False])  # effort is a cost criterion
SEVERITY_SCORE = {"high": 3.0, "medium": 2.0, "low": 1.0}


@dataclass
class ScreenSummary:
    screen_id: str
    name: str
    complexity: float
    cognitive_load: float
    quadrant: str


@dataclass
class RankedFix:
    rank: int
    screen_id: str
    screen_name: str
    quadrant: str
    factor: str
    title: str
    fix: str
    severity: str
    node_ids: list[str]
    sources: list[str]
    guideline: str
    score: float               # TOPSIS closeness, 0–1 (higher = do first)
    pareto_optimal: bool


@dataclass
class Recommendation:
    file_key: str
    screens: list[ScreenSummary]
    fixes: list[RankedFix]
    unmatched_factors: list[str]
    report_md: str
    warnings: list[str] = field(default_factory=list)


def recommend(
    c1: ComponentOutput,
    c2: ComponentOutput,
    *,
    design_name: str | None = None,
    screen_names: dict[str, str] | None = None,
    rules: dict[str, Rule] | None = None,
    threshold: float = THRESHOLD,
    use_llm: bool = False,
) -> Recommendation:
    if c1.file_key != c2.file_key:
        raise ValueError(f"C1 and C2 analysed different files: {c1.file_key} vs {c2.file_key}")
    rules = load_rules() if rules is None else rules
    names = screen_names or {}

    metrics = aggregate(c1, c2)
    quadrants = {m.screen_id: classify(m.complexity, m.cognitive_load, threshold) for m in metrics}
    candidates, unmatched = match(metrics, quadrants, rules)

    matrix = np.array(
        [
            [
                SEVERITY_SCORE[c.violation.severity],
                c.rule.impact,
                URGENCY[c.quadrant],
                c.rule.effort,
            ]
            for c in candidates
        ],
        dtype=float,
    ).reshape(len(candidates), len(CRITERIA))
    scores = np.round(topsis(matrix, WEIGHTS, BENEFIT), 4)
    front = pareto_front(matrix, BENEFIT)

    order = sorted(
        range(len(candidates)),
        key=lambda i: (-scores[i], candidates[i].screen_id, candidates[i].rule.factor),
    )
    fixes = []
    for rank, i in enumerate(order, start=1):
        c = candidates[i]
        fixes.append(
            RankedFix(
                rank=rank,
                screen_id=c.screen_id,
                screen_name=names.get(c.screen_id, c.screen_id),
                quadrant=c.quadrant.value,
                factor=c.rule.factor,
                title=c.rule.title,
                fix=c.rule.fix,
                severity=c.violation.severity,
                node_ids=c.violation.node_ids,
                sources=c.violation.sources,
                guideline=c.rule.guideline,
                score=float(scores[i]),
                pareto_optimal=bool(front[i]),
            )
        )

    screens = [
        ScreenSummary(
            screen_id=m.screen_id,
            name=names.get(m.screen_id, m.screen_id),
            complexity=m.complexity,
            cognitive_load=m.cognitive_load,
            quadrant=quadrants[m.screen_id].value,
        )
        for m in metrics
    ]

    warnings = []
    if unmatched:
        warnings.append(
            "No rule for factor(s) " + ", ".join(unmatched) + " — check the factor vocabulary "
            "in components/recommendation/rules.json."
        )
    report = build_report(design_name or c1.file_key, screens, fixes, unmatched)
    if use_llm:
        try:
            report = polish_with_gemini(report)
        except ReportPhrasingError as exc:
            warnings.append(str(exc))

    return Recommendation(c1.file_key, screens, fixes, unmatched, report, warnings)
