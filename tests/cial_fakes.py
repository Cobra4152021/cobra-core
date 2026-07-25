"""Shared fakes for CIAL unit tests (no network)."""

from __future__ import annotations

import json
from typing import Any

from cobra_core.cial.providers.http_transport import HttpResponse


class FakeTransport:
    """Scripted HTTP responses for deterministic provider tests."""

    def __init__(self, script: list[HttpResponse | Exception] | None = None) -> None:
        self.script = list(script or [])
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "has_auth": "Authorization" in headers,
                "auth_redacted": headers.get("Authorization", "").startswith("Bearer "),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self.script:
            raise AssertionError("FakeTransport script exhausted")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def completion_body(content: str = "hello", *, prompt: int = 3, completion: int = 2) -> bytes:
    payload = {
        "id": "chatcmpl-test",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
    }
    return json.dumps(payload).encode("utf-8")
