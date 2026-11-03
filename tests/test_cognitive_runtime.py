from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread
import unittest
from unittest.mock import patch

from modules.cognitive.information_space import InformationSignal
from modules.cognitive.runtime import CognitiveRuntime, _SessionRuntime


class CognitiveRuntimeTests(unittest.TestCase):
    def test_session_histories_and_latest_snapshots_are_isolated(self) -> None:
        runtime = CognitiveRuntime()

        runtime.evaluate(
            [InformationSignal(content="alpha", attention=0.2)],
            session_id="session-a",
        )
        runtime.evaluate(
            [InformationSignal(content="beta", attention=0.8)],
            session_id="session-a",
        )
        runtime.evaluate(
            [InformationSignal(content="gamma", attention=0.9)],
            session_id="session-b",
        )

        first_session = runtime.current_state(session_id="session-a")
        second_session = runtime.current_state(session_id="session-b")
        unknown_session = runtime.current_state(session_id="not-created")

        self.assertEqual(first_session["mindwaves"]["step"], 2)
        self.assertEqual(len(first_session["mindwaves"]["history"]), 2)
        self.assertEqual(first_session["snapshot"]["scores"]["attention"], 0.8)
        self.assertEqual(second_session["mindwaves"]["step"], 1)
        self.assertEqual(second_session["snapshot"]["scores"]["attention"], 0.9)
        self.assertIsNone(unknown_session["snapshot"])
        self.assertEqual(unknown_session["mindwaves"]["step"], 0)

    def test_evicted_session_is_returned_as_empty_and_capacity_is_bounded(self) -> None:
        runtime = CognitiveRuntime(max_sessions=1)
        signal = [InformationSignal(content="bounded")]
        runtime.evaluate(signal, session_id="older")
        runtime.evaluate(signal, session_id="newer")

        self.assertIsNone(runtime.current_state(session_id="older")["snapshot"])
        self.assertEqual(runtime.current_state(session_id="newer")["mindwaves"]["step"], 1)

    def test_in_flight_evaluation_pins_session_against_lru_eviction(self) -> None:
        runtime = CognitiveRuntime(max_sessions=1)
        evaluation_started = Event()
        allow_evaluation_to_finish = Event()
        second_evaluation_started = Event()
        original_evaluate = _SessionRuntime.evaluate

        def delayed_evaluate(session, signals):
            if current_thread().name.startswith("pinned-evaluation"):
                evaluation_started.set()
                if not allow_evaluation_to_finish.wait(timeout=5):
                    raise TimeoutError("test did not release pinned evaluation")
            return original_evaluate(session, signals)

        first_signal = [InformationSignal(content="first", attention=0.25)]
        second_signal = [InformationSignal(content="second", attention=0.75)]

        with patch.object(_SessionRuntime, "evaluate", delayed_evaluate):
            with ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="pinned-evaluation"
            ) as pool:
                first = pool.submit(
                    runtime.evaluate,
                    first_signal,
                    session_id="first-session",
                )
                self.assertTrue(evaluation_started.wait(timeout=2))

                def evaluate_second_session():
                    second_evaluation_started.set()
                    return runtime.evaluate(
                        second_signal,
                        session_id="second-session",
                    )

                second = pool.submit(evaluate_second_session)
                self.assertTrue(second_evaluation_started.wait(timeout=2))
                self.assertFalse(second.done())

                allow_evaluation_to_finish.set()
                first_result = first.result(timeout=2)
                second_result = second.result(timeout=2)

        self.assertEqual(first_result["snapshot"]["signal_count"], 1)
        self.assertEqual(first_result["snapshot"]["scores"]["attention"], 0.25)
        self.assertEqual(second_result["snapshot"]["scores"]["attention"], 0.75)
        self.assertEqual(
            runtime.current_state(session_id="second-session")["snapshot"]["scores"][
                "attention"
            ],
            0.75,
        )

    def test_rejects_invalid_session_ids_and_capacity(self) -> None:
        with self.assertRaises(ValueError):
            CognitiveRuntime(max_sessions=0)

        runtime = CognitiveRuntime()
        for invalid_id in ("", "has spaces", "x" * 129):
            with self.subTest(session_id=invalid_id):
                with self.assertRaises(ValueError):
                    runtime.current_state(session_id=invalid_id)


if __name__ == "__main__":
    unittest.main()
