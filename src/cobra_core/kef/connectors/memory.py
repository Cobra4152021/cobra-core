"""In-memory evidence connector (tests + request-seeded Computer handles)."""

from __future__ import annotations

import threading
from typing import Any

from cobra_core.kef.filters import filter_by_kinds, filter_by_metadata, filter_by_skill_types
from cobra_core.kef.types import EvidenceItem, HealthStatus, RetrievalQuery


class MemoryConnector:
    connector_id = "memory"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, EvidenceItem] = {}

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def upsert(self, item: EvidenceItem) -> None:
        with self._lock:
            self._items[item.id] = item

    def upsert_many(self, items: list[EvidenceItem]) -> None:
        with self._lock:
            for item in items:
                self._items[item.id] = item

    def health(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def lookup(self, ref_id: str) -> EvidenceItem | None:
        with self._lock:
            return self._items.get(ref_id)

    def read(self, ref_id: str) -> EvidenceItem | None:
        return self.lookup(ref_id)

    def metadata(self, ref_id: str) -> dict[str, Any] | None:
        item = self.lookup(ref_id)
        if item is None:
            return None
        return {
            "id": item.id,
            "type": item.type.value,
            "title": item.title,
            "integrity_hash": item.integrity_hash,
            "skill_evidence_type": item.skill_evidence_type,
            "metadata": dict(item.metadata),
        }

    def search(self, query: RetrievalQuery) -> list[EvidenceItem]:
        with self._lock:
            items = list(self._items.values())
        if query.ref_ids:
            wanted = set(query.ref_ids)
            items = [i for i in items if i.id in wanted or i.content_reference in wanted]
        items = filter_by_kinds(items, query.kinds)
        skill_types = query.required_skill_types | query.optional_skill_types
        if skill_types and not query.ref_ids:
            items = filter_by_skill_types(items, skill_types)
        items = filter_by_metadata(items, query.metadata_filters)
        return items[: max(1, query.max_results)]
