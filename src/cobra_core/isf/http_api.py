"""
Authenticated ISF HTTP handlers (staging ops).

Additive endpoints — does not alter Protocol V1 chat/completions wire.
Never returns prompts, secrets, or raw evidence bodies.
"""

from __future__ import annotations

from typing import Any

from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.isf.audit import ISF_AUDIT
from cobra_core.isf.computer_adapter import ComputerIsfAdapter
from cobra_core.isf.enabled import isf_enabled
from cobra_core.isf.engine import SkillEngine
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.metrics import ISF_METRICS
from cobra_core.isf.registry import SKILL_REGISTRY


def handle_isf_skills() -> dict[str, Any]:
    skills = []
    for sid in sorted(SKILL_REGISTRY.ids()):
        m = SKILL_REGISTRY.get(sid)
        skills.append(
            {
                "skill_id": m.id,
                "version": m.version,
                "title": m.title,
                "required_capabilities": sorted(c.value for c in m.required_capabilities),
                "required_evidence_types": sorted(e.value for e in m.required_evidence_types),
                "schema": m.schema_key,
                "minimum_confidence": m.confidence_policy.minimum_confidence,
            }
        )
    return {
        "isf_enabled": isf_enabled(),
        "count": len(skills),
        "skills": skills,
    }


def handle_isf_audit(*, limit: int = 50, correlation_id: str | None = None) -> dict[str, Any]:
    entries = ISF_AUDIT.recent(max(1, min(limit, 200)))
    if correlation_id:
        entries = [e for e in entries if e.get("correlation_id") == correlation_id]
    return {"count": len(entries), "entries": entries}


def handle_isf_metrics_json() -> dict[str, Any]:
    return ISF_METRICS.snapshot()


def handle_isf_execute(
    payload: dict[str, Any],
    *,
    config: CialConfig | None = None,
    correlation_id: str = "",
    cial_engine: CialEngine | None = None,
) -> tuple[int, dict[str, Any]]:
    """Execute a Computer skill request through ISF."""
    if not isf_enabled():
        return 503, {
            "ok": False,
            "error": {
                "code": IsfErrorCode.ISF_DISABLED.value,
                "message": "ISF_ENABLED=false; Investigation Skills Framework unavailable",
            },
        }

    cfg = config or load_cial_config()
    # Prefer injected engine; otherwise build default (mock always; openai when live).
    resolved_cial = cial_engine
    if resolved_cial is None:
        try:
            resolved_cial = CialEngine.build_default(cfg)
        except Exception:  # noqa: BLE001 — fall back to draft path if CIAL cannot boot
            resolved_cial = None
    engine = SkillEngine(config=cfg, cial_engine=resolved_cial)
    adapter = ComputerIsfAdapter(engine=engine)
    try:
        body = adapter.execute(payload, correlation_id=correlation_id)
        status = 200 if body.get("ok") else 422
        return status, body
    except IsfError as exc:
        code = exc.code.value
        http = 404 if exc.code == IsfErrorCode.SKILL_NOT_FOUND else 422
        if exc.code == IsfErrorCode.ISF_DISABLED:
            http = 503
        if exc.code == IsfErrorCode.SKILL_VERSION_UNSUPPORTED:
            http = 422
        return http, {
            "ok": False,
            "error": {"code": code, "message": exc.message},
            "correlation_id": correlation_id or payload.get("correlation_id") or None,
        }
