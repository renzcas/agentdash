import time
import json

def emit_pulse(message, role="agent", stream_id="default", critique=None):
    pulse = {
        "type": "agent_pulse",
        "data": {
            "message": message,
            "role": role,
            "timestamp": time.time(),
            "stream_id": stream_id,
            "critique": critique
        }
    }
    return f"data: {json.dumps(pulse)}\n\n"