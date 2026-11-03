import unittest

from modules.cognitive.information_space import (
    InformationEcologyEngine,
    InformationSignal,
)
from modules.cognitive.information_space.engine import EcologySnapshot
from modules.cognitive.mindwaves import MindWaves


class MindWavesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ecology = InformationEcologyEngine()

    def test_tracks_metric_fluctuation_and_attention_change(self) -> None:
        waves = MindWaves()
        baseline = self.ecology.evaluate(
            [InformationSignal(content="baseline", attention=0.2)]
        )
        changed = self.ecology.evaluate(
            [InformationSignal(content="changed", attention=0.8, novelty=0.9)]
        )

        first = waves.ingest(baseline)
        current = waves.ingest(changed)

        self.assertEqual(first["fluctuation"], 0.0)
        self.assertEqual(current["step"], 2)
        self.assertGreater(current["fluctuation"], 0.0)
        self.assertAlmostEqual(current["attention_delta"], 0.6)
        self.assertEqual(len(current["history"]), 2)

    def test_keeps_only_the_configured_history(self) -> None:
        waves = MindWaves(history_size=2)
        snapshot = self.ecology.evaluate([])

        for _ in range(3):
            current = waves.ingest(snapshot)

        self.assertEqual(current["step"], 3)
        self.assertEqual([point["step"] for point in current["history"]], [2, 3])

    def test_rejects_invalid_history_size_and_incomplete_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            MindWaves(history_size=0)

        with self.assertRaisesRegex(ValueError, "dimensions"):
            MindWaves().ingest(EcologySnapshot(signal_count=0, scores={"other": 0.0}))

    def test_rejects_non_snapshot_input(self) -> None:
        with self.assertRaisesRegex(TypeError, "EcologySnapshot"):
            MindWaves().ingest({"scores": {}})


if __name__ == "__main__":
    unittest.main()
