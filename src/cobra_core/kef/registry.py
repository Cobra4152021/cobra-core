"""Connector registry — storage-neutral connector discovery."""

from __future__ import annotations

import threading

from cobra_core.kef.config import KefConfig, load_kef_config
from cobra_core.kef.connectors.base import EvidenceConnector
from cobra_core.kef.connectors.evidence_vault import EvidenceVaultConnector
from cobra_core.kef.connectors.memory import MemoryConnector
from cobra_core.kef.connectors.mock import MockConnector
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import HealthStatus


class ConnectorRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._connectors: dict[str, EvidenceConnector] = {}

    def register(self, connector: EvidenceConnector) -> None:
        cid = getattr(connector, "connector_id", "") or ""
        if not cid:
            raise KefError(KefErrorCode.INVALID_REQUEST, "connector_id required")
        with self._lock:
            self._connectors[cid] = connector

    def get(self, connector_id: str) -> EvidenceConnector:
        with self._lock:
            conn = self._connectors.get(connector_id)
        if conn is None:
            raise KefError(
                KefErrorCode.CONNECTOR_NOT_FOUND,
                f"unknown connector: {connector_id}",
            )
        return conn

    def list_ids(self) -> list[str]:
        with self._lock:
            return sorted(self._connectors.keys())

    def health_snapshot(self) -> dict[str, str]:
        out: dict[str, str] = {}
        with self._lock:
            items = list(self._connectors.items())
        for cid, conn in items:
            try:
                status = conn.health()
                out[cid] = status.value if isinstance(status, HealthStatus) else str(status)
            except Exception:
                out[cid] = HealthStatus.UNKNOWN.value
        return out

    def clear(self) -> None:
        with self._lock:
            self._connectors.clear()

    def all(self) -> list[EvidenceConnector]:
        with self._lock:
            return list(self._connectors.values())


def build_default_registry(
    *, include_mock: bool = True, config: KefConfig | None = None
) -> ConnectorRegistry:
    cfg = config or load_kef_config()
    reg = ConnectorRegistry()
    reg.register(MemoryConnector())
    if include_mock:
        reg.register(MockConnector(seed_defaults=True))
    reg.register(EvidenceVaultConnector(config=cfg))
    return reg


CONNECTOR_REGISTRY = build_default_registry()
