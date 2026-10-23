"""Fetch the Figma file ONCE and build the shared ``Design`` (screens + flat node list).

C1 and C2 both analyse the Design returned here, so their scores and node IDs line up.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.contracts import Design, Node, Screen
from shared.figma_client import get_file

CACHE_DIR = Path(__file__).resolve().parents[1] / "output" / "cache"

# A top-level frame is treated as a mobile screen when it is portrait and its width
# falls in this range (covers 320pt iPhone SE up to large Android phones).
MOBILE_MIN_WIDTH = 320
MOBILE_MAX_WIDTH = 480


def ingest(file_key: str, use_cache: bool = False) -> Design:
    """Fetch ``file_key`` from Figma (or the local cache) and build the Design.

    Every fetch is written to ``output/cache/<file_key>.json``; ``use_cache=True`` reads
    that file instead of calling the API, which avoids Figma rate limits while developing.
    """
    cache_file = CACHE_DIR / f"{file_key}.json"
    if use_cache and cache_file.exists():
        figma_file = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        figma_file = get_file(file_key)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(figma_file), encoding="utf-8")
    return build_design(file_key, figma_file)


def build_design(file_key: str, figma_file: dict[str, Any]) -> Design:
    """Build a Design from raw ``GET /v1/files/:key`` JSON. Hidden layers are skipped."""
    design = Design(file_key=file_key, name=figma_file.get("name", file_key))
    for page in figma_file.get("document", {}).get("children", []):
        for frame in _top_level_frames(page):
            if not _is_visible(frame) or not _is_mobile_screen(frame):
                continue
            x, y, w, h = _bbox(frame) or (0.0, 0.0, 0.0, 0.0)
            screen = Screen(id=frame["id"], name=frame.get("name", ""), page=page.get("name", ""),
                            width=w, height=h)
            _walk(frame, screen, parent_id=None, depth=0, design=design)
            design.screens.append(screen)
    return design


def _top_level_frames(container: dict[str, Any]):
    """Frames placed directly on a page, including frames grouped inside sections."""
    for child in container.get("children", []):
        if child.get("type") == "SECTION" and _is_visible(child):
            yield from _top_level_frames(child)
        elif child.get("type") == "FRAME":
            yield child


def _is_mobile_screen(frame: dict[str, Any]) -> bool:
    box = _bbox(frame)
    if box is None:
        return False
    _, _, w, h = box
    return MOBILE_MIN_WIDTH <= w <= MOBILE_MAX_WIDTH and h >= w


def _is_visible(node: dict[str, Any]) -> bool:
    return node.get("visible", True)


def _bbox(node: dict[str, Any]) -> tuple[float, float, float, float] | None:
    box = node.get("absoluteBoundingBox")
    if not box:
        return None
    return (float(box["x"]), float(box["y"]), float(box["width"]), float(box["height"]))


def _walk(node: dict[str, Any], screen: Screen, parent_id: str | None, depth: int,
          design: Design) -> None:
    design.nodes[node["id"]] = Node(
        id=node["id"],
        name=node.get("name", ""),
        type=node.get("type", ""),
        screen_id=screen.id,
        parent_id=parent_id,
        depth=depth,
        bbox=_bbox(node),
        raw={k: v for k, v in node.items() if k != "children"},
    )
    screen.node_ids.append(node["id"])
    for child in node.get("children", []):
        if _is_visible(child):
            _walk(child, screen, parent_id=node["id"], depth=depth + 1, design=design)
