# UXDAS / Designly — Project Setup Spec (Python + Streamlit)

> Hand this to Claude Code (or follow it yourself) to scaffold the folder structure and install dependencies for the **whole 3-component desktop software**. This is the shared base all three members build on top of.

Project: **J26-IM-302 (UXDAS / Designly)** — automated mobile-app UI/UX analysis for Figma designs.

Components:
- **C1 — Interface Complexity Analysis** (Senara, IT23177178)
- **C2 — Cognitive Load Estimation** (De Alwis, IT23307544)
- **C3 — UI Recommendation System** (Shen, IT23368170)

---

## 1. Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| Figma read | `requests` (Figma REST API) |
| LLM | Google Gemini via `google-genai` |
| MCDM / maths | NumPy |
| Tests | pytest |
| Config | python-dotenv |
| Lint/format | ruff |

Runs as a **local desktop tool**: launch with one command, use it in the browser on `localhost`.

---

## 2. Prerequisites

- **Python 3.11 or newer** — check with `python --version`. If missing, install from python.org (tick "Add Python to PATH").
- A **Google Gemini API key** (free) from `aistudio.google.com/apikey`.

---

## 3. Folder structure

```
UXDAS/
├── app/
│   ├── main.py                 # Streamlit entry point (the UI)
│   └── orchestrator.py         # runs ingest → C1 → C2 → C3, wires outputs
│
├── shared/
│   ├── __init__.py
│   ├── contracts.py            # the data contract ALL components import
│   ├── figma_client.py         # ONE Figma REST client
│   └── ingest.py               # fetch the file ONCE, build node tree + frame list
│
├── components/
│   ├── __init__.py
│   ├── complexity/             # C1 — Senara
│   │   ├── __init__.py
│   │   └── analyze.py          # analyze(design) -> ComponentOutput
│   ├── cognitive_load/         # C2 — De Alwis
│   │   ├── __init__.py
│   │   └── estimate.py         # estimate(design) -> ComponentOutput
│   └── recommendation/         # C3 — Shen (port of the existing engine)
│       ├── __init__.py
│       ├── aggregate.py
│       ├── quadrant.py
│       ├── rule_engine.py
│       ├── pareto.py
│       ├── topsis.py
│       ├── report.py
│       ├── recommend.py        # orchestrates C3's own pipeline
│       └── rules.json          # the mobile UI rule set
│
├── apply/                      # the "apply fixes" arm (plugin bridge OR report-only)
│   └── README.md               # decide later; see note in §9
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── c1_complexity.json
│   │   └── c2_cognitive_load.json
│   └── test_recommendation.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml              # ruff + pytest config
└── README.md
```

Each member owns one folder under `components/`. They integrate only through `shared/contracts.py` — never by importing each other's internals.

---

## 4. Setup commands

Windows (Command Prompt), run from where you want the project:

```cmd
mkdir UXDAS
cd UXDAS
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS / Linux:

```bash
mkdir UXDAS && cd UXDAS
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> Create `requirements.txt` (below) **before** the `pip install` line.

Then set up your key:

```cmd
copy .env.example .env
notepad .env
```
Put `GEMINI_API_KEY=your_key_here` in it and save.

---

## 5. requirements.txt

```
streamlit>=1.40
requests>=2.32
google-genai>=0.3
numpy>=2.0
python-dotenv>=1.0
pytest>=8.0
ruff>=0.6
```

---

## 6. .env.example

```
# Figma personal access token (read designs). Create one in Figma → Settings → Security.
FIGMA_TOKEN=your_figma_token_here

# Google Gemini API key (report phrasing / C2 reasoning). From aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_key_here
```

## 7. .gitignore

```
.venv/
__pycache__/
*.pyc
.env
output/
.pytest_cache/
.ruff_cache/
```

---

## 8. shared/contracts.py — the single most important file

Every component reads and writes this shape. Agree on it before writing any component logic.

```python
"""Shared data contract for all UXDAS components."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Violation:
    factor: str            # key looked up in C3's rules.json (shared vocabulary!)
    severity: str          # "high" | "medium" | "low"
    node_ids: list[str]    # Figma node IDs where the issue occurs


@dataclass
class ScreenAnalysis:
    screen_id: str
    score: float           # 0–100. complexity for C1, cognitive load for C2
    violations: list[Violation] = field(default_factory=list)


@dataclass
class ComponentOutput:
    file_key: str
    screens: list[ScreenAnalysis] = field(default_factory=list)
```

**Rules of the contract:**
- Scores are **0–100** (C3's quadrant threshold is 60).
- `factor` strings **must match the keys in `components/recommendation/rules.json`** exactly, or C3 silently produces no fix. This shared vocabulary is the thing all three must agree on in writing.
- `node_ids` come from the **single ingest**, so all three reference the same node tree.

---

## 9. What each shared piece does

- **`shared/figma_client.py`** — one function: `get_file(file_key) -> dict`, calling the Figma REST API `GET /v1/files/:key` with the `FIGMA_TOKEN`. Nobody else calls Figma directly.
- **`shared/ingest.py`** — `ingest(file_key) -> Design`: fetch the file once, extract the mobile frames (screens) and a flat node list with IDs. C1 and C2 both analyse **this**, so their scores and node IDs line up.
- **`app/orchestrator.py`** — `run(file_key)`: `ingest → complexity.analyze → cognitive_load.estimate → recommendation.recommend`, returning the final ranked fixes + report.
- **`app/main.py`** — Streamlit UI: a text box for the Figma file key, a Run button, and panels showing each screen's quadrant, ranked fixes, and the report (with a download button).
- **`apply/`** — the "write fixes back to Figma" arm. Note: Figma's REST API is **read-only for design content**, so applying edits needs either a small Figma plugin fed by C3's fix list, or you keep the output as the report only. Decide this with your team; it does not block building everything else.

---

## 10. How to run

With the venv active:

```cmd
streamlit run app/main.py
```

It opens in your browser at `http://localhost:8501`. Paste a Figma file key, click Run.

Run the tests:

```cmd
pytest
```

Lint:

```cmd
ruff check .
```

---

## 11. Build order

1. Scaffold the folders + files above; install deps (§4).
2. Write `shared/contracts.py` and **agree the `factor` vocabulary** with the team.
3. Write `shared/figma_client.py` + `shared/ingest.py`.
4. Each member builds their `components/<x>/` to take the ingested design and return a `ComponentOutput`.
5. Port C3's engine into `components/recommendation/` (ask Claude for the Python port of the existing, tested engine).
6. Wire `app/orchestrator.py`, then `app/main.py`.
7. Decide the `apply/` arm.

---

## 12. Non-goals / constraints

- Mobile app UI designs only.
- C3 core (quadrant, rules, Pareto, TOPSIS) is **deterministic**; the LLM only phrases the report.
- Secrets in `.env` only; `.env` is git-ignored.
- No Figma canvas writes over REST (Figma limitation) — see §9.
