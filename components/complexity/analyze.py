"""C1 — Interface Complexity Analysis (owner: Senara, IT23177178).

Contract: ``analyze(design) -> ComponentOutput``
  - one ScreenAnalysis per screen in ``design.screens``
  - ``score`` is 0–100, higher = more complex (C3 treats >= 60 as high)
  - every Violation.factor must be a key in components/recommendation/rules.json
  - node_ids must come from ``design.nodes``
"""
from __future__ import annotations

from shared.contracts import ComponentOutput, Design, ScreenAnalysis


def analyze(design: Design) -> ComponentOutput:
    # PLACEHOLDER so the pipeline runs end-to-end: score = visible layer count, capped at 100.
    # Replace with the real complexity model.
    screens = [
        ScreenAnalysis(screen_id=screen.id, score=min(100.0, float(len(screen.node_ids))))
        for screen in design.screens
    ]
    return ComponentOutput(file_key=design.file_key, screens=screens)
