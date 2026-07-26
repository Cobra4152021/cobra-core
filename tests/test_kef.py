"""KC-027 Knowledge & Evidence Framework tests."""

from __future__ import annotations

import os

import pytest

from cobra_core.isf.engine import SkillEngine
from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.isf.registry import SkillRegistry
from cobra_core.isf.skills import register_builtin_skills
from cobra_core.isf.types import SkillExecutionStatus, SkillRequest
from cobra_core.kef.audit import KEF_AUDIT
from cobra_core.kef.citation import assign_citation_labels, attach_citations_to_output
from cobra_core.kef.config import load_kef_config
from cobra_core.kef.connectors.evidence_vault import EvidenceVaultConnector
from cobra_core.kef.connectors.memory import MemoryConnector
from cobra_core.kef.connectors.mock import MockConnector
from cobra_core.kef.deduplication import deduplicate
from cobra_core.kef.metrics import KEF_METRICS
from cobra_core.kef.normalizer import normalize_evidence_ref, normalize_native
from cobra_core.kef.ranking import rank_items
from cobra_core.kef.registry import ConnectorRegistry, build_default_registry
from cobra_core.kef.retrieval import KefGateway
from cobra_core.kef.security import Principal
from cobra_core.kef.types import (
    EvidenceItem,
    EvidenceKind,
    EvidencePermissions,
    RetrievalMode,
    RetrievalQuery,
)


@pytest.fixture(autouse=True)
def _kef_clean():
    KEF_AUDIT.clear()
    KEF_METRICS.clear()
    yield
    KEF_AUDIT.clear()
    KEF_METRICS.clear()


def _registry() -> SkillRegistry:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    return reg


def test_connector_registry_defaults():
    reg = build_default_registry()
    ids = reg.list_ids()
    assert "memory" in ids
    assert "mock" in ids
    assert "evidence_vault" in ids
    health = reg.health_snapshot()
    assert health["memory"] == "healthy"
    assert health["evidence_vault"] == "unavailable"


def test_normalization_from_evidence_ref():
    ref = EvidenceRef(EvidenceType.POLICY_DOCUMENT, "pol-1", {"title": "Policy A"})
    item = normalize_evidence_ref(ref)
    assert item.id == "pol-1"
    assert item.type == EvidenceKind.POLICY
    assert item.skill_evidence_type == "policy_document"
    assert item.integrity_hash
    assert "text" not in item.metadata


def test_deduplication_by_hash():
    a = EvidenceItem(
        id="a",
        type=EvidenceKind.POLICY,
        source="memory",
        integrity_hash="samehash",
        confidence=0.5,
        skill_evidence_type="policy_document",
    )
    b = EvidenceItem(
        id="b",
        type=EvidenceKind.POLICY,
        source="memory",
        integrity_hash="samehash",
        confidence=0.9,
        skill_evidence_type="policy_document",
    )
    unique, removed, rels = deduplicate([a, b])
    assert removed == 1
    assert len(unique) == 1
    assert unique[0].id == "b"
    assert "a" in (rels.get("b") or [])


def test_ranking_explicit_match_wins():
    items = [
        EvidenceItem(id="other", type=EvidenceKind.DOCUMENT, source="m", integrity_hash="1"),
        EvidenceItem(id="wanted", type=EvidenceKind.POLICY, source="m", integrity_hash="2"),
    ]
    q = RetrievalQuery(mode=RetrievalMode.EXACT, ref_ids=("wanted",))
    ranked = rank_items(items, q)
    assert ranked[0].id == "wanted"
    assert ranked[0].retrieval_score > ranked[1].retrieval_score


def test_citation_generation():
    items = [
        EvidenceItem(id="x", type=EvidenceKind.IMAGE, source="m", integrity_hash="h1"),
        EvidenceItem(id="y", type=EvidenceKind.IMAGE, source="m", integrity_hash="h2"),
    ]
    cites = assign_citation_labels(items)
    assert [c.public_id() for c in cites] == ["EV-001", "EV-002"]
    out = attach_citations_to_output({"summary": "ok", "findings": ["f1"]}, cites)
    assert out["citations"] == ["EV-001", "EV-002"]


def test_permission_filtering():
    reg = ConnectorRegistry()
    mem = MemoryConnector()
    denied = EvidenceItem(
        id="secret",
        type=EvidenceKind.POLICY,
        source="memory",
        integrity_hash="z" * 32,
        skill_evidence_type="policy_document",
        permissions=EvidencePermissions(deny=True),
    )
    mem.upsert(denied)
    reg.register(mem)
    gw = KefGateway(registry=reg)
    result = gw.retrieve_for_skill(
        skill_id="policy_compliance_review",
        required_evidence=frozenset({EvidenceType.POLICY_DOCUMENT}),
        evidence_refs=(EvidenceRef(EvidenceType.POLICY_DOCUMENT, "secret"),),
        principal=Principal(role="investigator"),
    )
    assert result.permission_denials == 1
    assert "policy_document" in result.missing_required


def test_missing_required_evidence_before_air():
    engine = SkillEngine(registry=_registry(), cial_engine=None)
    # Force mock path: no cial, but need AIR to not be reached — missing evidence returns early
    result = engine.execute(
        SkillRequest(
            skill_id="vehicle_damage_assessment",
            evidence=(),
            correlation_id="kef-miss-1",
        )
    )
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
    assert EvidenceType.VEHICLE_PHOTOS in result.missing_evidence
    assert result.metadata.get("kef_enabled") is True
    assert KEF_METRICS.snapshot()["missing_required_evidence_total"] >= 1


def test_skill_success_includes_citations():
    os.environ["CIAL_LIVE_PROVIDER_ENABLED"] = "false"
    engine = SkillEngine(registry=_registry(), cial_engine=None)
    result = engine.execute(
        SkillRequest(
            skill_id="policy_compliance_review",
            evidence=(EvidenceRef(EvidenceType.POLICY_DOCUMENT, "pol-ok"),),
            correlation_id="kef-cite-1",
            profile_id="default",
        )
    )
    assert result.status in {
        SkillExecutionStatus.COMPLETED,
        SkillExecutionStatus.NEEDS_HUMAN_REVIEW,
    }
    assert result.output.get("citations")
    assert result.output["citations"][0].startswith("EV-")
    assert result.needs_human_review is True


def test_budget_and_policy_skills_cite():
    engine = SkillEngine(registry=_registry(), cial_engine=None)
    for skill, etype, rid in [
        ("budget_analysis", EvidenceType.BUDGET_SPREADSHEET, "bud-1"),
        ("policy_compliance_review", EvidenceType.POLICY_DOCUMENT, "pol-2"),
    ]:
        result = engine.execute(SkillRequest(skill_id=skill, evidence=(EvidenceRef(etype, rid),)))
        assert result.status != SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
        assert result.output.get("citations")


def test_vehicle_photos_pass_kef_before_air_capability_gate():
    """Vision skill clears KEF; AIR may still fail closed without a vision route."""
    reg = ConnectorRegistry()
    reg.register(MemoryConnector())
    gw = KefGateway(registry=reg)
    result = gw.retrieve_for_skill(
        skill_id="vehicle_damage_assessment",
        required_evidence=frozenset({EvidenceType.VEHICLE_PHOTOS}),
        evidence_refs=(EvidenceRef(EvidenceType.VEHICLE_PHOTOS, "photo-1"),),
    )
    assert result.missing_required == []
    assert result.citations
    assert result.citations[0].public_id() == "EV-001"


def test_mock_connector_fixtures():
    mock = MockConnector(seed_defaults=True)
    item = mock.lookup("mock-policy-001")
    assert item is not None
    assert item.type == EvidenceKind.POLICY


def test_evidence_vault_stub_fails_closed():
    vault = EvidenceVaultConnector(enabled=False)
    with pytest.raises(Exception) as exc:
        vault.search(RetrievalQuery(mode=RetrievalMode.EXACT, skill_id="policy_compliance_review"))
    assert "stub" in str(exc.value).lower() or "not" in str(exc.value).lower()


def test_audit_has_no_document_bodies():
    reg = ConnectorRegistry()
    reg.register(MemoryConnector())
    gw = KefGateway(registry=reg, audit=KEF_AUDIT)
    gw.retrieve_for_skill(
        skill_id="evidence_summary",
        required_evidence=frozenset({EvidenceType.EVIDENCE_BUNDLE}),
        evidence_refs=(
            EvidenceRef(
                EvidenceType.EVIDENCE_BUNDLE,
                "bundle-1",
                {"text": "SECRET_BODY_SHOULD_NOT_APPEAR"},
            ),
        ),
    )
    entries = KEF_AUDIT.recent(5)
    assert entries
    blob = str(entries[-1])
    assert "SECRET_BODY" not in blob
    assert "returned_count" in entries[-1]


def test_metrics_bounded_labels():
    snap = KEF_METRICS.snapshot()
    text = KEF_METRICS.render_prometheus()
    assert "kef_retrieval_total" in text
    for label in ("correlation_id", "execution_id", "user_id", "case_id"):
        assert f'{label}="' not in text
    assert "average_retrieval_ms" in snap


def test_kef_disabled_restores_isf_gap_check(monkeypatch):
    monkeypatch.setenv("KEF_ENABLED", "false")
    # reload path uses kef_enabled() which reads env
    from cobra_core.kef import config as kef_config

    assert kef_config.kef_enabled() is False
    engine = SkillEngine(registry=_registry(), cial_engine=None)
    result = engine.execute(SkillRequest(skill_id="budget_analysis", evidence=()))
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
    assert result.metadata.get("kef_enabled") is False


def test_config_rejects_semantic():
    with pytest.raises(ValueError):
        load_kef_config(env={"KEF_SEMANTIC_ENABLED": "true"})


def test_native_normalize_strips_body():
    item = normalize_native(
        {
            "id": "n1",
            "type": "document",
            "title": "Doc",
            "metadata": {"text": "nope"},
            "content": "BODY",
        },
        connector_id="memory",
    )
    assert item.id == "n1"
    # body fields are not copied onto EvidenceItem content fields as readable body
    assert item.summary == ""
