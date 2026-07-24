"""Frozen Protocol V1 constants (must match Cobra Computer flags)."""

PROTOCOL_VERSION = "1"
COMPATIBILITY_VERSION = "1"
PROVIDER_ID = "cobra-core"
DEFAULT_MODEL = "cobra-core-qwen3-8b"

# Capability keys (machine-readable; future negotiation without redesign).
CAPABILITY_KEYS = (
    "streaming",
    "vision",
    "toolCalling",
    "jsonMode",
    "thinking",
    "embeddings",
)
