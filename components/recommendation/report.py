"""Build the Markdown report. The content is deterministic; Gemini may only rephrase it."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from components.recommendation.recommend import RankedFix, ScreenSummary

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

_PHRASING_PROMPT = """\
You are editing a UI/UX analysis report for a mobile app designer.
Rewrite it in clear, friendly, concise language. Keep every screen, fix, rank, score,
severity and layer ID exactly as given. Do not add, remove or reorder fixes.
Return Markdown only.

REPORT:
"""


class ReportPhrasingError(RuntimeError):
    """Gemini is not configured or the call failed; callers fall back to the plain report."""


def build_report(
    title: str,
    screens: list[ScreenSummary],
    fixes: list[RankedFix],
    unmatched_factors: list[str],
) -> str:
    lines = [f"# UXDAS report — {title}", "", "## Screens", ""]
    lines += ["| Screen | Complexity | Cognitive load | Quadrant |", "|---|---:|---:|---|"]
    lines += [
        f"| {s.name} | {s.complexity:.1f} | {s.cognitive_load:.1f} | {s.quadrant} |"
        for s in screens
    ]

    lines += ["", "## Ranked fixes", ""]
    if not fixes:
        lines.append("No fixes — no violations were reported.")
    for f in fixes:
        pareto = " · Pareto-optimal" if f.pareto_optimal else ""
        lines += [
            f"### {f.rank}. {f.title} — {f.screen_name}",
            f"- **Fix:** {f.fix}",
            f"- Severity: {f.severity} · Quadrant: {f.quadrant} · Score: {f.score:.3f}{pareto}",
            f"- Reported by: {', '.join(f.sources)} · Layers: {', '.join(f.node_ids) or '—'}",
            f"- Guideline: {f.guideline}",
            "",
        ]

    if unmatched_factors:
        lines += [
            "## Unknown factors",
            "",
            "These factors have no rule in rules.json, so no fix was produced:",
            "",
            *[f"- `{factor}`" for factor in unmatched_factors],
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def polish_with_gemini(markdown: str) -> str:
    """Rephrase the report with Gemini. Raises ReportPhrasingError on any failure."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_key_here":
        raise ReportPhrasingError("GEMINI_API_KEY is not set; showing the plain report.")
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            contents=_PHRASING_PROMPT + markdown,
        )
    except Exception as exc:  # network, quota, unknown model, ...
        message = f"Gemini phrasing failed ({exc}); showing the plain report."
        raise ReportPhrasingError(message) from exc
    return response.text or markdown
