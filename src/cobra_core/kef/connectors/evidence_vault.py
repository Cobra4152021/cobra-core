"""Computer Evidence Vault connector."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.kef.config import KefConfig
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import (
    EvidenceItem,
    EvidenceKind,
    EvidencePermissions,
    HealthStatus,
    RetrievalQuery,
)
from cobra_core.kef.vault_http import UrllibVaultTransport, VaultHttpTransport
from cobra_core.resilience.circuit_breaker import CircuitBreaker
from cobra_core.resilience.config import ResilienceConfig


class EvidenceVaultConnector:
    """
    Narrow adapter over explicitly supported Vault read/search endpoints.
    """

    connector_id = "evidence_vault"

    def __init__(
        self,
        *,
        config: KefConfig | None = None,
        enabled: bool | None = None,
        transport: VaultHttpTransport | None = None,
    ) -> None:
        self.config = config or KefConfig(
            vault_enabled=bool(enabled),
            vault_base_url="https://invalid" if enabled else "",
            vault_auth_token="test" if enabled else "",
        )
        self.enabled = self.config.vault_enabled if enabled is None else enabled
        self.transport = transport or (
            UrllibVaultTransport(
                self.config.vault_base_url,
                timeout_ms=self.config.vault_timeout_ms,
                allow_private_hosts=self.config.vault_allow_private_hosts,
            )
            if self.enabled
            else None
        )
        self._health: tuple[float, HealthStatus] | None = None
        self._breaker = CircuitBreaker(
            "evidence_vault",
            ResilienceConfig(
                max_attempts=self.config.vault_max_attempts,
                circuit_failure_threshold=self.config.vault_circuit_failure_threshold,
                circuit_window_seconds=self.config.vault_circuit_window_seconds,
                circuit_open_seconds=self.config.vault_circuit_open_seconds,
            ),
        )

    def health(self) -> HealthStatus:
        if not self.enabled:
            return HealthStatus.UNAVAILABLE
        if (
            self._health
            and time.monotonic() - self._health[0] < self.config.vault_health_ttl_seconds
        ):
            return self._health[1]
        try:
            if self.transport is None:
                result = HealthStatus.UNAVAILABLE
            else:
                headers = {"X-Hidden-Grid-Key": self.config.vault_auth_token}
                status, _ = self.transport.request("GET", "/api/r2-health", None, headers)
                result = HealthStatus.HEALTHY if 200 <= status < 300 else HealthStatus.DEGRADED
        except Exception:
            result = HealthStatus.UNAVAILABLE
        self._health = (time.monotonic(), result)
        return result

    def lookup(self, ref_id: str) -> EvidenceItem | None:
        status, body = self._request("GET", "/api/file", {"manifestKey": ref_id})
        if status == 404:
            return None
        self._raise_status(status)
        return self._map_record(_record(body))

    def read(self, ref_id: str) -> EvidenceItem | None:
        return self.lookup(ref_id)

    def metadata(self, ref_id: str) -> dict[str, Any] | None:
        item = self.lookup(ref_id)
        return dict(item.metadata) if item else None

    def search(self, query: RetrievalQuery) -> list[EvidenceItem]:
        route = "/api/evidence-search" if query.metadata_filters.get("case_id") else "/api/search"
        params = {"q": query.text_query, "caseId": str(query.metadata_filters.get("case_id") or "")}
        status, body = self._request("GET", route, params, org_id=query.org_id)
        self._raise_status(status)
        if not isinstance(body, dict):
            raise KefError(KefErrorCode.RETRIEVAL_FAILED, "invalid Evidence Vault response")
        records = body.get("files") or body.get("results") or []
        if not isinstance(records, list):
            lanes = body.get("lanes") if isinstance(body.get("lanes"), dict) else {}
            records = []
            for lane_key in ("files", "extracts"):
                lane_items = lanes.get(lane_key) if isinstance(lanes, dict) else None
                if isinstance(lane_items, list):
                    records.extend([x for x in lane_items if isinstance(x, dict)])
        if not isinstance(records, list):
            raise KefError(KefErrorCode.RETRIEVAL_FAILED, "invalid Evidence Vault response")
        mapped: list[EvidenceItem] = []
        for item in records[: self.config.vault_max_results]:
            if not isinstance(item, dict):
                continue
            # evidence-search hits often nest FileRecord under "file" or use manifestKey directly
            record = item.get("file") if isinstance(item.get("file"), dict) else item
            if isinstance(record, dict):
                mapped.append(self._map_record(record))
        return mapped

    def _request(
        self, method: str, path: str, query: dict[str, str] | None, *, org_id: str = ""
    ) -> tuple[int, dict[str, Any] | str]:
        if not self.enabled or self.transport is None:
            raise KefError(KefErrorCode.CONNECTOR_UNAVAILABLE, "Evidence Vault is not configured")
        allowed, _ = self._breaker.allow_request()
        if not allowed:
            raise KefError(
                KefErrorCode.CONNECTOR_UNAVAILABLE, "Evidence Vault temporarily unavailable"
            )
        headers = {"X-Hidden-Grid-Key": self.config.vault_auth_token}
        if org_id:
            headers["X-Cobra-Org-Id"] = org_id
        for attempt in range(self.config.vault_max_attempts):
            try:
                status, body = self.transport.request(method, path, query, headers)
            except TimeoutError:
                if attempt + 1 < self.config.vault_max_attempts:
                    continue
                self._breaker.record_failure()
                raise KefError(KefErrorCode.VAULT_TIMEOUT, "Evidence Vault timed out") from None
            if status in {429, 500} and attempt + 1 < self.config.vault_max_attempts:
                continue
            if status >= 500 or status == 429:
                self._breaker.record_failure()
            elif 200 <= status < 300:
                self._breaker.record_success()
            return status, body
        raise KefError(KefErrorCode.RETRIEVAL_FAILED, "Evidence Vault retrieval failed")

    def _raise_status(self, status: int) -> None:
        if 200 <= status < 300:
            return
        codes = {
            401: KefErrorCode.VAULT_AUTH_FAILURE,
            403: KefErrorCode.VAULT_FORBIDDEN,
            429: KefErrorCode.VAULT_RATE_LIMITED,
        }
        raise KefError(
            codes.get(status, KefErrorCode.CONNECTOR_UNAVAILABLE), "Evidence Vault unavailable"
        )

    def _map_record(self, record: dict[str, Any]) -> EvidenceItem:
        key = str(record.get("manifestKey") or record.get("id") or "").strip()
        if not key:
            raise KefError(
                KefErrorCode.RETRIEVAL_FAILED, "Evidence Vault record missing manifest key"
            )
        metadata = dict(record.get("metadata") or {})
        integrity_hash = str(record.get("sha256") or record.get("integrity_hash") or "")
        explicit_state = str(
            record.get("integrityState") or metadata.get("integrity_state") or ""
        ).lower()
        if explicit_state not in {"verified", "unverified", "mismatch", "unavailable"}:
            explicit_state = "verified" if integrity_hash else "unverified"
        metadata.update(
            {
                "vault_source_id": str(
                    record.get("sourceId") or metadata.get("vault_source_id") or key
                ),
                "vault_document_id": str(record.get("documentId") or record.get("id") or key),
                "source_version": str(
                    record.get("version") or metadata.get("source_version") or "1"
                ),
                "integrity_state": explicit_state,
                "partial": bool(record.get("partial", False)),
                "truncated": bool(record.get("truncated", False)),
                "native_score": record.get("score", 0.0),
                "retrieval_timestamp_ms": int(time.time() * 1000),
                "connector_id": self.connector_id,
            }
        )
        if int(record.get("size") or 0) > self.config.max_item_size_bytes:
            metadata["partial"] = True
            metadata["truncated"] = True
        kind_value = (
            record.get("evidenceKind") or record.get("evidenceType") or record.get("classification")
        )
        try:
            kind = (
                EvidenceKind(str(kind_value).lower())
                if kind_value
                else _kind_from_content_type(str(record.get("contentType") or ""))
            )
        except ValueError:
            kind = _kind_from_content_type(str(record.get("contentType") or ""))
        # Prefer explicit skill/evidence type from Vault metadata; never invent
        # policy/contract/budget solely from filename.
        skill_type = (
            str(
                record.get("evidenceType")
                or metadata.get("evidenceType")
                or metadata.get("skill_evidence_type")
                or ""
            )
            .strip()
            .lower()
            or None
        )
        return EvidenceItem(
            id=key,
            type=kind,
            source=self.connector_id,
            title=str(
                record.get("title") or record.get("filename") or record.get("sourceTitle") or key
            ),
            summary=str(record.get("summary") or "")[: self.config.max_chars_per_chunk],
            content_reference=key,
            created_time=record.get("uploadedAt") or record.get("created_time"),
            modified_time=record.get("parsedAt") or record.get("modified_time"),
            author=record.get("author"),
            integrity_hash=integrity_hash,
            metadata=metadata,
            permissions=EvidencePermissions(
                deny=bool(
                    record.get("deny", False)
                    or str(record.get("status") or "").lower() == "quarantined"
                ),
                classification=str(metadata.get("classification") or "internal"),
                visibility=str(metadata.get("visibility") or "org"),
            ),
            retrieval_score=float(record.get("score") or 0.0),
            skill_evidence_type=skill_type,
            canonical_id=str(metadata.get("canonical_id") or key),
            duplicate_of=record.get("duplicateOf") or metadata.get("duplicate_of"),
        )


def _record(body: dict[str, Any] | str) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise KefError(KefErrorCode.RETRIEVAL_FAILED, "invalid Evidence Vault response")
    record = body.get("file") or body
    if not isinstance(record, dict):
        raise KefError(KefErrorCode.RETRIEVAL_FAILED, "invalid Evidence Vault response")
    return record


def _kind_from_content_type(content_type: str) -> EvidenceKind:
    value = content_type.lower()
    if "pdf" in value:
        return EvidenceKind.PDF
    if "word" in value or "officedocument.wordprocessingml" in value:
        return EvidenceKind.DOCX
    if "spreadsheet" in value or "excel" in value:
        return EvidenceKind.SPREADSHEET
    if value.startswith("image/"):
        return EvidenceKind.IMAGE
    return EvidenceKind.DOCUMENT
