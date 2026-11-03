import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import database
import server
from server import app
from modules.cognitive.runtime import cognitive_runtime
from state import state


class EcologyApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "investigations.db"
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_evaluates_signals_and_returns_mindwaves_state(self) -> None:
        response = self.client.post(
            "/api/ecology/evaluate",
            json={
                "session_id": "api-session",
                "signals": [
                    {
                        "content": "Observed system evidence",
                        "source": "sensor-a",
                        "confidence": 0.9,
                        "relevance": 0.8,
                        "attention": 1.0,
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["snapshot"]["signal_count"], 1)
        self.assertEqual(len(result["snapshot"]["scores"]), 11)
        self.assertEqual(result["snapshot"]["scores"]["attention"], 1.0)
        self.assertEqual(result["session_id"], "api-session")
        self.assertTrue(result["mindwaves"]["step"] > 0)

    def test_investigation_worker_publishes_progressive_ecology(self) -> None:
        session_id = "investigation:1"
        with (
            patch("server.update_investigation"),
            patch("server.save_investigation_concepts"),
        ):
            server.investigation_worker("How should memory work?", 1)

        self.assertEqual(state["status"], "Complete")
        current_state = cognitive_runtime.current_state(session_id=session_id)
        snapshot = current_state["snapshot"]
        self.assertEqual(snapshot["signal_count"], 6)
        self.assertEqual(snapshot["scores"]["attention"], 1.0 / 6)
        self.assertEqual(
            current_state["mindwaves"]["step"],
            6,
        )

    def test_api_sessions_keep_independent_mindwaves_histories(self) -> None:
        def evaluate(session_id: str, attention: float):
            return self.client.post(
                "/api/ecology/evaluate",
                json={
                    "session_id": session_id,
                    "signals": [{"content": "session signal", "attention": attention}],
                },
            )

        first = evaluate("session-a", 0.2).json()
        second = evaluate("session-a", 0.8).json()
        other = evaluate("session-b", 0.9).json()

        self.assertEqual(first["mindwaves"]["step"], 1)
        self.assertEqual(second["mindwaves"]["step"], 2)
        self.assertEqual(other["mindwaves"]["step"], 1)
        self.assertEqual(
            cognitive_runtime.current_state(session_id="session-a")["snapshot"]["scores"][
                "attention"
            ],
            0.8,
        )
        self.assertEqual(
            cognitive_runtime.current_state(session_id="session-b")["snapshot"]["scores"][
                "attention"
            ],
            0.9,
        )

    def test_api_creates_a_fresh_session_when_session_id_is_omitted(self) -> None:
        payload = {"signals": [{"content": "standalone evaluation"}]}

        first = self.client.post("/api/ecology/evaluate", json=payload).json()
        second = self.client.post("/api/ecology/evaluate", json=payload).json()

        self.assertNotEqual(first["session_id"], second["session_id"])
        self.assertEqual(first["mindwaves"]["step"], 1)
        self.assertEqual(second["mindwaves"]["step"], 1)

    def test_ecology_stream_requires_a_valid_session_id(self) -> None:
        self.assertEqual(self.client.get("/api/ecology/stream").status_code, 422)
        invalid = self.client.get(
            "/api/ecology/stream",
            params={"session_id": "invalid session"},
        )
        self.assertEqual(invalid.status_code, 422)

    def test_rejects_invalid_signal_fields_and_oversized_batches(self) -> None:
        invalid_inputs = [
            {"session_id": "bad session", "signals": [{"content": "signal"}]},
            {"signals": [{"content": "   "}]},
            {"signals": [{"content": "signal", "confidence": 2.0}]},
            {"signals": [{"content": "signal", "source": ""}]},
            {"signals": [{"content": "signal"}] * 101},
        ]

        for payload in invalid_inputs:
            with self.subTest(payload_size=len(payload["signals"])):
                response = self.client.post("/api/ecology/evaluate", json=payload)
                self.assertEqual(response.status_code, 422)

        non_finite = self.client.post(
            "/api/ecology/evaluate",
            content=b'{"signals":[{"content":"signal","confidence":NaN}]}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(non_finite.status_code, 422)

    def test_cockpit_serves_the_live_ecology_visualization(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information Ecology", response.text)
        self.assertIn("/api/ecology/stream?session_id=", response.text)


if __name__ == "__main__":
    unittest.main()
