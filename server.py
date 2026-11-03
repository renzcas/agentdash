from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from functools import lru_cache
from pydantic import BaseModel
import platform, sys, time, json, os
from modules.trace_utils import stream_trace
from pulse import emit_pulse
from fastapi.staticfiles import StaticFiles

from agents import PILLARS
from agents.pipeline import run_agents
from database import (
    create_investigation,
    get_all_investigations,
    init_db,
    save_investigation_concepts,
    update_investigation,
)
from modules.symbolic_memory import extract_concepts
from state import state

app = FastAPI()


class InvestigationRequest(BaseModel):
    question: str


@app.on_event("startup")
async def startup() -> None:
    init_db()

def get_metadata():
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", "unknown"),
        "cwd": os.getcwd(),
        "timestamp": time.time()
    }

def investigation_worker(question: str, investigation_id: int) -> None:
    try:
        state["question"] = question
        state["investigation_id"] = investigation_id
        state["status"] = "Starting"
        state["progress"] = 10
        state["trace"] = ""
        state["trace_history"] = ["Starting investigation"]
        state["observation"] = ""
        state["insight"] = ""
        state["agent_results"] = {}
        state["error"] = None
        update_investigation(
            investigation_id,
            status="Starting",
            progress=10,
            agent_results=json.dumps(state["agent_results"]),
        )

        results = run_agents(question)
        concepts = extract_concepts(question)
        save_investigation_concepts(investigation_id, concepts)
        for index, (agent_name, result) in enumerate(results.items(), start=1):
            state["agent_results"][agent_name] = result
            state["status"] = f"{agent_name} Agent"
            state["trace"] = next(
                (value for key, value in result.items() if key not in {"agent", "status"}),
                "Agent completed.",
            )
            state["progress"] = 10 + round(index * 80 / len(results))
            state["trace_history"].append(f"{agent_name}: {state['trace']}")
            update_investigation(
                investigation_id,
                status=state["status"],
                progress=state["progress"],
                agent_results=json.dumps(state["agent_results"]),
            )

        state["observation"] = results["Observer"]["observation"]
        state["insight"] = " ".join(
            (
                results["Compression"]["summary"],
                results["Wisdom"]["reflection"],
                results["Wisdom"]["evidence_limit"],
                f"Recommended next step: {results['Builder']['next_step']}",
                results["Agency"]["recommendation"],
            )
        )
        state["progress"] = 100
        state["status"] = "Complete"
        state["trace_history"].append("Investigation complete")
        update_investigation(
            investigation_id,
            status="Complete",
            progress=100,
            observation=state["observation"],
            insight=state["insight"],
            agent_results=json.dumps(state["agent_results"]),
        )
    except Exception as e:
        state["status"] = "Failed"
        state["error"] = str(e)
        state["trace_history"].append("Investigation failed")
        update_investigation(
            investigation_id,
            status="Failed",
            error=state["error"],
            agent_results=json.dumps(state["agent_results"]),
        )

@app.post("/api/run")
async def run_investigation(payload: InvestigationRequest, background_tasks: BackgroundTasks):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    investigation_id = create_investigation(question)
    background_tasks.add_task(investigation_worker, question, investigation_id)
    return {"success": True, "investigation_id": investigation_id}


@app.get("/api/investigations")
async def list_investigations():
    return get_all_investigations()


@app.get("/api/pillars")
async def list_pillars():
    return PILLARS

def event_stream():
    session_id = f"session_{int(time.time())}"

    while True:
        # 📊 Emit Dashboard State First
        yield f"""data: {json.dumps({
            'type': 'dashboard',
            'investigation_id': state['investigation_id'],
            'question': state['question'],
            'status': state['status'],
            'progress': state['progress'],
            'trace': state['trace'],
            'trace_history': state['trace_history'],
            'observation': state['observation'],
            'insight': state['insight'],
            'agent_results': state['agent_results'],
            'error': state['error']
        })}\n\n"""
        time.sleep(1)

        # 🔁 Interpreter pulse
        yield f"""data: {json.dumps({
            'type': 'interpreter_pulse',
            'data': get_metadata(),
            'stream_id': session_id
        })}\n\n"""
        time.sleep(2)

        # 🧠 Agent pulses
        yield emit_pulse("Planner initialized", role="planner", stream_id=session_id)
        time.sleep(1)
        yield emit_pulse("Critic evaluating plan...", role="critic", stream_id=session_id, critique="Too linear")
        time.sleep(1)

        # 🧠 Token-level trace
        for token in ["The", "agent", "is", "thinking", "..."]:
            yield stream_trace(token, role="planner", stream_id=session_id)
            time.sleep(0.5)

@app.get("/stream")
async def stream(request: Request):
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@lru_cache(maxsize=1)
def load_attention_model():
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    model = AutoModel.from_pretrained("bert-base-uncased", attn_implementation="eager")
    input_ids = tokenizer("The agent is thinking...", return_tensors="pt")["input_ids"]
    return model, input_ids


@app.get("/complex-attention")
def stream_complex_attention():
    import torch
    from modules.complex_attention import build_complex_attention, collapse_attention, phase_entropy

    model, input_ids = load_attention_model()
    outputs = model(input_ids, output_attentions=True)
    attention_tensor = torch.stack(outputs.attentions)

    A_complex = build_complex_attention(attention_tensor)
    collapsed = collapse_attention(A_complex)
    entropy = phase_entropy(A_complex)

    def gen():
        yield f"data: {{\"collapsed\": {collapsed.tolist()}, \"entropy\": {entropy.tolist()}}}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory="static", html=True), name="static")