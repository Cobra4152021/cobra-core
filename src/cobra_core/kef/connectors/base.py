"""Evidence connector abstraction."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cobra_core.kef.types import EvidenceItem, HealthStatus, RetrievalQuery


@runtime_checkable
class EvidenceConnector(Protocol):
    """Storage-neutral connector interface."""

    connector_id: str

    def health(self) -> HealthStatus: ...

    def lookup(self, ref_id: str) -> EvidenceItem | None: ...

    def read(self, ref_id: str) -> EvidenceItem | None: ...

    def metadata(self, ref_id: str) -> dict[str, Any] | None: ...

    def search(self, query: RetrievalQuery) -> list[EvidenceItem]: ...
