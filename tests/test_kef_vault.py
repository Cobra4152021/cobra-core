"""KC-028 Evidence Vault connector + KEF security/integrity tests."""

from __future__ import annotations

import pytest

from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.kef.citation_validate import validate_citations
from cobra_core.kef.config import KefConfig, load_kef_config
from cobra_core.kef.connectors.evidence_vault import EvidenceVaultConnector
from cobra_core.kef.connectors.memory import MemoryConnector
from cobra_core.kef.context_budget import apply_budget
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.integrity import classify_integrity, filter_integrity
from cobra_core.kef.registry import ConnectorRegistry
from cobra_core.kef.retrieval import KefGateway
from cobra_core.kef.security import Principal
from cobra_core.kef.types import EvidenceItem, EvidenceKind, IntegrityState
from cobra_core.kef.vault_http import DeterministicVaultAdapter
from cobra_core.kef.versioning import select_version


def _cfg(**overrides: object) -> KefConfig:
    base = dict(
        vault_enabled=True,
        vault_base_url="https://vault.example.test",
        vault_auth_token="staging-read-token",
        vault_require_tls=True,
        vault_allow_private_hosts=True,
        allow_request_seed=False,
        allow_unverified_integrity=False,
    )
    base.update(overrides)
    return KefConfig(**base)  # type: ignore[arg-type]


def _record(
    key: str,
    *,
    evidence_type: str = "policy_document",
    kind: str = "policy",
    sha: str = "a" * 64,
    deny: bool = False,
    integrity: str | None = None,
    version: str = "1",
    size: int = 100,
) -> dict:
    return {
        "id": f"doc-{key}",
        "manifestKey": key,
        "title": f"Title {key}",
        "sha256": sha,
        "evidenceType": evidence_type,
        "evidenceKind": kind,
        "version": version,
        "deny": deny,
        "integrityState": integrity,
        "size": size,
        "contentType": "application/pdf",
        "uploadedAt": "2026-01-01T00:00:00Z",
    }


def test_vault_lookup_success_and_provenance():
    adapter = DeterministicVaultAdapter(
        "success",
        records={"pol-1": _record("pol-1", evidence_type="policy_document", kind="policy")},
    )
    conn = EvidenceVaultConnector(config=_cfg(), transport=adapter)
    item = conn.lookup("pol-1")
    assert item is not None
    assert item.source == "evidence_vault"
    assert item.integrity_hash == "a" * 64
    assert item.metadata["vault_source_id"]
    assert item.metadata["vault_document_id"]
    assert item.skill_evidence_type == "policy_document"
    assert classify_integrity(item) == IntegrityState.VERIFIED


def test_vault_auth_failures_no_retry_exhaustion_path():
    for scenario, code in [
        ("401", KefErrorCode.VAULT_AUTH_FAILURE),
        ("403", KefErrorCode.VAULT_FORBIDDEN),
    ]:
        conn = EvidenceVaultConnector(config=_cfg(), transport=DeterministicVaultAdapter(scenario))
        with pytest.raises(KefError) as exc:
            conn.lookup("x")
        assert exc.value.code == code


def test_vault_timeout_then_success():
    class Flaky(DeterministicVaultAdapter):
        def __init__(self) -> None:
            super().__init__("success", records={"pol-1": _record("pol-1")})
            self.n = 0

        def request(self, method, path, query, headers):  # type: ignore[no-untyped-def]
            self.n += 1
            if self.n == 1:
                raise TimeoutError("first")
            return super().request(method, path, query, headers)

    conn = EvidenceVaultConnector(config=_cfg(vault_max_attempts=2), transport=Flaky())
    assert conn.lookup("pol-1") is not None


def test_vault_timeout_exhaustion():
    conn = EvidenceVaultConnector(
        config=_cfg(vault_max_attempts=2), transport=DeterministicVaultAdapter("timeout")
    )
    with pytest.raises(KefError) as exc:
        conn.lookup("x")
    assert exc.value.code == KefErrorCode.VAULT_TIMEOUT


def test_hash_mismatch_excluded():
    item = EvidenceItem(
        id="bad",
        type=EvidenceKind.POLICY,
        source="evidence_vault",
        integrity_hash="abc",
        metadata={"integrity_state": "mismatch"},
        skill_evidence_type="policy_document",
    )
    ok, rejected, mismatch = filter_integrity([item], allow_unverified=False, required_ids={"bad"})
    assert ok == []
    assert mismatch == ["bad"]
    assert rejected


def test_permission_denied_never_in_context():
    adapter = DeterministicVaultAdapter(
        "permission_denied",
        records={"secret": _record("secret", evidence_type="policy_document")},
    )
    reg = ConnectorRegistry()
    reg.register(EvidenceVaultConnector(config=_cfg(), transport=adapter))
    gw = KefGateway(registry=reg, config=_cfg())
    result = gw.retrieve_for_skill(
        skill_id="policy_compliance_review",
        required_evidence=frozenset({EvidenceType.POLICY_DOCUMENT}),
        evidence_refs=(EvidenceRef(EvidenceType.POLICY_DOCUMENT, "secret"),),
        principal=Principal(role="investigator"),
    )
    assert result.permission_denials == 1
    assert "policy_document" in result.missing_required
    assert result.items == []


def test_no_request_seed_when_disabled():
    reg = ConnectorRegistry()
    reg.register(MemoryConnector())
    gw = KefGateway(registry=reg, config=_cfg(vault_enabled=False, allow_request_seed=False))
    result = gw.retrieve_for_skill(
        skill_id="policy_compliance_review",
        required_evidence=frozenset({EvidenceType.POLICY_DOCUMENT}),
        evidence_refs=(EvidenceRef(EvidenceType.POLICY_DOCUMENT, "pol-missing"),),
    )
    assert "policy_document" in result.missing_required


def test_duplicates_collapsed():
    adapter = DeterministicVaultAdapter(
        "duplicates",
        records={"pol-1": _record("pol-1", sha="samehash" + "0" * 56)},
    )
    # Force same hash on duplicate copy
    adapter.records["pol-1"]["sha256"] = "s" * 64
    conn = EvidenceVaultConnector(config=_cfg(), transport=adapter)
    reg = ConnectorRegistry()
    reg.register(conn)
    # Seed two identical via search path
    items = conn.search(
        __import__("cobra_core.kef.types", fromlist=["RetrievalQuery"]).RetrievalQuery(
            mode=__import__(
                "cobra_core.kef.types", fromlist=["RetrievalMode"]
            ).RetrievalMode.METADATA,
            text_query="policy",
        )
    )
    from cobra_core.kef.deduplication import deduplicate

    unique, removed, _ = deduplicate(items)
    assert removed >= 1
    assert len(unique) == 1


def test_version_selection_latest():
    items = [
        EvidenceItem(
            id="v1",
            type=EvidenceKind.POLICY,
            source="evidence_vault",
            integrity_hash="1",
            metadata={
                "source_version": "1",
                "integrity_state": "verified",
                "vault_document_id": "policy-doc",
            },
        ),
        EvidenceItem(
            id="v2",
            type=EvidenceKind.POLICY,
            source="evidence_vault",
            integrity_hash="2",
            metadata={
                "source_version": "2",
                "integrity_state": "verified",
                "vault_document_id": "policy-doc",
            },
        ),
    ]
    selected = select_version(items, mode="latest")
    assert len(selected) == 1
    assert selected[0].id == "v2"


def test_context_budget_required_fails_closed():
    huge = EvidenceItem(
        id="req",
        type=EvidenceKind.DOCUMENT,
        source="evidence_vault",
        integrity_hash="h",
        summary="x" * 10_000,
        metadata={"excerpt": "y" * 50_000, "integrity_state": "verified"},
    )
    with pytest.raises(KefError) as exc:
        apply_budget([huge], _cfg(max_total_evidence_chars=100), required_ids={"req"})
    assert exc.value.code == KefErrorCode.EVIDENCE_CONTEXT_BUDGET_EXCEEDED


def test_invented_citation_rejected():
    from cobra_core.kef.types import Citation

    violations = validate_citations(
        {"summary": "see EV-999", "citations": ["EV-999"]},
        [Citation(evidence_id="real", label="EV-001")],
        set(),
        set(),
    )
    assert any(v.startswith("unknown:") for v in violations)


def test_config_requires_token_when_vault_enabled():
    with pytest.raises(ValueError):
        load_kef_config(
            env={
                "KEF_EVIDENCE_VAULT_ENABLED": "true",
                "KEF_EVIDENCE_VAULT_BASE_URL": "https://example.com",
            }
        )


def test_gateway_vault_path_with_skill_type():
    adapter = DeterministicVaultAdapter(
        "success",
        records={
            "bud-1": _record(
                "bud-1",
                evidence_type="budget_spreadsheet",
                kind="budget",
                sha="b" * 64,
            )
        },
    )
    reg = ConnectorRegistry()
    reg.register(EvidenceVaultConnector(config=_cfg(), transport=adapter))
    gw = KefGateway(registry=reg, config=_cfg())
    result = gw.retrieve_for_skill(
        skill_id="budget_analysis",
        required_evidence=frozenset({EvidenceType.BUDGET_SPREADSHEET}),
        evidence_refs=(EvidenceRef(EvidenceType.BUDGET_SPREADSHEET, "bud-1"),),
    )
    assert result.missing_required == []
    assert result.citations
    assert result.provenance
    assert result.provenance[0].vault_document_id
    assert result.connector_ids == ["evidence_vault"]
