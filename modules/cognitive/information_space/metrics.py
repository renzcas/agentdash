"""Deterministic, bounded metrics for an information ecology."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import InformationSignal


DIMENSIONS = (
    "signal_volume",
    "source_diversity",
    "coherence",
    "novelty",
    "uncertainty",
    "relevance",
    "attention",
    "memory",
    "prediction_error",
    "goal_alignment",
    "utility",
)

_TOKEN_PATTERN = re.compile(r"[^\W\d_]+", re.UNICODE)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _coherence(signals: Sequence[InformationSignal]) -> float:
    if not signals:
        return 0.0
    if len(signals) == 1:
        return 1.0

    token_sets = [
        {word.casefold() for word in _TOKEN_PATTERN.findall(signal.content)}
        for signal in signals
    ]
    pair_scores = []
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            union = left | right
            pair_scores.append(len(left & right) / len(union) if union else 0.0)
    return _mean(pair_scores)


def calculate_metrics(signals: Sequence[InformationSignal]) -> dict[str, float]:
    """Return the 11 ecology dimensions in the documented order."""
    count = len(signals)
    if count == 0:
        return dict.fromkeys(DIMENSIONS, 0.0)

    return {
        "signal_volume": 1.0 - math.exp(-count / 5.0),
        "source_diversity": len({signal.source for signal in signals}) / count,
        "coherence": _coherence(signals),
        "novelty": _mean([signal.novelty for signal in signals]),
        "uncertainty": _mean([1.0 - signal.confidence for signal in signals]),
        "relevance": _mean([signal.relevance for signal in signals]),
        "attention": _mean([signal.attention for signal in signals]),
        "memory": _mean([signal.retention for signal in signals]),
        "prediction_error": _mean(
            [signal.prediction_error for signal in signals]
        ),
        "goal_alignment": _mean(
            [signal.goal_alignment for signal in signals]
        ),
        "utility": _mean([signal.utility for signal in signals]),
    }
