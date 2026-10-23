"""Map each violation's ``factor`` to a fix from rules.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from components.recommendation.aggregate import MergedViolation, ScreenMetrics
from components.recommendation.quadrant import Quadrant

RULES_PATH = Path(__file__).with_name("rules.json")


@dataclass(frozen=True)
class Rule:
    factor: str
    category: str      # "complexity" | "cognitive_load"
    title: str
    fix: str
    impact: int        # 1–5, how much the fix improves the screen
    effort: int        # 1–5, how costly the fix is to apply
    guideline: str


@dataclass
class Candidate:
    screen_id: str
    quadrant: Quadrant
    violation: MergedViolation
    rule: Rule


def load_rules(path: Path = RULES_PATH) -> dict[str, Rule]:
    factors = json.loads(path.read_text(encoding="utf-8"))["factors"]
    return {key: Rule(factor=key, **spec) for key, spec in factors.items()}


def match(
    screens: list[ScreenMetrics], quadrants: dict[str, Quadrant], rules: dict[str, Rule]
) -> tuple[list[Candidate], list[str]]:
    """Return fix candidates plus the sorted factors that have no rule.

    Unknown factors are returned rather than silently dropped so a vocabulary
    mismatch between components shows up in the UI and the report.
    """
    candidates: list[Candidate] = []
    unmatched: set[str] = set()
    for screen in screens:
        for violation in screen.violations:
            rule = rules.get(violation.factor)
            if rule is None:
                unmatched.add(violation.factor)
                continue
            candidates.append(
                Candidate(screen.screen_id, quadrants[screen.screen_id], violation, rule)
            )
    return candidates, sorted(unmatched)
