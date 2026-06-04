import time
import json

def stream_trace(token, role="agent", attention=None, stream_id="default"):
    trace = {
        "type": "token_trace",
        "data": {
            "token": token,
            "role": role,
            "timestamp": time.time(),
            "attention": attention,
            "stream_id": stream_id
        }
    }
    return f"data: {json.dumps(trace)}\n\n"
