# UXDAS / Designly

Automated mobile-app UI/UX analysis for Figma designs — project **J26-IM-302**.

A local desktop tool: paste a Figma file link, and it scores every mobile screen for
interface complexity (C1) and cognitive load (C2), then ranks concrete fixes (C3).

| Component | Folder | Owner |
|---|---|---|
| C1 — Interface Complexity Analysis | `components/complexity/` | Senara (IT23177178) |
| C2 — Cognitive Load Estimation | `components/cognitive_load/` | De Alwis (IT23307544) |
| C3 — UI Recommendation System | `components/recommendation/` | Shen (IT23368170) |

Full spec: [UXDAS_SETUP.md](UXDAS_SETUP.md).

---

## Setup

Needs **Python 3.11+** (`python --version`).

Windows (Command Prompt):

```cmd
git clone <repo-url> UXDAS
cd UXDAS
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

macOS / Linux:

```bash
git clone <repo-url> UXDAS && cd UXDAS
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

In `.env` set:

- `FIGMA_TOKEN` — Figma → Settings → Security → Personal access tokens
- `GEMINI_API_KEY` — free key from aistudio.google.com/apikey (only needed for report phrasing)

`.env` is git-ignored. Never commit keys.

## Run

```cmd
streamlit run app/main.py
```

Opens at http://localhost:8501. Paste a Figma file key or URL and click **Run**.
Pick **Sample data** in the sidebar to run C3 on `tests/fixtures/` without any Figma token.

```cmd
pytest           # tests
ruff check .     # lint
```

---

## How the pieces fit

```
Figma file ──► shared/ingest.py ──► Design ──┬──► C1 analyze()  ──► ComponentOutput ──┐
              (fetched ONCE)                 └──► C2 estimate() ──► ComponentOutput ──┴──► C3 recommend() ──► ranked fixes + report
```

- **`shared/contracts.py`** is the only thing components share. C1 and C2 receive a
  `Design` and return a `ComponentOutput`. Never import another member's internals.
- **Scores are 0–100.** C3 treats `>= 60` as high (`components/recommendation/quadrant.py`).
- **`Violation.factor` must be a key under `factors` in
  `components/recommendation/rules.json`.** An unknown factor gets no fix and shows a warning
  in the app. The current list is a **draft** — agree it as a team.
- **Node IDs** must come from `design.nodes`, so all three components point at the same layers.
- Only `shared/figma_client.py` talks to Figma. Fetched files are cached in `output/cache/`;
  keep **Reuse cached Figma file** ticked while developing to avoid Figma rate limits.

### Current state

| Part | State |
|---|---|
| `shared/` (contract, Figma client, ingest) | Working, tested |
| C1 `analyze()` | **Placeholder** — layer count as score, no violations |
| C2 `estimate()` | **Placeholder** — text-layer count as score, no violations |
| C3 pipeline | **Baseline** — working quadrant → rules → Pareto → TOPSIS → report; to be replaced by the port of the existing engine (keep the `recommend()` signature) |
| `app/` (orchestrator + Streamlit UI) | Working |
| `apply/` | Not decided — see [apply/README.md](apply/README.md) |

---

## Team workflow

1. Pull the latest `main`, then branch for your component:
   ```cmd
   git checkout main
   git pull
   git checkout -b c1-complexity        (or c2-cognitive-load / c3-recommendation)
   ```
2. Work inside **your own folder** under `components/`. Add your tests as
   `tests/test_<component>.py`, and add fixture data to `tests/fixtures/` if you need it.
3. Before pushing, run `ruff check .` and `pytest`; both must pass.
4. Push your branch and open a pull request into `main`. Another member reviews it.
5. **Changes to `shared/`, `rules.json`, `app/` or `requirements.txt` affect everyone** — make
   them in a separate PR and get agreement from all three before merging.

New dependency? Add it to `requirements.txt` in its own PR, then everyone re-runs
`pip install -r requirements.txt` after pulling.
