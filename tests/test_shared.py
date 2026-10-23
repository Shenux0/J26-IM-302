import pytest

from shared.contracts import ComponentOutput, ScreenAnalysis, Violation
from shared.figma_client import parse_file_key
from shared.ingest import build_design


def _frame(node_id, w, h, children=(), **extra):
    return {
        "id": node_id,
        "name": f"Frame {node_id}",
        "type": "FRAME",
        "absoluteBoundingBox": {"x": 0, "y": 0, "width": w, "height": h},
        "children": list(children),
        **extra,
    }


def _node(node_id, node_type, children=(), **extra):
    return {"id": node_id, "name": node_id, "type": node_type, "children": list(children), **extra}


FIGMA_FILE = {
    "name": "Demo app",
    "document": {
        "children": [
            {
                "id": "0:1",
                "name": "Page 1",
                "type": "CANVAS",
                "children": [
                    _frame("1:1", 375, 812, [
                        _node("1:2", "TEXT"),
                        _node("1:3", "RECTANGLE", visible=False),
                        _node("1:4", "GROUP", [_node("1:5", "TEXT")]),
                    ]),
                    _frame("1:6", 1440, 900),        # desktop: excluded
                    _frame("1:7", 375, 100),         # banner, not portrait: excluded
                    _frame("1:8", 390, 844, visible=False),  # hidden: excluded
                    {
                        "id": "1:9",
                        "type": "SECTION",
                        "children": [_frame("1:10", 390, 844, [_node("1:11", "TEXT")])],
                    },
                ],
            }
        ]
    },
}


def test_build_design_keeps_only_visible_mobile_frames():
    design = build_design("KEY", FIGMA_FILE)
    assert design.name == "Demo app"
    assert [s.id for s in design.screens] == ["1:1", "1:10"]
    assert design.screens[0].page == "Page 1"
    assert (design.screens[1].width, design.screens[1].height) == (390, 844)


def test_build_design_flattens_nodes_and_skips_hidden_layers():
    design = build_design("KEY", FIGMA_FILE)
    assert design.screens[0].node_ids == ["1:1", "1:2", "1:4", "1:5"]
    nested = design.nodes["1:5"]
    assert (nested.screen_id, nested.parent_id, nested.depth) == ("1:1", "1:4", 2)
    assert "children" not in design.nodes["1:4"].raw
    assert [n.id for n in design.screen_nodes("1:10")] == ["1:10", "1:11"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("AbC123", "AbC123"),
        ("https://www.figma.com/design/AbC123/My-App?node-id=1-2", "AbC123"),
        ("https://www.figma.com/file/AbC123/My-App", "AbC123"),
        ("https://www.figma.com/design/AbC123/branch/Br456/My-App", "Br456"),
    ],
)
def test_parse_file_key(text, expected):
    assert parse_file_key(text) == expected


def test_contract_round_trips_through_dict():
    violation = Violation("low_contrast", "low", ["1:2"])
    output = ComponentOutput("KEY", [ScreenAnalysis("1:1", 42.0, [violation])])
    assert ComponentOutput.from_dict(output.to_dict()) == output


def test_contract_rejects_bad_values():
    with pytest.raises(ValueError):
        Violation("low_contrast", "critical", [])
    with pytest.raises(ValueError):
        ScreenAnalysis("1:1", 120.0)
