"""Inference backends for Protocol V1. Default is mock (no GPU)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def approx_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


@dataclass
class InferenceResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    inference_ms: int


def truncate_messages(
    messages: list[dict[str, Any]],
    max_context: int | None,
) -> list[dict[str, Any]]:
    if max_context is None or max_context <= 0:
        return messages
    chars = 0
    out: list[dict[str, Any]] = []
    for msg in reversed(messages):
        content = str(msg.get("content") or "")
        if (chars + len(content)) / 4 > max_context and out:
            break
        chars += len(content)
        out.insert(0, msg)
    return out if out else messages[-1:]


def mock_complete(messages: list[dict[str, Any]], max_tokens: int) -> InferenceResult:
    """Deterministic mock completion — no model weights, no GPU."""
    import time

    t0 = time.perf_counter()
    prompt = "\n".join(f"{m.get('role', '')}: {m.get('content', '')}" for m in messages)
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = str(m.get("content") or "")
            break
    body = last_user.strip() or "(empty)"
    # Keep short, evidence-style mock; respect max_tokens approx.
    content = f"[mock] {body}"
    max_chars = max(8, max_tokens * 4)
    if len(content) > max_chars:
        content = content[: max_chars - 3] + "..."
    elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
    pt = approx_tokens(prompt)
    ct = approx_tokens(content)
    return InferenceResult(
        content=content, prompt_tokens=pt, completion_tokens=ct, inference_ms=elapsed
    )


def run_inference(
    *,
    mode: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
) -> InferenceResult:
    if mode in {"mock", "echo", "test"}:
        return mock_complete(messages, max_tokens)
    # Narrow choice: unknown modes fall back to mock (no GPU surprise).
    return mock_complete(messages, max_tokens)
