# AgentDash

AgentDash is a small Python project with two local dashboards:

- The main AgentDash Cockpit is served by FastAPI and displays investigation
  results from six deterministic agent classes.
- A separate Dash page in `main.py` plots a Lorenz-style attention trace.

The six-agent pipeline is rule-based Python code; it does not call an LLM.
The FastAPI server also loads the Hugging Face `bert-base-uncased` model at
startup for the `/complex-attention` endpoint. The first run may download
model files and take longer to start.

## Setup

Use Python 3.11 or newer, then create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the AgentDash Cockpit

From the repository root:

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The API also provides `/api/run`,
`/api/investigations`, `/api/pillars`, `/stream`, and `/complex-attention`.
Investigation history is stored in `data/investigations.db`.
Completed investigations also store deterministic keyword symbols in SQLite.
History cards show earlier completed investigations that share those symbols;
this is exact keyword matching, not semantic or vector search.

## Run the separate Dash visualization

```bash
python main.py
```

Open the local URL printed by Dash (typically <http://127.0.0.1:8050>).

## Tests

```bash
python -m unittest discover -s tests -v
```
