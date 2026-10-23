"""Merge C1 and C2 outputs into one record per screen."""
from __future__ import annotations

from dataclasses import dataclass, field

from shared.contracts import SEVERITIES, ComponentOutput

_SEVERITY_RANK = {s: i for i, s in enumerate(reversed(SEVERITIES))}  # low=0, medium=1, high=2


@dataclass
class MergedViolation:
    factor: str
    severity: str
    node_ids: list[str]
    sources: list[str]          # which components reported it: "C1", "C2"


@dataclass
class ScreenMetrics:
    screen_id: str
    complexity: float           # C1 score (0 if C1 did not report this screen)
    cognitive_load: float       # C2 score (0 if C2 did not report this screen)
    violations: list[MergedViolation] = field(default_factory=list)


def aggregate(c1: ComponentOutput, c2: ComponentOutput) -> list[ScreenMetrics]:
    """One ScreenMetrics per screen seen by either component, in first-seen order.

    The same factor reported by both components on one screen becomes a single
    violation with the higher severity and the union of node IDs.
    """
    screens: dict[str, ScreenMetrics] = {}
    for source, output, attr in (("C1", c1, "complexity"), ("C2", c2, "cognitive_load")):
        for analysis in output.screens:
            metrics = screens.setdefault(
                analysis.screen_id, ScreenMetrics(analysis.screen_id, 0.0, 0.0)
            )
            setattr(metrics, attr, analysis.score)
            by_factor = {v.factor: v for v in metrics.violations}
            for v in analysis.violations:
                existing = by_factor.get(v.factor)
                if existing is None:
                    merged = MergedViolation(v.factor, v.severity, list(v.node_ids), [source])
                    metrics.violations.append(merged)
                    by_factor[v.factor] = merged
                    continue
                if _SEVERITY_RANK[v.severity] > _SEVERITY_RANK[existing.severity]:
                    existing.severity = v.severity
                existing.node_ids += [n for n in v.node_ids if n not in existing.node_ids]
                if source not in existing.sources:
                    existing.sources.append(source)
    return list(screens.values())
