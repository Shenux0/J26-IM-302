# UXDAS / Designly (J26-IM-302)

Our research project. It takes a Figma mobile app design and checks its UI/UX: how complex each screen is (C1), how much cognitive load it puts on the user (C2), and then it suggests fixes and ranks them (C3).

This branch has the base project I set up. Please go through this before you start your part.

## Who does what

| Component | Owner | Your folder | Your branch |
|---|---|---|---|
| C1 Interface Complexity Analysis | Senara | `components/complexity/` | `Component-01-Interface-Complexity-Analysis-IT23177178` |
| C2 Cognitive Load Estimation | De Alwis | `components/cognitive_load/` | `Component-02-Cognitive-Load-Estimation-IT23307544` |
| C3 UI Recommendation System | Shen | `components/recommendation/` | `Component-03-UI-Recommendation-system-IT23368170` |

## Setting up

You need Python 3.11 or newer (check with `python --version`) and Git.

**1. Clone the repo, switch to my branch and make your own branch from it**

```
git clone https://github.com/Shenux0/J26-IM-302.git
cd J26-IM-302
git checkout Component-03-UI-Recommendation-system-IT23368170
git checkout -b <your branch name from the table>
```

**2. Create a virtual environment and install the packages**

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Mac it's `python3 -m venv .venv` and `source .venv/bin/activate`.
If PowerShell says running scripts is disabled, just use Command Prompt.
In VS Code, select the .venv interpreter (Ctrl+Shift+P, then "Python: Select Interpreter").

**3. Add your Figma token**

```
copy .env.example .env
```

Open `.env` and paste your token after `FIGMA_TOKEN=`. You can make one in Figma under Settings > Security > Personal access tokens (read access to file content is enough). The Gemini key is optional, you don't need it for C1 or C2.

`.env` is in `.gitignore`, so it won't get committed. Keep it that way, don't share keys in the repo.

## Running it

```
streamlit run app/main.py
```

It opens in the browser at http://localhost:8501. We're running it in the browser while we develop, it'll be turned into a proper desktop app at the end.

- Paste a Figma file link and click Run. If a component isn't added yet, the app shows a message and uses 0 for its scores. That's expected for now.
- "Sample data" in the sidebar runs only my part (C3) on example data. No Figma token needed, it's a good way to see what the final output looks like.

Tests and lint:

```
pytest
ruff check .
```

## How the parts connect

```
Figma file -> shared/ingest.py -> Design -> C1 analyze() + C2 estimate() -> C3 recommend() -> ranked fixes + report
```

The Figma file gets downloaded once in `shared/ingest.py` and the same `Design` object is passed to C1 and C2. That way all of us work on the same screens and the same node IDs. Please don't call the Figma API yourself, everything you need is in the `Design`.

Everything we pass between components is defined in `shared/contracts.py`. Have a look at it, it's short.

## What you need to build

Create your folder with an `__init__.py` and a main file. For C1:

`components/complexity/__init__.py`

```python
from components.complexity.analyze import analyze
```

`components/complexity/analyze.py`

```python
from shared.contracts import ComponentOutput, Design, ScreenAnalysis, Violation


def analyze(design: Design) -> ComponentOutput:
    screens = []
    for screen in design.screens:
        nodes = design.screen_nodes(screen.id)
        score = ...       # your model, 0 to 100
        violations = []   # e.g. Violation(factor="...", severity="high", node_ids=["12:34"])
        screens.append(ScreenAnalysis(screen_id=screen.id, score=score, violations=violations))
    return ComponentOutput(file_key=design.file_key, screens=screens)
```

For C2 it's the same idea: folder `components/cognitive_load/`, file `estimate.py`, function `estimate(design)`.

Keep those function names, `app/orchestrator.py` looks for `analyze` and `estimate`. Apart from that, how you organise your folder is up to you. Add as many files as you need.

What your output has to follow:

- One `ScreenAnalysis` for every screen in `design.screens`.
- `score` is between 0 and 100. Higher means more complex (C1) or more load (C2). C3 treats 60 and above as high.
- `severity` is `"high"`, `"medium"` or `"low"`.
- `node_ids` must be IDs from `design.nodes`, so we can point to the exact layer in Figma.
- `factor` is the name of the factor the problem falls under, e.g. `"typography"` or `"touch_target_size"`. We still have to agree the exact names and how a violation links to the rules in `rules.json`, so check with me before you rely on them.

`tests/fixtures/c1_complexity.json` and `tests/fixtures/c2_cognitive_load.json` show what the output looks like (made-up data).

### What's inside a Design

- `design.screens`: the mobile screens. Each has `id`, `name`, `page`, `width`, `height` and `node_ids`.
- `design.nodes`: every layer of every screen, as a dict of node ID -> `Node`.
- `design.screen_nodes(screen_id)`: all layers of one screen, starting with the screen frame itself.

Each `Node` has:

- `id`, `name`, `type` (`FRAME`, `TEXT`, `RECTANGLE`, `INSTANCE`, `GROUP`, `VECTOR`, ...)
- `depth` (0 is the screen frame) and `parent_id`
- `bbox`: `(x, y, width, height)`
- `raw`: the original Figma JSON for that layer (without its children). For example on a `TEXT` node, `raw["characters"]` is the text, `raw["style"]["fontSize"]` the font size and `raw["fills"]` the colours.

Only top-level frames that are portrait and 320 to 480 px wide count as mobile screens, and hidden layers are skipped. So test with a Figma file that has normal phone-sized frames.

### Testing your code quickly

You don't have to click through the app every time. From the project folder, open `python` and:

```python
from shared.ingest import ingest
from components.complexity import analyze

design = ingest("YOUR_FILE_KEY", use_cache=True)
print(analyze(design))
```

The file key is the part right after `/design/` in the Figma link. With `use_cache=True` the file is saved in `output/cache/` the first time and reused after that, so you won't keep hitting Figma's rate limit. Untick "Reuse cached Figma file" in the app if you change the design in Figma and want a fresh copy.

## Working together

- Only change files inside your own component folder. Put your tests in `tests/test_complexity.py` or `tests/test_cognitive_load.py`.
- If you need to change anything in `shared/`, `app/`, `rules.json` or `requirements.txt`, talk to me first. Those affect everyone.
- If you add a package, put it in `requirements.txt` and tell the group so everyone installs it.
- Run `pytest` and `ruff check .` before you push.
- Push only to your own branch. Don't merge into `main` or into my branch. Once your part is working, let me know and we'll put everything together.

If something doesn't work or isn't clear, just message me.
