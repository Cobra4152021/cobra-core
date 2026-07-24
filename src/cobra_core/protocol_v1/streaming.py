"""Protocol V1 one-shot-backed streaming event helpers (not native SSE)."""

from __future__ import annotations

from typing import Any


def oneshot_stream_events(*, text: str, request_id: str) -> dict[str, Any]:
    """
    Build Computer-compatible stream events after a single non-streaming completion.

    Wire path remains POST /v1/chat/completions with stream=false.
    Native SSE is out of Protocol V1.
    """
    return {
        "mode": "one-shot-backed",
        "wire": {
            "method": "POST",
            "path": "/v1/chat/completions",
            "stream": False,
        },
        "events": [
            {"type": "delta", "text": text, "requestId": request_id},
            {"type": "done", "text": text, "requestId": request_id},
        ],
    }


def oneshot_stream_error(*, request_id: str, error: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "one-shot-backed",
        "wire": {
            "method": "POST",
            "path": "/v1/chat/completions",
            "stream": False,
        },
        "events": [
            {"type": "error", "requestId": request_id, "error": error},
        ],
    }
