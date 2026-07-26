"""Normalize connector-native objects and ISF EvidenceRefs into EvidenceItem."""

from __future__ import annotations

import hashlib
from typing import Any

from cobra_core.isf.evidence import EvidenceRef
from cobra_core.kef.metadata import skill_type_to_kind
from cobra_core.kef.types import EvidenceItem, EvidenceKind, EvidencePermissions


def _hash_ref(ref_id: str, skill_type: str) -> str:
    digest = hashlib.sha256(f"{skill_type}:{ref_id}".encode()).hexdigest()
    return digest[:32]


def normalize_evidence_ref(
    ref: EvidenceRef,
    *,
    source: str = "request",
    connector_id: str = "memory",
) -> EvidenceItem:
    """Convert a Computer/ISF EvidenceRef into a KEF EvidenceItem (no body)."""
    skill_type = ref.evidence_type.value
    kind = skill_type_to_kind(skill_type)
    meta = dict(ref.metadata or {})
    integrity = str(meta.pop("content_hash", "") or meta.pop("integrity_hash", "") or "")
    if not integrity:
        integrity = _hash_ref(ref.ref_id, skill_type)
    title = str(meta.get("title") or ref.ref_id)
    summary = str(meta.get("summary") or "")
    # Never retain raw text bodies in the item.
    meta.pop("text", None)
    meta.pop("content", None)
    meta.pop("body", None)
    return EvidenceItem(
        id=ref.ref_id.strip(),
        type=kind,
        source=f"{connector_id}:{source}",
        title=title,
        summary=summary,
        content_reference=ref.ref_id.strip(),
        created_time=meta.get("created_time"),
        modified_time=meta.get("modified_time"),
        author=meta.get("author"),
        confidence=float(meta.get("confidence") or 1.0),
        integrity_hash=integrity,
        metadata=meta,
        permissions=_perms_from_meta(meta),
        retrieval_score=0.0,
        skill_evidence_type=skill_type,
        canonical_id=str(meta.get("canonical_id") or ref.ref_id.strip()),
    )


def normalize_native(
    raw: dict[str, Any],
    *,
    connector_id: str,
    default_kind: EvidenceKind = EvidenceKind.DOCUMENT,
) -> EvidenceItem:
    """Normalize a connector-native dict into EvidenceItem."""
    eid = str(raw.get("id") or raw.get("ref_id") or "").strip()
    if not eid:
        raise ValueError("native evidence missing id")
    kind_raw = str(raw.get("type") or raw.get("kind") or default_kind.value).strip().lower()
    try:
        kind = EvidenceKind(kind_raw)
    except ValueError:
        kind = default_kind
    skill_type = raw.get("skill_evidence_type") or raw.get("evidence_type")
    meta = dict(raw.get("metadata") or {})
    integrity = str(raw.get("integrity_hash") or meta.get("content_hash") or "")
    if not integrity:
        integrity = _hash_ref(eid, str(skill_type or kind.value))
    return EvidenceItem(
        id=eid,
        type=kind,
        source=str(raw.get("source") or connector_id),
        title=str(raw.get("title") or eid),
        summary=str(raw.get("summary") or ""),
        content_reference=str(raw.get("content_reference") or eid),
        created_time=raw.get("created_time"),
        modified_time=raw.get("modified_time"),
        author=raw.get("author"),
        confidence=float(raw.get("confidence") or 1.0),
        integrity_hash=integrity,
        metadata=meta,
        permissions=_perms_from_meta(
            {**meta, **{k: raw[k] for k in ("visibility", "classification", "deny") if k in raw}}
        ),
        retrieval_score=float(raw.get("retrieval_score") or 0.0),
        skill_evidence_type=str(skill_type) if skill_type else None,
        canonical_id=str(raw.get("canonical_id") or eid),
        duplicate_of=raw.get("duplicate_of"),
    )


def _perms_from_meta(meta: dict[str, Any]) -> EvidencePermissions:
    roles = meta.get("allow_roles")
    if isinstance(roles, (list, tuple, set, frozenset)):
        allow = frozenset(str(r) for r in roles)
    else:
        allow = frozenset({"owner", "admin", "investigator"})
    return EvidencePermissions(
        visibility=str(meta.get("visibility") or "org"),
        classification=str(meta.get("classification") or "internal"),
        allow_roles=allow,
        deny=bool(meta.get("deny") or False),
    )
