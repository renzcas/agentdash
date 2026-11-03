"""Bounded, thread-safe ecology runtimes scoped to independent sessions."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import re
from threading import Condition, RLock

from modules.cognitive.information_space.engine import (
    EcologySnapshot,
    InformationEcologyEngine,
    InformationSignal,
)
from modules.cognitive.mindwaves import MindWaves

_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


@dataclass
class _SessionRuntime:
    engine: InformationEcologyEngine = field(default_factory=InformationEcologyEngine)
    mind_waves: MindWaves = field(default_factory=MindWaves)
    latest: EcologySnapshot | None = None
    lock: RLock = field(default_factory=RLock)

    def evaluate(self, signals: Iterable[InformationSignal]) -> dict[str, object]:
        with self.lock:
            snapshot = self.engine.evaluate(signals)
            waves = self.mind_waves.ingest(snapshot)
            self.latest = snapshot
            return {"snapshot": snapshot.to_dict(), "mindwaves": waves}

    def current_state(self) -> dict[str, object]:
        with self.lock:
            return {
                "snapshot": self.latest.to_dict() if self.latest else None,
                "mindwaves": self.mind_waves.snapshot(),
            }


class CognitiveRuntime:
    """Keep independent per-session MindWaves histories with bounded retention."""

    def __init__(self, *, max_sessions: int = 128) -> None:
        if (
            isinstance(max_sessions, bool)
            or not isinstance(max_sessions, int)
            or max_sessions <= 0
        ):
            raise ValueError("max_sessions must be a positive integer")
        self._max_sessions = max_sessions
        self._sessions: OrderedDict[str, _SessionRuntime] = OrderedDict()
        self._active_operations: dict[str, int] = {}
        self._condition = Condition(RLock())

    @contextmanager
    def _session(
        self, session_id: str, *, create: bool
    ) -> Iterator[_SessionRuntime | None]:
        if (
            not isinstance(session_id, str)
            or not _SESSION_ID_PATTERN.fullmatch(session_id)
        ):
            raise ValueError(
                "session_id must be 1-128 letters, digits, dots, underscores, colons, "
                "or hyphens, starting with a letter or digit"
            )
        with self._condition:
            runtime = self._sessions.get(session_id)
            if runtime is None and create:
                while len(self._sessions) >= self._max_sessions:
                    evictable_id = next(
                        (
                            active_id
                            for active_id in self._sessions
                            if self._active_operations.get(active_id, 0) == 0
                        ),
                        None,
                    )
                    if evictable_id is not None:
                        del self._sessions[evictable_id]
                        self._active_operations.pop(evictable_id, None)
                        break
                    self._condition.wait()

                runtime = _SessionRuntime()
                self._sessions[session_id] = runtime
                self._active_operations[session_id] = 0
            elif runtime is None:
                yield None
                return

            self._sessions.move_to_end(session_id)
            self._active_operations[session_id] += 1

        try:
            yield runtime
        finally:
            with self._condition:
                self._active_operations[session_id] -= 1
                self._condition.notify_all()

    def evaluate(
        self,
        signals: Iterable[InformationSignal],
        *,
        session_id: str,
    ) -> dict[str, object]:
        with self._session(session_id, create=True) as runtime:
            if runtime is None:
                raise RuntimeError("session runtime creation failed")
            return {
                "session_id": session_id,
                **runtime.evaluate(signals),
            }

    def current_state(self, *, session_id: str) -> dict[str, object]:
        with self._session(session_id, create=False) as runtime:
            return {
                "session_id": session_id,
                **(
                    runtime.current_state()
                    if runtime is not None
                    else {
                        "snapshot": None,
                        "mindwaves": {
                            "step": 0,
                            "fluctuation": 0.0,
                            "attention": 0.0,
                            "attention_delta": 0.0,
                            "history": [],
                        },
                    }
                ),
            }


cognitive_runtime = CognitiveRuntime()
