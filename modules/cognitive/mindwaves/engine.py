"""Track bounded, continuous changes in ecology and attention metrics."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import asdict, dataclass
from threading import RLock

from modules.cognitive.information_space.engine import EcologySnapshot
from modules.cognitive.information_space.metrics import DIMENSIONS


@dataclass(frozen=True)
class MindWavePoint:
    step: int
    fluctuation: float
    attention: float
    attention_delta: float


class MindWaves:
    """Keep a bounded history of metric fluctuations and attention movement."""

    def __init__(self, *, history_size: int = 60) -> None:
        if (
            isinstance(history_size, bool)
            or not isinstance(history_size, int)
            or history_size <= 0
        ):
            raise ValueError("history_size must be a positive integer")
        self._history: deque[MindWavePoint] = deque(maxlen=history_size)
        self._previous_scores: dict[str, float] | None = None
        self._step = 0
        self._lock = RLock()

    def ingest(self, snapshot: EcologySnapshot) -> dict[str, object]:
        """Record a snapshot and return the updated fluctuation state."""
        if not isinstance(snapshot, EcologySnapshot):
            raise TypeError("snapshot must be an EcologySnapshot")
        scores = snapshot.scores
        if set(scores) != set(DIMENSIONS):
            raise ValueError("snapshot must contain all 11 ecology dimensions")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
            for value in scores.values()
        ):
            raise ValueError("snapshot scores must be finite values between 0 and 1")

        with self._lock:
            if self._previous_scores is None:
                fluctuation = 0.0
                attention_delta = 0.0
            else:
                fluctuation = sum(
                    abs(scores[name] - self._previous_scores[name])
                    for name in scores
                ) / len(scores)
                attention_delta = (
                    scores.get("attention", 0.0)
                    - self._previous_scores.get("attention", 0.0)
                )

            self._step += 1
            self._history.append(
                MindWavePoint(
                    step=self._step,
                    fluctuation=fluctuation,
                    attention=scores.get("attention", 0.0),
                    attention_delta=attention_delta,
                )
            )
            self._previous_scores = dict(scores)
            return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        """Return the latest point and a copy of the bounded history."""
        with self._lock:
            latest = self._history[-1] if self._history else None
            return {
                "step": self._step,
                "fluctuation": latest.fluctuation if latest else 0.0,
                "attention": latest.attention if latest else 0.0,
                "attention_delta": latest.attention_delta if latest else 0.0,
                "history": [asdict(point) for point in self._history],
            }
