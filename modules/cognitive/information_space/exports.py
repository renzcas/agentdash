"""JSON export helpers for ecology snapshots."""

from __future__ import annotations

import json
from pathlib import Path

from .engine import EcologySnapshot


def snapshot_to_json(snapshot: EcologySnapshot, *, indent: int = 2) -> str:
    """Serialize a snapshot while preserving the documented metric order."""
    return json.dumps(snapshot.to_dict(), indent=indent)


def write_snapshot(snapshot: EcologySnapshot, path: str | Path) -> None:
    """Write a snapshot as UTF-8 JSON, surfacing filesystem errors to callers."""
    Path(path).write_text(snapshot_to_json(snapshot) + "\n", encoding="utf-8")
