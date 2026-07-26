"""Versioned static price table (no live pricing APIs)."""

from __future__ import annotations

# USD per 1M tokens — conservative staging estimates (KC-026).
PRICE_TABLE_VERSION = "kc026-v1"

# (input_per_mtok, output_per_mtok)
_STATIC: dict[tuple[str, str], tuple[float, float]] = {
    ("mock", "*"): (0.0, 0.0),
    ("openai", "gpt-5.4-mini"): (0.15, 0.60),
    ("openai", "*"): (0.50, 1.50),
}


def estimate_cost_usd(
    provider_id: str,
    model_id: str,
    *,
    input_tokens: int,
    output_tokens: int,
) -> float:
    key = (provider_id.strip().lower(), model_id.strip())
    rates = _STATIC.get(key) or _STATIC.get((provider_id.strip().lower(), "*")) or (1.0, 2.0)
    inp, out = rates
    return round((max(0, input_tokens) * inp + max(0, output_tokens) * out) / 1_000_000.0, 8)
