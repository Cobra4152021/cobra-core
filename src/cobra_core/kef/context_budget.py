"""Bounded provider-context evidence selection."""

from __future__ import annotations

from dataclasses import replace

from cobra_core.kef.config import KefConfig
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import EvidenceItem


def estimate_tokens(chars: int) -> int:
    return (max(0, chars) + 3) // 4


def apply_budget(
    items: list[EvidenceItem], config: KefConfig, *, required_ids: set[str] | None = None
) -> tuple[list[EvidenceItem], int, list[EvidenceItem], int, int]:
    kept: list[EvidenceItem] = []
    excluded: list[EvidenceItem] = []
    truncated = 0
    chars = 0
    required = required_ids or set()
    for item in items:
        text = str(
            item.metadata.get("excerpt") or item.metadata.get("chunks") or item.summary or ""
        )
        limited = text[: config.max_chars_per_chunk * config.max_chunks_per_item]
        size = len(limited)
        if (
            chars + size > config.max_total_evidence_chars
            or estimate_tokens(chars + size) > config.max_total_evidence_tokens
        ):
            if item.id in required:
                raise KefError(
                    KefErrorCode.EVIDENCE_CONTEXT_BUDGET_EXCEEDED,
                    "required evidence exceeds context budget",
                )
            excluded.append(item)
            continue
        if len(limited) < len(text):
            truncated += 1
            meta = dict(item.metadata)
            meta["truncated"] = True
            item = replace(item, metadata=meta)
        kept.append(item)
        chars += size
    return kept, truncated, excluded, chars, estimate_tokens(chars)
