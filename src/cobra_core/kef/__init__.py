"""
Knowledge & Evidence Framework (KEF) — KC-027.

Single gateway for Investigation Skill evidence retrieval, validation,
normalization, ranking, and citation.
"""

from __future__ import annotations

from cobra_core.kef.config import KefConfig, kef_enabled, load_kef_config
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import (
    Citation,
    CitationProvenance,
    ContentInclusionMode,
    EvidenceItem,
    EvidenceKind,
    EvidencePermissions,
    IntegrityState,
    RetrievalMode,
    RetrievalQuery,
    RetrievalResult,
)

__all__ = [
    "Citation",
    "CitationProvenance",
    "ContentInclusionMode",
    "EvidenceItem",
    "EvidenceKind",
    "EvidencePermissions",
    "IntegrityState",
    "KefConfig",
    "KefError",
    "KefErrorCode",
    "RetrievalMode",
    "RetrievalQuery",
    "RetrievalResult",
    "kef_enabled",
    "load_kef_config",
]


def __getattr__(name: str) -> object:
    if name == "KefGateway":
        from cobra_core.kef.retrieval import KefGateway

        return KefGateway
    if name == "KEF_GATEWAY":
        from cobra_core.kef.retrieval import KEF_GATEWAY

        return KEF_GATEWAY
    if name == "KEF_AUDIT":
        from cobra_core.kef.audit import KEF_AUDIT

        return KEF_AUDIT
    if name == "KEF_METRICS":
        from cobra_core.kef.metrics import KEF_METRICS

        return KEF_METRICS
    if name == "CONNECTOR_REGISTRY":
        from cobra_core.kef.registry import CONNECTOR_REGISTRY

        return CONNECTOR_REGISTRY
    raise AttributeError(name)
