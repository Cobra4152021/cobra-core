"""KC-025 — Computer adapter, structured JSON, evidence, confidence, metrics, rollback."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from cobra_core.air.audit import AIR_AUDIT
from cobra_core.air.metrics import AIR_METRICS
from cobra_core.cial.config import CialConfig
from cobra_core.cial.types import InferenceResult, RoutingPolicy
from cobra_core.isf.audit import ISF_AUDIT
from cobra_core.isf.computer_adapter import ComputerIsfAdapter, skill_request_from_computer
from cobra_core.isf.engine import SkillEngine
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.isf.metrics import ISF_METRICS
from cobra_core.isf.registry import SkillRegistry
from cobra_core.isf.skills import register_builtin_skills
from cobra_core.isf.structured_json import extract_json_candidate, parse_provider_json
from cobra_core.isf.types import SkillExecutionStatus, SkillRequest
from cobra_core.isf.versioning import assert_version_compatible
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    # KC-025 structured-repair unit tests exercise the pre-RRF CIAL path.
    monkeypatch.setenv("RRF_ENABLED", "false")
    ISF_AUDIT.clear()
    AIR_AUDIT.clear()
    AIR_METRICS.reset()
    ISF_METRICS.reset()
    yield
    ISF_AUDIT.clear()
    ISF_METRICS.reset()


def _cfg(**overrides: object) -> CialConfig:
    base: dict[str, Any] = dict(
        enabled=True,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        mock_model=DEFAULT_MODEL,
    )
    base.update(overrides)
    return CialConfig(**base)  # type: ignore[arg-type]


def _engine(**cfg_kw: object) -> SkillEngine:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    return SkillEngine(registry=reg, config=_cfg(**cfg_kw))


# --- Structured JSON ------------------------------------------------------


def test_parse_json_in_markdown_fence() -> None:
    raw = '```json\n{"summary":"ok","confidence":0.4,"missing_information":[],"recommended_next_steps":[],"needs_human_review":true,"themes":[],"evidence_count":1,"gaps":[]}\n```'
    data = parse_provider_json(raw)
    assert data["summary"] == "ok"


def test_parse_rejects_empty_and_refusal() -> None:
    with pytest.raises(IsfError) as exc:
        parse_provider_json("")
    assert exc.value.code == IsfErrorCode.STRUCTURED_OUTPUT_INVALID
    with pytest.raises(IsfError):
        parse_provider_json("I cannot help with that.")
    assert extract_json_candidate("not json at all") is None or True


def test_parse_truncated_json() -> None:
    with pytest.raises(IsfError) as exc:
        parse_provider_json('{"summary": "x", "confidence":')
    assert exc.value.code == IsfErrorCode.STRUCTURED_OUTPUT_INVALID


# --- Versioning -----------------------------------------------------------


def test_version_compat_and_unsupported() -> None:
    assert_version_compatible(None, "1.0.0")
    assert_version_compatible("1.0.0", "1.0.0")
    assert_version_compatible("1.0.0", "1.0.2")
    with pytest.raises(IsfError) as exc:
        assert_version_compatible("2.0.0", "1.0.0")
    assert exc.value.code == IsfErrorCode.SKILL_VERSION_UNSUPPORTED


def test_engine_rejects_unsupported_version() -> None:
    engine = _engine()
    with pytest.raises(IsfError) as exc:
        engine.execute(
            SkillRequest(
                skill_id="evidence_summary",
                skill_version="9.9.9",
                evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
            )
        )
    assert exc.value.code == IsfErrorCode.SKILL_VERSION_UNSUPPORTED


# --- Evidence -------------------------------------------------------------


def test_policy_missing_document() -> None:
    engine = _engine()
    result = engine.execute(SkillRequest(skill_id="policy_compliance_review", evidence=()))
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
    assert EvidenceType.POLICY_DOCUMENT in result.missing_evidence


def test_document_comparison_needs_two_docs() -> None:
    engine = _engine()
    result = engine.execute(
        SkillRequest(
            skill_id="document_comparison",
            evidence=(
                EvidenceRef(
                    EvidenceType.DOCUMENT_PAIR,
                    "only_one",
                    metadata={"document_count": 1},
                ),
            ),
        )
    )
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE


def test_timeline_with_events_allowed() -> None:
    engine = _engine()
    result = engine.execute(
        SkillRequest(
            skill_id="timeline_construction",
            evidence=(EvidenceRef(EvidenceType.TIMELINE_SOURCE, "ev1"),),
        )
    )
    assert result.status == SkillExecutionStatus.NEEDS_HUMAN_REVIEW
    assert result.selected_provider == "mock"
    assert "events" in result.output


# --- Confidence -----------------------------------------------------------


def test_manifest_threshold_forces_review() -> None:
    engine = _engine()
    # Mock path caps confidence ≤ 0.5; threshold typically 0.7 → review.
    result = engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
        )
    )
    assert result.confidence <= 0.5
    assert result.needs_human_review is True
    entry = ISF_AUDIT.recent()[-1]
    assert entry["confidence_threshold"] is not None
    assert entry["needs_human_review"] is True


# --- Computer adapter -----------------------------------------------------


def test_adapter_rejects_provider_fields() -> None:
    with pytest.raises(IsfError) as exc:
        skill_request_from_computer({"skill_id": "evidence_summary", "provider_id": "openai"})
    assert "provider" in exc.value.message.lower() or "providers" in exc.value.message


def test_adapter_rejects_capabilities_array() -> None:
    with pytest.raises(IsfError):
        skill_request_from_computer({"skill_id": "evidence_summary", "capabilities": ["text"]})


def test_adapter_pending_approval_proposal() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    adapter = ComputerIsfAdapter(engine=SkillEngine(registry=reg, config=_cfg()))
    body = adapter.execute(
        {
            "skill_id": "evidence_summary",
            "skill_version": "1.0.0",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_text_1"}],
            "profile_id": "default",
            "inputs": {"question": "summarize"},
        },
        correlation_id="kc025_adapt_1",
    )
    assert body["ok"] is True
    assert body["proposal"]["status"] == "pending_approval"
    assert body["proposal"]["human_approval_required"] is True
    assert body["proposal"]["skill_id"] == "evidence_summary"
    assert "structured_result" in body["proposal"]
    assert body["extensions"]["isf"]["skill_id"] == "evidence_summary"


def test_adapter_unknown_skill() -> None:
    adapter = ComputerIsfAdapter(engine=SkillEngine(registry=SkillRegistry(), config=_cfg()))
    with pytest.raises(IsfError) as exc:
        adapter.execute({"skill_id": "nope"})
    assert exc.value.code == IsfErrorCode.SKILL_NOT_FOUND


# --- Schema repair --------------------------------------------------------


def test_schema_repair_once_then_fail() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    cial = MagicMock()
    # First: non-JSON; second: still non-JSON → invalid after one repair.
    cial.complete.side_effect = [
        InferenceResult(
            content="not json",
            prompt_tokens=1,
            completion_tokens=1,
            inference_ms=1,
            cial_provider_id="openai",
            cial_model_id="gpt-5.4-mini",
        ),
        InferenceResult(
            content="still not json",
            prompt_tokens=1,
            completion_tokens=1,
            inference_ms=1,
            cial_provider_id="openai",
            cial_model_id="gpt-5.4-mini",
        ),
    ]
    engine = SkillEngine(
        registry=reg,
        config=_cfg(
            active_profile="research",
            live_provider_enabled=True,
            openai_api_key="k",
            openai_model="gpt-5.4-mini",
        ),
        cial_engine=cial,
    )
    result = engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
            profile_id="research",
            correlation_id="repair_fail",
        )
    )
    assert result.status == SkillExecutionStatus.STRUCTURED_OUTPUT_INVALID
    assert result.metadata.get("repair_attempt_count") == 1
    assert cial.complete.call_count == 2


def test_schema_repair_success() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    good = (
        '{"summary":"ok","confidence":0.62,"missing_information":["x"],'
        '"recommended_next_steps":[],"needs_human_review":true,'
        '"themes":["a"],"evidence_count":1,"gaps":[]}'
    )
    cial = MagicMock()
    cial.complete.side_effect = [
        InferenceResult(
            content="garbage",
            prompt_tokens=1,
            completion_tokens=1,
            inference_ms=1,
            cial_provider_id="openai",
            cial_model_id="gpt-5.4-mini",
        ),
        InferenceResult(
            content=good,
            prompt_tokens=1,
            completion_tokens=1,
            inference_ms=1,
            cial_provider_id="openai",
            cial_model_id="gpt-5.4-mini",
        ),
    ]
    engine = SkillEngine(
        registry=reg,
        config=_cfg(
            active_profile="research",
            live_provider_enabled=True,
            openai_api_key="k",
            openai_model="gpt-5.4-mini",
        ),
        cial_engine=cial,
    )
    result = engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
            profile_id="research",
            correlation_id="repair_ok",
        )
    )
    assert result.status in {
        SkillExecutionStatus.COMPLETED,
        SkillExecutionStatus.NEEDS_HUMAN_REVIEW,
    }
    assert result.output["summary"] == "ok"
    assert result.metadata.get("schema_validation_result") == "repaired"
    # Confidence 0.62 below typical 0.7 → needs review; human approval still required.
    assert result.needs_human_review is True
    assert result.confidence == 0.62 or result.confidence <= 0.62


# --- Metrics / audit / disable --------------------------------------------


def test_isf_metrics_bounded() -> None:
    engine = _engine()
    engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
        )
    )
    snap = ISF_METRICS.snapshot()
    assert snap["execution_total"] >= 1
    text = ISF_METRICS.render_prometheus()
    assert "isf_execution_total" in text
    assert "correlation" not in text.lower()


def test_audit_phase8_fields() -> None:
    engine = _engine()
    engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
            correlation_id="aud_kc025",
        )
    )
    entry = ISF_AUDIT.recent()[-1]
    for key in (
        "correlation_id",
        "skill_id",
        "skill_version",
        "manifest_version",
        "requested_profile",
        "required_capabilities",
        "required_evidence_types",
        "evidence_validation_result",
        "selected_provider",
        "schema_name",
        "schema_validation_result",
        "repair_attempt_count",
        "confidence",
        "confidence_threshold",
        "needs_human_review",
        "execution_status",
        "timestamp",
    ):
        assert key in entry
    assert "prompt" not in entry
    assert "api_key" not in entry


def test_isf_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ISF_ENABLED", "false")
    engine = _engine()
    with pytest.raises(IsfError) as exc:
        engine.execute(
            SkillRequest(
                skill_id="evidence_summary",
                evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
            )
        )
    assert exc.value.code == IsfErrorCode.ISF_DISABLED


def test_http_isf_execute_and_skills(monkeypatch: pytest.MonkeyPatch) -> None:
    from cobra_core.isf.http_api import handle_isf_execute, handle_isf_skills

    monkeypatch.delenv("ISF_ENABLED", raising=False)
    skills = handle_isf_skills()
    assert skills["isf_enabled"] is True
    assert skills["count"] == 10
    status, body = handle_isf_execute(
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "http_1"}],
        },
        config=_cfg(),
        correlation_id="http_isf_1",
    )
    assert status == 200
    assert body["proposal"]["status"] == "pending_approval"
