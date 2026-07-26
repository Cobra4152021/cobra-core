"""Per-organization and per-API-client rate limits."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from cobra_core.api.errors import ApiError, ApiErrorCode


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset: int  # unix epoch seconds

    def headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset),
        }


class RateLimiter:
    """Fixed-window counter keyed by organization and API client."""

    def __init__(
        self,
        *,
        org_limit: int = 600,
        client_limit: int = 120,
        window_seconds: int = 60,
    ) -> None:
        self.org_limit = org_limit
        self.client_limit = client_limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._org: dict[str, tuple[int, int]] = {}  # key → (window_start, count)
        self._client: dict[str, tuple[int, int]] = {}

    def reset_for_tests(self) -> None:
        with self._lock:
            self._org.clear()
            self._client.clear()

    def _hit(
        self,
        store: dict[str, tuple[int, int]],
        key: str,
        limit: int,
        now: int,
    ) -> RateLimitResult:
        window = now - (now % self.window_seconds)
        reset = window + self.window_seconds
        start, count = store.get(key, (window, 0))
        if start != window:
            start, count = window, 0
        count += 1
        store[key] = (start, count)
        remaining = max(0, limit - count)
        return RateLimitResult(
            allowed=count <= limit,
            limit=limit,
            remaining=remaining,
            reset=reset,
        )

    def check(
        self,
        *,
        organization_id: str = "",
        api_client_id: str = "",
    ) -> RateLimitResult:
        now = int(time.time())
        with self._lock:
            org_key = organization_id.strip() or "_anonymous_org"
            client_key = api_client_id.strip() or "_anonymous_client"
            org_res = self._hit(self._org, org_key, self.org_limit, now)
            client_res = self._hit(self._client, client_key, self.client_limit, now)
        # Most restrictive remaining/reset
        allowed = org_res.allowed and client_res.allowed
        remaining = min(org_res.remaining, client_res.remaining)
        limit = min(org_res.limit, client_res.limit)
        reset = max(org_res.reset, client_res.reset)
        result = RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset=reset,
        )
        if not allowed:
            raise ApiError(
                error_code=ApiErrorCode.RATE_LIMITED,
                message="rate limit exceeded",
                status=429,
                details={"limit": limit, "reset": reset},
            )
        return result

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "org_keys": len(self._org),
                "client_keys": len(self._client),
                "org_limit": self.org_limit,
                "client_limit": self.client_limit,
                "window_seconds": self.window_seconds,
            }


RATE_LIMITER = RateLimiter()
