"""Information Ecology Engine: score a collection of structured signals."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from .metrics import calculate_metrics


@dataclass(frozen=True)
class InformationSignal:
    """One evidence item and its explicitly supplied cognitive attributes."""

    content: str
    source: str = "unspecified"
    confidence: float = 0.5
    relevance: float = 0.5
    novelty: float = 0.5
    attention: float = 0.5
    retention: float = 0.5
    prediction_error: float = 0.5
    goal_alignment: float = 0.5
    utility: float = 0.5

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        for name in (
            "confidence",
            "relevance",
            "novelty",
            "attention",
            "retention",
            "prediction_error",
            "goal_alignment",
            "utility",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise ValueError(f"{name} must be a finite number between 0 and 1")


@dataclass(frozen=True)
class EcologySnapshot:
    """A stable metric result suitable for APIs, visualization, and export."""

    signal_count: int
    scores: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class InformationEcologyEngine:
    """Calculate an 11-dimensional descriptive profile from information signals."""

    def evaluate(
        self, signals: Iterable[InformationSignal]
    ) -> EcologySnapshot:
        signal_list = list(signals)
        if any(not isinstance(signal, InformationSignal) for signal in signal_list):
            raise TypeError("signals must contain only InformationSignal values")
        return EcologySnapshot(
            signal_count=len(signal_list),
            scores=calculate_metrics(signal_list),
        )
