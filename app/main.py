"""Streamlit entry point. Run with: streamlit run app/main.py"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

# `streamlit run app/main.py` only puts app/ on sys.path; add the project root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app.orchestrator import PipelineResult, run, run_sample  # noqa: E402
from components.recommendation.quadrant import THRESHOLD  # noqa: E402
from shared.figma_client import FigmaError, parse_file_key  # noqa: E402

st.set_page_config(page_title="UXDAS / Designly", layout="wide")
st.title("UXDAS / Designly")
st.caption("Automated mobile UI/UX analysis for Figma designs")

with st.sidebar:
    source = st.radio("Input", ["Figma file", "Sample data"], help="Sample data runs C3 on "
                      "tests/fixtures and needs no Figma token.")
    use_cache = st.checkbox("Reuse cached Figma file", value=True,
                            help="Read output/cache/<key>.json instead of calling Figma again.")
    use_llm = st.checkbox("Polish report with Gemini", value=False)

file_input = ""
if source == "Figma file":
    file_input = st.text_input("Figma file key or URL", placeholder="https://www.figma.com/design/…")

if st.button("Run", type="primary"):
    try:
        with st.spinner("Analysing…"):
            if source == "Sample data":
                st.session_state.result = run_sample(use_llm=use_llm)
            elif not file_input.strip():
                st.warning("Enter a Figma file key or URL first.")
            else:
                key = parse_file_key(file_input)
                st.session_state.result = run(key, use_cache=use_cache, use_llm=use_llm)
    except FigmaError as exc:
        st.error(str(exc))

result: PipelineResult | None = st.session_state.get("result")
if result is None:
    st.stop()

rec = result.recommendation
for warning in rec.warnings:
    st.warning(warning)
if result.design is not None and not result.design.screens:
    st.info("No mobile screens found: top-level frames must be portrait and 320–480 px wide.")

tab_screens, tab_fixes, tab_report = st.tabs(["Screens", "Ranked fixes", "Report"])

with tab_screens:
    rows = [asdict(s) for s in rec.screens]
    st.caption(f"Quadrant threshold: {THRESHOLD:.0f} (complexity from C1, cognitive load from C2)")
    if rows:
        st.scatter_chart(rows, x="complexity", y="cognitive_load", color="quadrant")
    st.dataframe(rows, hide_index=True)

with tab_fixes:
    st.dataframe(
        [
            {
                "rank": f.rank,
                "screen": f.screen_name,
                "quadrant": f.quadrant,
                "issue": f.title,
                "fix": f.fix,
                "severity": f.severity,
                "score": f.score,
                "pareto": f.pareto_optimal,
                "layers": ", ".join(f.node_ids),
            }
            for f in rec.fixes
        ],
        hide_index=True,
    )

with tab_report:
    st.download_button(
        "Download report (.md)",
        rec.report_md,
        file_name=f"uxdas_report_{rec.file_key}.md",
        mime="text/markdown",
    )
    st.markdown(rec.report_md)
