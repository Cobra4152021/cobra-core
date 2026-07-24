"""
Inference backends for Protocol V1.

HTTP/transport logic must not live here. Default mode is mock (no GPU).
Token counting: mock uses deterministic ceil(chars/4); local mode uses tokenizer
counts from the Qwen adapter when available.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any


def approx_tokens(text: str) -> int:
    """Deterministic approx used by mock mode and context truncation (~4 chars/token)."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


@dataclass
class InferenceResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    inference_ms: int


class InferenceCancelledError(Exception):
    """Raised when a cancel event is observed before/during mock work."""


class InferenceFailedError(Exception):
    """Safe, non-leaking inference failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def truncate_messages(
    messages: list[dict[str, Any]],
    max_context: int | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Drop oldest turns to fit approx context cap (frozen fixture behavior).

    Returns (messages, error_code) where error_code is 'context_limit' if the
    newest single message alone cannot fit.
    """
    if max_context is None or max_context <= 0:
        return messages, None

    chars = 0
    out: list[dict[str, Any]] = []
    for msg in reversed(messages):
        content = str(msg.get("content") or "")
        msg_tokens = approx_tokens(content) if content else 0
        if chars / 4 + msg_tokens > max_context and out:
            break
        chars += len(content)
        out.insert(0, msg)

    if not out:
        out = messages[-1:]

    newest = str(out[-1].get("content") or "")
    if approx_tokens(newest) > max_context:
        return out, "context_limit"
    return out, None


def mock_complete(
    messages: list[dict[str, Any]],
    max_tokens: int,
    *,
    delay_ms: int = 0,
    cancel_event: threading.Event | None = None,
    fail: bool = False,
) -> InferenceResult:
    """Deterministic mock completion — no model weights, no GPU."""
    t0 = time.perf_counter()
    if fail:
        raise InferenceFailedError("provider_error", "Inference failed")

    remaining = max(0, delay_ms) / 1000.0
    while remaining > 0:
        if cancel_event is not None and cancel_event.is_set():
            raise InferenceCancelledError()
        step = min(0.05, remaining)
        time.sleep(step)
        remaining -= step
        if time.perf_counter() - t0 > (delay_ms / 1000.0) + 0.01:
            break

    if cancel_event is not None and cancel_event.is_set():
        raise InferenceCancelledError()

    prompt = "\n".join(f"{m.get('role', '')}: {m.get('content', '')}" for m in messages)
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = str(m.get("content") or "")
            break
    body = last_user.strip() or "(empty)"
    content = f"[mock] {body}"
    max_chars = max(8, max_tokens * 4)
    if len(content) > max_chars:
        content = content[: max_chars - 3] + "..."
    elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
    return InferenceResult(
        content=content,
        prompt_tokens=approx_tokens(prompt),
        completion_tokens=approx_tokens(content),
        inference_ms=elapsed,
    )


def run_local_qwen(
    messages: list[dict[str, Any]],
    max_tokens: int,
    *,
    adapter: Any,
    artifact_dir: Any,
    manifest: Any,
) -> InferenceResult:
    """
    Call existing QwenLocalAdapter without changing weights/quantization.

    Uses official chat template + NF4 load path already validated in Core.
    """
    from cobra_core.schemas.inference import ChatMessage, InferenceRequest

    t0 = time.perf_counter()
    chat = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]
    req = InferenceRequest(
        user_prompt=chat[-1].content if chat else "",
        messages=chat,
        max_new_tokens=max_tokens,
        temperature=0.0,
    )
    result = adapter.generate_local(
        artifact_dir=artifact_dir,
        manifest=manifest,
        manifest_ref=str(getattr(manifest, "model_name", "qwen3-8b")),
        request=req,
        messages=chat,
        run_id="protocol-v1",
        environment_reference=None,
    )
    text = (getattr(result, "assistant_response", None) or result.raw_generated_text or "").strip()
    prompt_tokens = int(
        result.input_token_count
        if result.input_token_count is not None
        else approx_tokens("\n".join(m["content"] for m in messages))
    )
    completion_tokens = int(
        result.output_token_count if result.output_token_count is not None else approx_tokens(text)
    )
    elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
    return InferenceResult(
        content=text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        inference_ms=elapsed,
    )
