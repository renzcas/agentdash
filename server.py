from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import platform, sys, time, json, os
from modules.trace_utils import stream_trace
from pulse import emit_pulse
from modules.complex_attention import build_complex_attention, collapse_attention, phase_entropy
from fastapi.staticfiles import StaticFiles

from transformers import AutoModel, AutoTokenizer
import torch

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

def event_stream():
    session_id = f"session_{int(time.time())}"  # Unique per stream

    while True:
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