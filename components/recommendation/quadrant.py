"""Place each screen in a complexity × cognitive-load quadrant."""
from __future__ import annotations

from enum import StrEnum

THRESHOLD = 60.0  # scores >= THRESHOLD count as "high"


class Quadrant(StrEnum):
    CRITICAL = "critical"                   # high complexity, high cognitive load
    HIGH_COMPLEXITY = "high_complexity"     # high complexity, low cognitive load
    HIGH_LOAD = "high_cognitive_load"       # low complexity, high cognitive load
    HEALTHY = "healthy"                     # low complexity, low cognitive load


# How urgently a screen's fixes matter; used as a TOPSIS benefit criterion.
URGENCY = {
    Quadrant.CRITICAL: 1.0,
    Quadrant.HIGH_COMPLEXITY: 0.7,
    Quadrant.HIGH_LOAD: 0.7,
    Quadrant.HEALTHY: 0.3,
}


def classify(complexity: float, cognitive_load: float, threshold: float = THRESHOLD) -> Quadrant:
    high_complexity = complexity >= threshold
    high_load = cognitive_load >= threshold
    if high_complexity and high_load:
        return Quadrant.CRITICAL
    if high_complexity:
        return Quadrant.HIGH_COMPLEXITY
    if high_load:
        return Quadrant.HIGH_LOAD
    return Quadrant.HEALTHY
