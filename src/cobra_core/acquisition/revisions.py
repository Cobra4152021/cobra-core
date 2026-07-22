"""Pinned revision enforcement."""

from __future__ import annotations

import re

_FLOATING = re.compile(
    r"^(main|master|latest|head|tip|current|origin/main|origin/master)$",
    re.IGNORECASE,
)
_COMMIT_LIKE = re.compile(r"^[0-9a-fA-F]{7,64}$")


class UnpinnedRevisionError(ValueError):
    """Raised when a floating or placeholder revision is requested."""


def assert_pinned_revision(revision: str) -> str:
    """Require an immutable revision pin (commit SHA preferred)."""
    cleaned = revision.strip()
    if not cleaned:
        raise UnpinnedRevisionError("revision is empty")
    if _FLOATING.match(cleaned):
        raise UnpinnedRevisionError(
            f"floating revision refused: {revision!r}; pin an exact commit SHA"
        )
    if not _COMMIT_LIKE.match(cleaned):
        raise UnpinnedRevisionError(
            f"revision must look like a git/content commit SHA, got {revision!r}"
        )
    return cleaned.lower()
