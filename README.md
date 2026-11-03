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

## Cognitive modules

The cockpit displays live Information Ecology metrics and MindWaves fluctuation
history as investigation agents complete. Evaluate caller-provided signals with
`POST /api/ecology/evaluate`:

```json
{
  "signals": [
    {
      "content": "Observed evidence",
      "source": "sensor-a",
      "confidence": 0.9,
      "relevance": 0.8,
      "attention": 1.0
    }
  ],
  "session_id": "analysis-session-1"
}
```

The remaining signal dimensions default to `0.5`. The endpoint accepts at most
100 signals per request and returns `snapshot` (signal count and 11 scores) and
`mindwaves` (current fluctuation, attention movement, and bounded history).
Reuse the returned `session_id` on subsequent evaluations to continue that
session's history. If omitted, the endpoint creates a fresh session for that
request. `GET /api/ecology/stream?session_id=analysis-session-1` streams only
that session's state. Investigation sessions use `investigation:<id>` and the
cockpit switches its stream to the active investigation. Runtime state is
in-memory per server process, capped at 128 least-recently-used sessions, and
is cleared on process restart; an evicted session appears empty if queried
again. In-flight reads and evaluations pin their session; when the registry is
full of active sessions, creating another session waits until an operation
finishes before evicting the least-recently-used idle session. Session IDs
separate state but are not authentication credentials.
Multi-worker deployments need shared storage to keep evaluation and SSE state
consistent across workers.
The evaluation scores are descriptive indicators; lexical overlap is used for
coherence and does not represent semantic understanding.

## Run the separate Dash visualization

```bash
python main.py
```

Open the local URL printed by Dash (typically <http://127.0.0.1:8050>).

## Tests

```bash
python -m unittest discover -s tests -v
```
