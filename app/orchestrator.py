"""Run the full pipeline: ingest → C1 → C2 → C3."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from components.cognitive_load import estimate
from components.complexity import analyze
from components.recommendation import Recommendation, recommend
from shared.contracts import ComponentOutput, Design
from shared.ingest import ingest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


@dataclass
class PipelineResult:
    design: Design | None          # None when running on sample fixtures
    complexity: ComponentOutput    # C1
    cognitive_load: ComponentOutput  # C2
    recommendation: Recommendation   # C3


def run(file_key: str, *, use_cache: bool = False, use_llm: bool = False) -> PipelineResult:
    design = ingest(file_key, use_cache=use_cache)
    c1 = analyze(design)
    c2 = estimate(design)
    rec = recommend(
        c1,
        c2,
        design_name=design.name,
        screen_names={s.id: s.name for s in design.screens},
        use_llm=use_llm,
    )
    return PipelineResult(design, c1, c2, rec)


def run_sample(*, use_llm: bool = False) -> PipelineResult:
    """Run C3 on the C1/C2 fixtures in tests/fixtures — no Figma token needed."""
    c1 = _load_output(FIXTURES_DIR / "c1_complexity.json")
    c2 = _load_output(FIXTURES_DIR / "c2_cognitive_load.json")
    rec = recommend(c1, c2, design_name="Sample data", use_llm=use_llm)
    return PipelineResult(None, c1, c2, rec)


def _load_output(path: Path) -> ComponentOutput:
    return ComponentOutput.from_dict(json.loads(path.read_text(encoding="utf-8")))
