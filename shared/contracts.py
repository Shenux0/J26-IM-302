"""Shared data contract for all UXDAS components.

Input side:  ``shared.ingest`` builds ONE ``Design`` per Figma file; C1 and C2 both analyse it.
Output side: C1 and C2 each return a ``ComponentOutput``; C3 consumes both.

Change this file only with agreement from all three members — everyone imports it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SEVERITIES = ("high", "medium", "low")
SCORE_MIN, SCORE_MAX = 0.0, 100.0


# --- Input: the ingested design (shared.ingest -> C1, C2) --------------------


@dataclass
class Node:
    id: str                    # Figma node ID, e.g. "12:345"
    name: str
    type: str                  # Figma node type: FRAME, TEXT, RECTANGLE, INSTANCE, ...
    screen_id: str             # the screen (top-level frame) this node belongs to
    parent_id: str | None      # None for the screen frame itself
    depth: int                 # 0 = the screen frame, 1 = its direct children, ...
    bbox: tuple[float, float, float, float] | None  # (x, y, width, height), absolute
    raw: dict[str, Any] = field(default_factory=dict, repr=False)  # Figma JSON minus children


@dataclass
class Screen:
    id: str                    # node ID of the top-level frame
    name: str
    page: str                  # Figma page the frame lives on
    width: float
    height: float
    node_ids: list[str] = field(default_factory=list)  # depth-first, frame first


@dataclass
class Design:
    file_key: str
    name: str
    screens: list[Screen] = field(default_factory=list)
    nodes: dict[str, Node] = field(default_factory=dict)  # every node of every screen

    def screen_nodes(self, screen_id: str) -> list[Node]:
        """All nodes of one screen, depth-first, starting with the frame itself."""
        screen = next(s for s in self.screens if s.id == screen_id)
        return [self.nodes[i] for i in screen.node_ids]


# --- Output: component results (C1, C2 -> C3) --------------------------------


@dataclass
class Violation:
    factor: str            # key looked up in C3's rules.json (shared vocabulary!)
    severity: str          # "high" | "medium" | "low"
    node_ids: list[str]    # Figma node IDs where the issue occurs

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")


@dataclass
class ScreenAnalysis:
    screen_id: str
    score: float           # 0–100. complexity for C1, cognitive load for C2
    violations: list[Violation] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not SCORE_MIN <= self.score <= SCORE_MAX:
            raise ValueError(f"score must be in [0, 100], got {self.score} ({self.screen_id})")


@dataclass
class ComponentOutput:
    file_key: str
    screens: list[ScreenAnalysis] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComponentOutput:
        return cls(
            file_key=data["file_key"],
            screens=[
                ScreenAnalysis(
                    screen_id=s["screen_id"],
                    score=float(s["score"]),
                    violations=[
                        Violation(
                            factor=v["factor"],
                            severity=v["severity"],
                            node_ids=list(v.get("node_ids", [])),
                        )
                        for v in s.get("violations", [])
                    ],
                )
                for s in data.get("screens", [])
            ],
        )
