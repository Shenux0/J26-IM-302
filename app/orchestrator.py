"""Run the full pipeline: ingest → C1 → C2 → C3."""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

from components.recommendation import Recommendation, recommend
from shared.contracts import ComponentOutput, Design, ScreenAnalysis
from shared.ingest import ingest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


@dataclass
class PipelineResult:
    design: Design | None          # None when running on sample fixtures
    complexity: ComponentOutput    # C1
    cognitive_load: ComponentOutput  # C2
    recommendation: Recommendation   # C3
    missing: list[str] = field(default_factory=list)  # components not added to the project yet


def run(file_key: str, *, use_cache: bool = False, use_llm: bool = False) -> PipelineResult:
    design = ingest(file_key, use_cache=use_cache)
    analyze = _optional_component("components.complexity", "analyze")
    estimate = _optional_component("components.cognitive_load", "estimate")
    missing = [name for name, fn in (("C1", analyze), ("C2", estimate)) if fn is None]

    c1 = analyze(design) if analyze else _empty_output(design)
    c2 = estimate(design) if estimate else _empty_output(design)
    rec = recommend(
        c1,
        c2,
        design_name=design.name,
        screen_names={s.id: s.name for s in design.screens},
        use_llm=use_llm,
    )
    return PipelineResult(design, c1, c2, rec, missing)


def run_sample(*, use_llm: bool = False) -> PipelineResult:
    """Run C3 on the C1/C2 fixtures in tests/fixtures — no Figma token needed."""
    c1 = _load_output(FIXTURES_DIR / "c1_complexity.json")
    c2 = _load_output(FIXTURES_DIR / "c2_cognitive_load.json")
    rec = recommend(c1, c2, design_name="Sample data", use_llm=use_llm)
    return PipelineResult(None, c1, c2, rec)


def _optional_component(module: str, func: str) -> Callable[[Design], ComponentOutput] | None:
    """Return ``module.func``, or None while the component's folder doesn't exist yet."""
    try:
        return getattr(import_module(module), func)
    except ModuleNotFoundError as exc:
        if exc.name != module:
            raise  # the component exists but one of its own imports is broken
        return None


def _empty_output(design: Design) -> ComponentOutput:
    """Stand-in for a missing component: score 0 and no violations on every screen."""
    return ComponentOutput(design.file_key, [ScreenAnalysis(s.id, 0.0) for s in design.screens])


def _load_output(path: Path) -> ComponentOutput:
    return ComponentOutput.from_dict(json.loads(path.read_text(encoding="utf-8")))
