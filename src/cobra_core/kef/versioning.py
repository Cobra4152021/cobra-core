"""Explicit Evidence Vault version selection."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from cobra_core.kef.types import EvidenceItem

VersionMode = Literal["latest", "specific", "effective_at", "all"]


def select_version(
    items: list[EvidenceItem],
    *,
    event_date: str | None = None,
    requested_version: str | None = None,
    mode: VersionMode = "latest",
) -> list[EvidenceItem]:
    """Select one version per vault document unless an explicit ``all`` is requested."""
    if mode == "all":
        return items
    selected: dict[str, EvidenceItem] = {}
    for item in items:
        key = str(item.metadata.get("vault_document_id") or item.id)
        version = str(item.metadata.get("source_version") or "")
        if mode == "specific" and version != (requested_version or ""):
            continue
        if (
            mode == "effective_at"
            and event_date
            and str(item.metadata.get("effective_at") or "") > event_date
        ):
            continue
        prior = selected.get(key)
        if prior is None or version > str(prior.metadata.get("source_version") or ""):
            meta = dict(item.metadata)
            meta["version_selection"] = mode
            meta["version_assumption"] = "latest/current" if mode == "latest" else mode
            selected[key] = replace(item, metadata=meta)
    return list(selected.values())
