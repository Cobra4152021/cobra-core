"""Execution idempotency — no duplicate proposals from retry/fallback."""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from typing import Any


def make_execution_id(
    *,
    skill_id: str,
    skill_version: str,
    correlation_id: str,
    revision: str,
    profile_id: str,
) -> str:
    """Bounded, non-secret key — never from prompts or evidence bodies."""
    material = "|".join(
        [
            skill_id.strip(),
            skill_version.strip(),
            (correlation_id or "").strip()[:64],
            revision.strip() or "1",
            profile_id.strip().lower(),
        ]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"rrf_{digest}"


@dataclass
class IdempotencyStore:
    """In-process store of completed logical executions."""

    _lock: threading.Lock = field(default_factory=threading.Lock)
    _results: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get(self, execution_id: str) -> dict[str, Any] | None:
        with self._lock:
            hit = self._results.get(execution_id)
            return dict(hit) if hit else None

    def put(self, execution_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            # Bound size
            if len(self._results) > 2000:
                # Drop arbitrary oldest-ish keys
                for k in list(self._results.keys())[:500]:
                    self._results.pop(k, None)
            self._results[execution_id] = dict(payload)

    def clear(self) -> None:
        with self._lock:
            self._results.clear()


IDEMPOTENCY_STORE = IdempotencyStore()
