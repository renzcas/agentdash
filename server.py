from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
import platform, sys, time, json, os
from modules.trace_utils import stream_trace
from pulse import emit_pulse
from modules.complex_attention import build_complex_attention, collapse_attention, phase_entropy
from fastapi.staticfiles import StaticFiles
from transformers import AutoModel, AutoTokenizer
import torch

from state import state

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

input_ids = tokenizer("The agent is thinking...", return_tensors="pt")["input_ids"]
app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

def get_metadata():
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", "unknown"),
        "cwd": os.getcwd(),
        "timestamp": time.time()
    }

def investigation_worker(question):
    try:
        state["question"] = question
        state["status"] = "Starting"
        state["progress"] = 10
        time.sleep(1)
        
        state["status"] = "Building Model"
        state["trace"] = "Constructing symbolic graph"
        state["progress"] = 40
        time.sleep(2)
        
        state["status"] = "Analyzing"
        state["trace"] = "Evaluating memory relationships"
        state["progress"] = 70
        time.sleep(2)
        
        state["observation"] = "Memory activity detected"
        state["progress"] = 100
        state["status"] = "Complete"
    except Exception as e:
        state["status"] = "Failed"
        state["error"] = str(e)

@app.post("/api/run")
async def run_investigation(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    question = body.get("question", "Unknown Question")
    background_tasks.add_task(investigation_worker, question)
    return {"success": True}

def event_stream():
    session_id = f"session_{int(time.time())}"

    while True:
        # 📊 Emit Dashboard State First
        yield f"""data: {json.dumps({
            'type': 'dashboard',
            'question': state['question'],
            'status': state['status'],
            'progress': state['progress'],
            'trace': state['trace'],
            'observation': state['observation'],
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

@app.get("/complex-attention")
async def stream_complex_attention(request: Request):
    outputs = model(input_ids, output_attentions=True)
    attention_tensor = torch.stack(outputs.attentions)

    A_complex = build_complex_attention(attention_tensor)
    collapsed = collapse_attention(A_complex)
    entropy = phase_entropy(A_complex)

    def gen():
        yield f"data: {{\"collapsed\": {collapsed.tolist()}, \"entropy\": {entropy.tolist()}}}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")