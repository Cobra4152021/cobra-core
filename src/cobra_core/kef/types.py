"""KEF evidence model and retrieval contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceKind(StrEnum):
    """Normalized evidence kinds (storage / connector facing)."""

    POLICY = "policy"
    REPORT = "report"
    DOCUMENT = "document"
    PDF = "pdf"
    DOCX = "docx"
    SPREADSHEET = "spreadsheet"
    EMAIL = "email"
    IMAGE = "image"
    AUDIO_TRANSCRIPT = "audio_transcript"
    VIDEO_TRANSCRIPT = "video_transcript"
    TIMELINE = "timeline"
    CASE_NOTE = "case_note"
    BUDGET = "budget"
    CONTRACT = "contract"
    # Reserved / future
    DATABASE = "database"
    BODY_CAMERA = "body_camera"
    DISPATCH = "dispatch"
    GPS = "gps"


class RetrievalMode(StrEnum):
    EXACT = "exact"
    METADATA = "metadata"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    REGISTRY = "registry"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class IntegrityState(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    MISMATCH = "mismatch"
    UNAVAILABLE = "unavailable"


class ContentInclusionMode(StrEnum):
    METADATA_ONLY = "metadata_only"
    EXCERPT = "excerpt"
    CHUNKS = "chunks"


@dataclass(frozen=True)
class EvidencePermissions:
    """Access control metadata for an evidence item."""

    visibility: str = "org"
    classification: str = "internal"
    allow_roles: frozenset[str] = frozenset({"owner", "admin", "investigator"})
    deny: bool = False

    def allows(self, *, role: str, classification_ceiling: str | None = None) -> bool:
        if self.deny:
            return False
        role_key = (role or "").strip().lower() or "investigator"
        if role_key not in {r.lower() for r in self.allow_roles} and "any" not in {
            r.lower() for r in self.allow_roles
        }:
            return False
        if classification_ceiling:
            order = ("public", "internal", "confidential", "restricted")
            try:
                if order.index(self.classification.lower()) > order.index(
                    classification_ceiling.lower()
                ):
                    return False
            except ValueError:
                return False
        return True


@dataclass(frozen=True)
class EvidenceItem:
    """
    Normalized evidence object returned by KEF (no raw document body).

    Connector metadata conventions: ``vault_source_id``, ``vault_document_id``,
    ``source_version``, ``integrity_state``, ``partial``, ``truncated``, and
    ``native_score``. Content excerpts/chunks are bounded and never audited.
    """

    id: str
    type: EvidenceKind
    source: str
    title: str = ""
    summary: str = ""
    content_reference: str = ""
    created_time: str | None = None
    modified_time: str | None = None
    author: str | None = None
    confidence: float = 1.0
    integrity_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    permissions: EvidencePermissions = field(default_factory=EvidencePermissions)
    retrieval_score: float = 0.0
    # Skill-facing evidence type (ISF EvidenceType value) when known
    skill_evidence_type: str | None = None
    duplicate_of: str | None = None
    canonical_id: str | None = None

    def __post_init__(self) -> None:
        if not (self.id or "").strip():
            raise ValueError("EvidenceItem.id is required")


@dataclass(frozen=True)
class Citation:
    """Reference from a finding/conclusion to supporting evidence."""

    evidence_id: str
    label: str = ""
    skill_evidence_type: str | None = None

    def public_id(self) -> str:
        """Stable citation token (EV-xxx style when label set)."""
        if self.label:
            return self.label
        return self.evidence_id


@dataclass(frozen=True)
class CitationProvenance:
    """Non-secret source lineage retained alongside a public citation label."""

    citation_label: str
    connector_id: str
    vault_source_id: str = ""
    vault_document_id: str = ""
    source_version: str = ""
    chunk_or_excerpt_location: str = ""
    integrity_hash: str = ""
    retrieval_timestamp_ms: int = 0
    display_title: str = ""


@dataclass(frozen=True)
class RetrievalQuery:
    """Connector-facing retrieval request (never includes document bodies)."""

    mode: RetrievalMode
    skill_id: str = ""
    correlation_id: str = ""
    ref_ids: tuple[str, ...] = ()
    required_skill_types: frozenset[str] = frozenset()
    optional_skill_types: frozenset[str] = frozenset()
    kinds: frozenset[EvidenceKind] = frozenset()
    metadata_filters: dict[str, Any] = field(default_factory=dict)
    text_query: str = ""
    max_results: int = 25
    actor_role: str = "investigator"
    org_id: str = ""
    classification_ceiling: str = "confidential"


@dataclass
class RetrievalResult:
    """Outcome of a KEF retrieval for one skill execution."""

    items: list[EvidenceItem]
    citations: list[Citation]
    missing_required: list[str]
    duplicates_removed: int = 0
    permission_denials: int = 0
    connector_ids: list[str] = field(default_factory=list)
    mode: RetrievalMode = RetrievalMode.EXACT
    latency_ms: int = 0
    audit_id: str = ""
    provenance: list[CitationProvenance] = field(default_factory=list)
    integrity_counts: dict[str, int] = field(default_factory=dict)
    truncated_count: int = 0
    evidence_characters: int = 0
    estimated_tokens: int = 0
    context_budget_ok: bool = True
    denied_ids: list[str] = field(default_factory=list)
