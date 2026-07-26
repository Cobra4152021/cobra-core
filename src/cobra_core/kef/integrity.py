"""Evidence integrity gates."""

from __future__ import annotations

from cobra_core.kef.types import EvidenceItem, IntegrityState


def classify_integrity(item: EvidenceItem) -> IntegrityState:
    raw = str(item.metadata.get("integrity_state") or "").lower().strip()
    if raw == IntegrityState.MISMATCH.value:
        return IntegrityState.MISMATCH
    if raw == IntegrityState.UNAVAILABLE.value:
        return IntegrityState.UNAVAILABLE
    if raw == IntegrityState.UNVERIFIED.value:
        return IntegrityState.UNVERIFIED
    if raw == IntegrityState.VERIFIED.value:
        return IntegrityState.VERIFIED
    # No explicit state: presence of an integrity hash implies verified at source.
    if item.integrity_hash:
        return IntegrityState.VERIFIED
    return IntegrityState.UNVERIFIED


def filter_integrity(
    items: list[EvidenceItem], *, allow_unverified: bool, required_ids: set[str]
) -> tuple[list[EvidenceItem], list[EvidenceItem], list[str]]:
    kept: list[EvidenceItem] = []
    rejected: list[EvidenceItem] = []
    mismatch_ids: list[str] = []
    for item in items:
        state = classify_integrity(item)
        if state == IntegrityState.MISMATCH:
            rejected.append(item)
            mismatch_ids.append(item.id)
        elif state != IntegrityState.VERIFIED and not allow_unverified and item.id in required_ids:
            rejected.append(item)
        else:
            kept.append(item)
    return kept, rejected, mismatch_ids
