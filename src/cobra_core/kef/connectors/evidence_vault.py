"""Evidence Vault connector — adapter stub only (no production integration)."""

from __future__ import annotations

from typing import Any

from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import EvidenceItem, HealthStatus, RetrievalQuery


class EvidenceVaultConnector:
    """
    Stub for a future Evidence Vault integration.

    All retrieval methods fail closed with CONNECTOR_UNAVAILABLE / NOT_IMPLEMENTED.
    """

    connector_id = "evidence_vault"

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    def health(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE if not self.enabled else HealthStatus.UNKNOWN

    def lookup(self, ref_id: str) -> EvidenceItem | None:
        self._reject(ref_id)
        return None

    def read(self, ref_id: str) -> EvidenceItem | None:
        self._reject(ref_id)
        return None

    def metadata(self, ref_id: str) -> dict[str, Any] | None:
        self._reject(ref_id)
        return None

    def search(self, query: RetrievalQuery) -> list[EvidenceItem]:
        raise KefError(
            KefErrorCode.NOT_IMPLEMENTED,
            "EvidenceVaultConnector is a stub; production vault integration is out of scope",
        )

    def _reject(self, ref_id: str) -> None:
        _ = ref_id
        raise KefError(
            KefErrorCode.CONNECTOR_UNAVAILABLE,
            "Evidence Vault connector is not configured for KC-027",
        )
