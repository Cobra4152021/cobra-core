"""AIR capability catalog (provider- and model-neutral)."""

from __future__ import annotations

from enum import StrEnum


class AirCapability(StrEnum):
    """
    Machine-readable capabilities Computer may request.

    AIR matches these against provider/model descriptors. Vendors are never
    part of the request contract.
    """

    REASONING = "reasoning"
    VISION = "vision"
    OCR = "ocr"
    CODING = "coding"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    STRUCTURED_OUTPUT = "structured_output"
    LONG_CONTEXT = "long_context"
    OFFLINE = "offline"
    # Reserved for future registration (not required by initial profiles).
    AUDIO = "audio"
    VIDEO = "video"
    AGENTS = "agents"
    TEXT = "text"
    RESEARCH = "research"


# Initial capabilities explicitly in scope for KC-022.
INITIAL_CAPABILITIES: frozenset[AirCapability] = frozenset(
    {
        AirCapability.REASONING,
        AirCapability.VISION,
        AirCapability.OCR,
        AirCapability.CODING,
        AirCapability.SUMMARIZATION,
        AirCapability.CLASSIFICATION,
        AirCapability.TRANSLATION,
        AirCapability.STRUCTURED_OUTPUT,
        AirCapability.LONG_CONTEXT,
        AirCapability.OFFLINE,
        AirCapability.TEXT,
        AirCapability.RESEARCH,
    }
)

FUTURE_CAPABILITIES: frozenset[AirCapability] = frozenset(
    {
        AirCapability.AUDIO,
        AirCapability.VIDEO,
        AirCapability.AGENTS,
    }
)


def parse_air_capabilities(
    values: list[str] | tuple[str, ...] | frozenset[str] | set[str],
) -> frozenset[AirCapability]:
    """Parse capability strings; unknown names raise ValueError."""
    out: set[AirCapability] = set()
    for raw in values:
        key = str(raw).strip().lower()
        try:
            out.add(AirCapability(key))
        except ValueError as exc:
            raise ValueError(f"unknown AIR capability: {raw!r}") from exc
    return frozenset(out)
