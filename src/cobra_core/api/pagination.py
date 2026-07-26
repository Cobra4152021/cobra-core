"""Deterministic cursor pagination."""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from cobra_core.api.errors import ApiError, ApiErrorCode

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


@dataclass(frozen=True)
class Page:
    items: list[Any]
    limit: int
    cursor: str | None
    next_cursor: str | None

    def public_dict(self) -> dict[str, Any]:
        return {
            "data": self.items,
            "pagination": {
                "limit": self.limit,
                "cursor": self.cursor,
                "next_cursor": self.next_cursor,
            },
        }


def encode_cursor(offset: int) -> str:
    raw = json.dumps({"o": int(offset)}, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        pad = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + pad).decode("utf-8")
        data = json.loads(raw)
        offset = int(data["o"])
        if offset < 0:
            raise ValueError("negative")
        return offset
    except Exception as exc:  # noqa: BLE001
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message="invalid cursor",
            status=400,
        ) from exc


def parse_limit(raw: str | int | None, *, default: int = DEFAULT_LIMIT) -> int:
    if raw is None or raw == "":
        return default
    try:
        n = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message="limit must be an integer",
            status=400,
        ) from exc
    if n < 1 or n > MAX_LIMIT:
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message=f"limit must be between 1 and {MAX_LIMIT}",
            status=400,
        )
    return n


def paginate[T](
    items: Sequence[T],
    *,
    limit: int | None = None,
    cursor: str | None = None,
    serialize: Any = None,
) -> Page:
    lim = limit if limit is not None else DEFAULT_LIMIT
    offset = decode_cursor(cursor)
    slice_ = list(items[offset : offset + lim])
    next_off = offset + lim
    next_cursor = encode_cursor(next_off) if next_off < len(items) else None
    data = [serialize(x) for x in slice_] if serialize is not None else list(slice_)
    return Page(items=data, limit=lim, cursor=cursor, next_cursor=next_cursor)
