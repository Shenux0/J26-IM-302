"""C2 — Cognitive Load Estimation (owner: De Alwis, IT23307544).

Contract: ``estimate(design) -> ComponentOutput``
  - one ScreenAnalysis per screen in ``design.screens``
  - ``score`` is 0–100, higher = more cognitive load (C3 treats >= 60 as high)
  - every Violation.factor must be a key in components/recommendation/rules.json
  - node_ids must come from ``design.nodes``
"""
from __future__ import annotations

from shared.contracts import ComponentOutput, Design, ScreenAnalysis


def estimate(design: Design) -> ComponentOutput:
    # PLACEHOLDER so the pipeline runs end-to-end: score = 4 points per text layer, capped at 100.
    # Replace with the real cognitive load model.
    screens = []
    for screen in design.screens:
        text_layers = sum(1 for node in design.screen_nodes(screen.id) if node.type == "TEXT")
        screens.append(ScreenAnalysis(screen_id=screen.id, score=min(100.0, 4.0 * text_layers)))
    return ComponentOutput(file_key=design.file_key, screens=screens)
