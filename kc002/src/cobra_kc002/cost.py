"""Compute cost meter — hard-stop before budget ceiling."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CostMeter:
    max_hours: float
    max_cost_usd: float
    hourly_usd: float
    started_at: float
    spent_usd: float = 0.0
    hours: float = 0.0

    @classmethod
    def from_env(cls) -> "CostMeter":
        return cls(
            max_hours=float(os.environ.get("KC002_MAX_GPU_HOURS", "8")),
            max_cost_usd=float(os.environ.get("KC002_MAX_COST_USD", "100")),
            hourly_usd=float(os.environ.get("KC002_GPU_HOURLY_USD", "1.50")),
            started_at=time.time(),
        )

    def tick(self) -> None:
        self.hours = (time.time() - self.started_at) / 3600.0
        self.spent_usd = self.hours * self.hourly_usd

    def check(self) -> None:
        self.tick()
        if self.hours >= self.max_hours:
            raise RuntimeError(
                f"KC-002 hard stop: GPU hours {self.hours:.3f} >= {self.max_hours}"
            )
        if self.spent_usd >= self.max_cost_usd:
            raise RuntimeError(
                f"KC-002 hard stop: cost ${self.spent_usd:.2f} >= ${self.max_cost_usd}"
            )

    def save(self, path: Path) -> None:
        self.tick()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
