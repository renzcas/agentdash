import json
import math
import tempfile
import unittest
from pathlib import Path

from modules.cognitive.information_space import (
    InformationEcologyEngine,
    InformationSignal,
)
from modules.cognitive.information_space.exports import (
    snapshot_to_json,
    write_snapshot,
)
from modules.cognitive.information_space.metrics import DIMENSIONS
from modules.cognitive.information_space.visualizations import build_ecology_figure


class InformationSignalTests(unittest.TestCase):
    def test_rejects_empty_content_and_out_of_range_metrics(self) -> None:
        with self.assertRaises(ValueError):
            InformationSignal(content=" ")
        with self.assertRaisesRegex(ValueError, "confidence"):
            InformationSignal(content="evidence", confidence=1.1)
        with self.assertRaisesRegex(ValueError, "utility"):
            InformationSignal(content="evidence", utility=float("nan"))


class InformationEcologyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = InformationEcologyEngine()

    def test_empty_input_returns_all_zero_dimensions(self) -> None:
        snapshot = self.engine.evaluate([])

        self.assertEqual(snapshot.signal_count, 0)
        self.assertEqual(tuple(snapshot.scores), DIMENSIONS)
        self.assertEqual(set(snapshot.scores.values()), {0.0})

    def test_calculates_all_eleven_dimensions_for_structured_signals(self) -> None:
        snapshot = self.engine.evaluate(
            [
                InformationSignal(
                    content="shared evidence signal",
                    source="sensor-a",
                    confidence=0.8,
                    relevance=0.9,
                    novelty=0.7,
                    attention=0.6,
                    retention=0.5,
                    prediction_error=0.2,
                    goal_alignment=0.9,
                    utility=0.8,
                ),
                InformationSignal(
                    content="shared evidence report",
                    source="sensor-b",
                    confidence=0.6,
                    relevance=0.7,
                    novelty=0.3,
                    attention=0.8,
                    retention=0.9,
                    prediction_error=0.4,
                    goal_alignment=0.7,
                    utility=0.6,
                ),
            ]
        )

        self.assertEqual(snapshot.signal_count, 2)
        self.assertEqual(tuple(snapshot.scores), DIMENSIONS)
        self.assertAlmostEqual(snapshot.scores["signal_volume"], 1 - math.exp(-0.4))
        self.assertEqual(snapshot.scores["source_diversity"], 1.0)
        self.assertAlmostEqual(snapshot.scores["coherence"], 0.5)
        self.assertAlmostEqual(snapshot.scores["uncertainty"], 0.3)
        self.assertAlmostEqual(snapshot.scores["relevance"], 0.8)
        self.assertAlmostEqual(snapshot.scores["memory"], 0.7)
        self.assertAlmostEqual(snapshot.scores["prediction_error"], 0.3)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in snapshot.scores.values()))

    def test_rejects_values_that_are_not_information_signals(self) -> None:
        with self.assertRaisesRegex(TypeError, "InformationSignal"):
            self.engine.evaluate(["not a signal"])

    def test_snapshot_can_be_serialized_and_written_as_json(self) -> None:
        snapshot = self.engine.evaluate([InformationSignal(content="evidence")])

        decoded = json.loads(snapshot_to_json(snapshot))
        self.assertEqual(decoded["signal_count"], 1)
        self.assertEqual(tuple(decoded["scores"]), DIMENSIONS)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            write_snapshot(snapshot, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), decoded)

    def test_builds_a_closed_radar_chart_for_the_snapshot(self) -> None:
        snapshot = self.engine.evaluate([InformationSignal(content="evidence")])

        figure = build_ecology_figure(snapshot)

        self.assertEqual(len(figure.data[0].r), len(DIMENSIONS) + 1)
        self.assertEqual(figure.data[0].r[0], figure.data[0].r[-1])


if __name__ == "__main__":
    unittest.main()
