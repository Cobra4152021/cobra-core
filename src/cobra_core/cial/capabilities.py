"""Typed capability values for CIAL model registration and routing."""

from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    """Machine-readable capabilities a model may declare."""

    TEXT = "text"
    REASONING = "reasoning"
    JSON = "json"
    TOOLS = "tools"
    VISION = "vision"
    STREAMING = "streaming"
    RESEARCH = "research"


def parse_capabilities(values: list[str] | tuple[str, ...] | frozenset[str]) -> frozenset[Capability]:
    """Parse capability strings into a frozenset; unknown names raise ValueError."""
    out: set[Capability] = set()
    for raw in values:
        key = str(raw).strip().lower()
        try:
            out.add(Capability(key))
        except ValueError as exc:
            raise ValueError(f"unknown capability: {raw!r}") from exc
    return frozenset(out)
