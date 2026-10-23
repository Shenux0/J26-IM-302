import json
from pathlib import Path

import numpy as np
import pytest

from components.recommendation import recommend
from components.recommendation.aggregate import aggregate
from components.recommendation.pareto import pareto_front
from components.recommendation.quadrant import Quadrant, classify
from components.recommendation.rule_engine import load_rules
from components.recommendation.topsis import topsis
from shared.contracts import ComponentOutput, ScreenAnalysis, Violation

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> ComponentOutput:
    return ComponentOutput.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


@pytest.fixture
def c1() -> ComponentOutput:
    return _load("c1_complexity.json")


@pytest.fixture
def c2() -> ComponentOutput:
    return _load("c2_cognitive_load.json")


def test_fixture_factors_exist_in_rules(c1, c2):
    rules = load_rules()
    for output in (c1, c2):
        for screen in output.screens:
            for violation in screen.violations:
                assert violation.factor in rules, violation.factor


@pytest.mark.parametrize(
    ("complexity", "load", "expected"),
    [
        (60, 60, Quadrant.CRITICAL),
        (60, 59.9, Quadrant.HIGH_COMPLEXITY),
        (59.9, 60, Quadrant.HIGH_LOAD),
        (10, 10, Quadrant.HEALTHY),
    ],
)
def test_quadrant_threshold_is_60(complexity, load, expected):
    assert classify(complexity, load) == expected


def test_aggregate_merges_same_factor_from_both_components(c1, c2):
    home = next(s for s in aggregate(c1, c2) if s.screen_id == "1:2")
    assert (home.complexity, home.cognitive_load) == (78.0, 71.0)
    merged = [v for v in home.violations if v.factor == "weak_visual_hierarchy"]
    assert len(merged) == 1
    assert merged[0].severity == "high"
    assert merged[0].sources == ["C1", "C2"]
    assert merged[0].node_ids == ["1:14", "1:17"]


def test_pareto_front_drops_dominated_rows():
    matrix = np.array([[3, 1], [2, 2], [1, 1], [3, 1]])
    assert pareto_front(matrix, np.array([True, True])).tolist() == [True, True, False, True]
    # [1, 1] is dominated when both columns are benefits, but not once column 2 is a cost.
    tradeoff = np.array([[3, 3], [1, 1]])
    assert pareto_front(tradeoff, np.array([True, True])).tolist() == [True, False]
    assert pareto_front(tradeoff, np.array([True, False])).tolist() == [True, True]


def test_topsis_scores_ideal_and_anti_ideal():
    matrix = np.array([[5, 1], [3, 3], [1, 5]])  # benefit, cost
    scores = topsis(matrix, np.array([0.5, 0.5]), np.array([True, False]))
    assert scores[0] == pytest.approx(1.0)
    assert scores[2] == pytest.approx(0.0)
    assert scores[0] > scores[1] > scores[2]


def test_topsis_single_candidate_scores_one():
    assert topsis(np.array([[2, 3]]), np.array([1, 1]), np.array([True, False])).tolist() == [1.0]


def test_recommend_is_ranked_and_deterministic(c1, c2):
    first, second = recommend(c1, c2), recommend(c1, c2)
    assert first == second
    assert [f.rank for f in first.fixes] == list(range(1, len(first.fixes) + 1))
    assert [f.score for f in first.fixes] == sorted((f.score for f in first.fixes), reverse=True)
    assert {s.screen_id: s.quadrant for s in first.screens} == {
        "1:2": "critical",
        "1:3": "high_cognitive_load",
        "1:4": "high_complexity",
        "1:5": "healthy",
    }
    assert first.unmatched_factors == []
    assert first.fixes[0].screen_id == "1:2"  # high-severity fix on the critical screen


def test_unknown_factor_is_reported_not_silently_dropped():
    c1 = ComponentOutput("K", [ScreenAnalysis("s", 80, [Violation("not_a_factor", "high", ["n"])])])
    c2 = ComponentOutput("K", [ScreenAnalysis("s", 80)])
    result = recommend(c1, c2)
    assert result.fixes == []
    assert result.unmatched_factors == ["not_a_factor"]
    assert result.warnings
    assert "not_a_factor" in result.report_md


def test_recommend_rejects_outputs_for_different_files():
    with pytest.raises(ValueError):
        recommend(ComponentOutput("A"), ComponentOutput("B"))
