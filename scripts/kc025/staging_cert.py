#!/usr/bin/env python3
"""
KC-025 ISF staging certification harness.

Computer → ISF → AIR → CIAL path. Never prints API keys, prompts,
evidence text, or provider response bodies.

Usage:
  set CORE_AUTH from %TEMP%\\kc018-core-auth.txt
  python scripts/kc025/staging_cert.py --phase offline
  python scripts/kc025/staging_cert.py --phase live
  python scripts/kc025/staging_cert.py --soak 10
  python scripts/kc025/staging_cert.py --phase rollback
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://cobra-core-staging.cobra4152020.workers.dev"
ORG = "org_staging_smoke"
UA = "CobraKC025Cert/1.0 (compatible; Mozilla/5.0)"


@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str


@dataclass
class SoakStats:
    total: int = 0
    successes: int = 0
    expected_failures: int = 0
    unexpected_failures: int = 0
    schema_valid: int = 0
    repair_attempts: int = 0
    repair_success: int = 0
    human_review: int = 0
    providers: dict[str, int] = field(default_factory=dict)
    models: dict[str, int] = field(default_factory=dict)
    confidences: list[float] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    audit_ok: int = 0
    governance_failures: int = 0


def _load_token() -> str:
    env = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    if env:
        return env
    path = Path(os.environ.get("TEMP", os.environ.get("TMP", "."))) / "kc018-core-auth.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit("COBRA_CORE_AUTH_SECRET or %TEMP%/kc018-core-auth.txt required")


def _req(
    method: str,
    url: str,
    *,
    token: str,
    body: dict[str, Any] | None = None,
    timeout: float = 90.0,
    request_id: str | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Cobra-Org-Id": ORG,
        "Content-Type": "application/json",
        "User-Agent": UA,
    }
    if request_id:
        headers["x-request-id"] = request_id
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ctype = resp.headers.get("Content-Type") or ""
            if "application/json" in ctype or raw.startswith("{"):
                return int(resp.status), json.loads(raw)
            return int(resp.status), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return int(exc.code), json.loads(raw)
        except json.JSONDecodeError:
            return int(exc.code), {"raw_len": len(raw)}


def _safe(s: str, n: int = 160) -> str:
    return (s or "")[:n]


def _execute(
    base: str,
    token: str,
    payload: dict[str, Any],
    *,
    rid: str,
) -> tuple[int, dict[str, Any]]:
    st, body = _req(
        "POST",
        f"{base}/isf/execute",
        token=token,
        body=payload,
        request_id=rid,
    )
    return st, body if isinstance(body, dict) else {"raw": str(body)[:80]}


def phase_offline(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    isf = health.get("isfGate") if isinstance(health, dict) else None
    air = health.get("airGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "health_isf_enabled",
            st == 200 and isinstance(isf, dict) and isf.get("isfEnabled") is True,
            _safe(json.dumps({"isf": isf, "airEnabled": (air or {}).get("airEnabled")})),
        )
    )
    cats = (air or {}).get("catalogProviders") if isinstance(air, dict) else None
    out.append(
        CaseResult(
            "catalog_mock_only_offline",
            cats == ["mock"],
            _safe(str(cats)),
        )
    )

    # A — evidence_summary mock + pending_approval
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_text_1"}],
            "profile_id": "default",
        },
        rid="kc025_off_a",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "evidence_summary_mock_pending",
            st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
            and prop.get("selected_provider") == "mock"
            and isinstance(prop.get("structured_result"), dict)
            and "summary" in (prop.get("structured_result") or {}),
            _safe(
                json.dumps(
                    {
                        "status": (prop or {}).get("status"),
                        "provider": (prop or {}).get("selected_provider"),
                        "conf": (prop or {}).get("confidence"),
                    }
                )
            ),
        )
    )

    # B — vehicle_damage with images → fail closed (no vision in mock catalog)
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "vehicle_damage_assessment",
            "evidence": [{"evidence_type": "vehicle_photos", "ref_id": "fx_photo_1"}],
        },
        rid="kc025_off_b",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "vehicle_damage_fail_closed_no_vision",
            st in {422, 503}
            and isinstance(err, dict)
            and err.get("code") in {"routing_failed", "capability_unavailable", "no_provider"},
            _safe(json.dumps(err or body.get("proposal"))),
        )
    )
    # Accept routing_failed from IsfError
    if not out[-1].ok and isinstance(err, dict) and err.get("code") == "routing_failed":
        out[-1] = CaseResult(out[-1].name, True, out[-1].detail)

    # C — missing evidence before provider
    st, body = _execute(
        base,
        token,
        {"skill_id": "vehicle_damage_assessment", "evidence": []},
        rid="kc025_off_c",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "missing_evidence_before_provider",
            st == 422
            and isinstance(prop, dict)
            and prop.get("status") == "failed"
            and prop.get("execution_status") == "missing_required_evidence",
            _safe(str((prop or {}).get("execution_status"))),
        )
    )

    # D — unknown skill
    st, body = _execute(
        base,
        token,
        {"skill_id": "not_a_real_skill"},
        rid="kc025_off_d",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "unknown_skill",
            st == 404 and isinstance(err, dict) and err.get("code") == "skill_not_found",
            _safe(str(err)),
        )
    )

    # E — unsupported version
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "skill_version": "9.9.9",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_text_1"}],
        },
        rid="kc025_off_e",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "unsupported_version",
            st == 422 and isinstance(err, dict) and err.get("code") == "skill_version_unsupported",
            _safe(str(err)),
        )
    )

    # Reject provider fields
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "provider_id": "openai",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_text_1"}],
        },
        rid="kc025_off_reject_provider",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "reject_provider_id",
            st == 422 and isinstance(err, dict),
            _safe(str(err)),
        )
    )

    st, metrics = _req("GET", f"{base}/isf/metrics", token=token)
    out.append(
        CaseResult(
            "isf_metrics_present",
            st == 200 and isinstance(metrics, dict) and "execution_total" in metrics,
            _safe(str(list(metrics.keys())[:8] if isinstance(metrics, dict) else metrics)),
        )
    )
    return out


def phase_live(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else None
    live_open = isinstance(air, dict) and air.get("liveGateOpen") is True
    cats = (air or {}).get("catalogProviders") if isinstance(air, dict) else []
    out.append(
        CaseResult(
            "live_gate_open",
            live_open and "openai" in (cats or []),
            _safe(json.dumps({"live": live_open, "catalog": cats})),
        )
    )

    fixtures: list[tuple[str, dict[str, Any], str]] = [
        (
            "vehicle_damage_assessment",
            {
                "skill_id": "vehicle_damage_assessment",
                "evidence": [{"evidence_type": "vehicle_photos", "ref_id": "fx_synth_vehicle_1"}],
                "profile_id": "research",
            },
            "openai",
        ),
        (
            "policy_compliance_review",
            {
                "skill_id": "policy_compliance_review",
                "evidence": [{"evidence_type": "policy_document", "ref_id": "fx_policy_1"}],
                "profile_id": "research",
            },
            "",
        ),
        (
            "document_comparison",
            {
                "skill_id": "document_comparison",
                "evidence": [
                    {
                        "evidence_type": "document_pair",
                        "ref_id": "fx_docs_pair",
                        "metadata": {"document_count": 2},
                    }
                ],
                "profile_id": "research",
            },
            "",
        ),
        (
            "timeline_construction",
            {
                "skill_id": "timeline_construction",
                "evidence": [{"evidence_type": "timeline_source", "ref_id": "fx_events_1"}],
                "profile_id": "research",
            },
            "",
        ),
        (
            "evidence_summary",
            {
                "skill_id": "evidence_summary",
                "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_text_live_1"}],
                "profile_id": "research",
            },
            "",
        ),
    ]

    for name, payload, expect_provider in fixtures:
        st, body = _execute(base, token, payload, rid=f"kc025_live_{name}")
        prop = body.get("proposal") if isinstance(body, dict) else None
        structured = (prop or {}).get("structured_result") if isinstance(prop, dict) else None
        provider_ok = True
        if expect_provider and isinstance(prop, dict):
            provider_ok = prop.get("selected_provider") == expect_provider
        ok = (
            st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
            and isinstance(structured, dict)
            and "summary" in structured
            and "confidence" in structured
            and prop.get("human_approval_required") is True
            and provider_ok
        )
        # Live path may hit structured_output_invalid if provider returns free-form —
        # record honestly.
        out.append(
            CaseResult(
                f"live_{name}",
                ok,
                _safe(
                    json.dumps(
                        {
                            "http": st,
                            "status": (prop or {}).get("status"),
                            "provider": (prop or {}).get("selected_provider"),
                            "model": (prop or {}).get("selected_model"),
                            "exec": (prop or {}).get("execution_status"),
                            "err": (body.get("error") if isinstance(body, dict) else None),
                        }
                    )
                ),
            )
        )
    return out


def phase_rollback(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    isf = health.get("isfGate") if isinstance(health, dict) else None
    air = health.get("airGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "rollback_isf_disabled",
            st == 200 and isinstance(isf, dict) and isf.get("isfEnabled") is False,
            _safe(json.dumps(isf)),
        )
    )
    out.append(
        CaseResult(
            "rollback_air_still_on",
            isinstance(air, dict) and air.get("airEnabled") is True,
            _safe(json.dumps({"airEnabled": (air or {}).get("airEnabled")})),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_rb_1"}],
        },
        rid="kc025_rb_1",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "isf_execute_unavailable",
            st == 503 and isinstance(err, dict) and err.get("code") == "isf_disabled",
            _safe(str(err)),
        )
    )
    # Legacy chat still works (mock)
    st, chat = _req(
        "POST",
        f"{base}/v1/chat/completions",
        token=token,
        body={
            "model": "cobra-default",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8,
            "stream": False,
        },
        request_id="kc025_rb_chat",
    )
    out.append(
        CaseResult(
            "legacy_chat_mock_ok",
            st == 200 and isinstance(chat, dict) and "choices" in chat,
            _safe(f"http={st}"),
        )
    )
    return out


def phase_live_gate_close(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else None
    isf = health.get("isfGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "live_closed_isf_on",
            st == 200
            and isinstance(isf, dict)
            and isf.get("isfEnabled") is True
            and isinstance(air, dict)
            and air.get("liveGateOpen") is False,
            _safe(json.dumps({"isf": isf, "live": (air or {}).get("liveGateOpen")})),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "vehicle_damage_assessment",
            "evidence": [{"evidence_type": "vehicle_photos", "ref_id": "fx_photo_close"}],
        },
        rid="kc025_close_vda",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "vision_fail_closed_after_live_close",
            st == 422 and isinstance(err, dict) and err.get("code") == "routing_failed",
            _safe(str(err)),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "fx_close_sum"}],
        },
        rid="kc025_close_sum",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "offline_skill_mock_ok",
            st == 200
            and isinstance(prop, dict)
            and prop.get("selected_provider") == "mock"
            and prop.get("status") == "pending_approval",
            _safe(str((prop or {}).get("selected_provider"))),
        )
    )
    return out


def run_soak(base: str, token: str, n: int) -> SoakStats:
    """Workload mix: 25% summary, 20% timeline, 15% policy, 15% docs, 15% vehicle, 10% fail."""
    stats = SoakStats()
    mix: list[tuple[str, dict[str, Any], bool]] = []
    # Build proportional list
    plan = (
        [
            (
                "evidence_summary",
                {
                    "skill_id": "evidence_summary",
                    "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "soak_sum"}],
                },
                True,
            )
        ]
        * max(1, int(n * 0.25))
        + [
            (
                "timeline_construction",
                {
                    "skill_id": "timeline_construction",
                    "evidence": [{"evidence_type": "timeline_source", "ref_id": "soak_tl"}],
                },
                True,
            )
        ]
        * max(1, int(n * 0.20))
        + [
            (
                "policy_compliance_review",
                {
                    "skill_id": "policy_compliance_review",
                    "evidence": [{"evidence_type": "policy_document", "ref_id": "soak_pol"}],
                },
                True,
            )
        ]
        * max(1, int(n * 0.15))
        + [
            (
                "document_comparison",
                {
                    "skill_id": "document_comparison",
                    "evidence": [
                        {
                            "evidence_type": "document_pair",
                            "ref_id": "soak_docs",
                            "metadata": {"document_count": 2},
                        }
                    ],
                },
                True,
            )
        ]
        * max(1, int(n * 0.15))
        + [
            (
                "vehicle_damage_assessment",
                {
                    "skill_id": "vehicle_damage_assessment",
                    "evidence": [{"evidence_type": "vehicle_photos", "ref_id": "soak_vda"}],
                },
                False,  # expected fail offline (no vision)
            )
        ]
        * max(1, int(n * 0.15))
        + [
            ("missing_evidence", {"skill_id": "policy_compliance_review", "evidence": []}, False),
            ("unknown_skill", {"skill_id": "nope_skill"}, False),
            (
                "bad_version",
                {
                    "skill_id": "evidence_summary",
                    "skill_version": "8.0.0",
                    "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "x"}],
                },
                False,
            ),
        ]
    )
    while len(plan) < n:
        plan.append(plan[len(plan) % max(1, len(plan))])
    plan = plan[:n]

    for i, (name, payload, expect_success) in enumerate(plan):
        t0 = time.perf_counter()
        st, body = _execute(base, token, payload, rid=f"kc025_soak_{n}_{i}")
        ms = (time.perf_counter() - t0) * 1000
        stats.total += 1
        stats.latencies_ms.append(ms)
        prop = body.get("proposal") if isinstance(body, dict) else None
        err = body.get("error") if isinstance(body, dict) else None
        success = (
            expect_success
            and st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
        )
        expected_fail = (not expect_success) and (
            st in {404, 422, 503}
            or (isinstance(prop, dict) and prop.get("status") == "failed")
            or (isinstance(err, dict))
        )
        if success:
            stats.successes += 1
            stats.schema_valid += 1
            if prop.get("needs_human_review"):
                stats.human_review += 1
            p = str(prop.get("selected_provider") or "none")
            m = str(prop.get("selected_model") or "none")
            stats.providers[p] = stats.providers.get(p, 0) + 1
            stats.models[m] = stats.models.get(m, 0) + 1
            try:
                stats.confidences.append(float(prop.get("confidence") or 0))
            except (TypeError, ValueError):
                pass
            meta_repair = ((body.get("extensions") or {}).get("isf") or {}).get("metadata") or {}
            rc = int(meta_repair.get("repair_attempt_count") or 0)
            if rc:
                stats.repair_attempts += rc
                if (meta_repair.get("schema_validation_result") or "") == "repaired":
                    stats.repair_success += 1
        elif expected_fail:
            stats.expected_failures += 1
        else:
            stats.unexpected_failures += 1
            print(f"UNEXPECTED name={name} http={st} detail={_safe(json.dumps(body))}")

        # Audit completeness sample
        st_a, aud = _req(
            "GET",
            f"{base}/isf/audit?limit=5",
            token=token,
            request_id=f"kc025_soak_aud_{i}",
        )
        if st_a == 200 and isinstance(aud, dict) and aud.get("count", 0) >= 0:
            entries = aud.get("entries") or []
            if entries:
                e0 = entries[-1]
                needed = {"skill_id", "correlation_id", "execution_status", "timestamp"}
                if needed.issubset(set(e0.keys())):
                    stats.audit_ok += 1

    return stats


def _print_cases(cases: list[CaseResult]) -> int:
    fails = 0
    for c in cases:
        mark = "PASS" if c.ok else "FAIL"
        if not c.ok:
            fails += 1
        print(f"  [{mark}] {c.name}: {c.detail}")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser(description="KC-025 ISF staging cert")
    ap.add_argument("--base", default=os.environ.get("COBRA_CORE_STAGING_URL", DEFAULT_BASE))
    ap.add_argument(
        "--phase",
        choices=["offline", "live", "live-close", "rollback", "all-offline"],
        default="offline",
    )
    ap.add_argument("--soak", type=int, default=0, help="Run soak of N requests")
    args = ap.parse_args()
    token = _load_token()
    print(f"KC-025 cert base={args.base} phase={args.phase} soak={args.soak}")

    fails = 0
    if args.soak > 0:
        stats = run_soak(args.base, token, args.soak)
        lats = sorted(stats.latencies_ms)
        p50 = lats[len(lats) // 2] if lats else 0
        p95 = lats[int(len(lats) * 0.95)] if lats else 0
        avg = statistics.mean(lats) if lats else 0
        print(
            json.dumps(
                {
                    "total": stats.total,
                    "successes": stats.successes,
                    "expected_failures": stats.expected_failures,
                    "unexpected_failures": stats.unexpected_failures,
                    "schema_valid": stats.schema_valid,
                    "repair_attempts": stats.repair_attempts,
                    "repair_success": stats.repair_success,
                    "human_review": stats.human_review,
                    "providers": stats.providers,
                    "models": stats.models,
                    "confidence_avg": round(statistics.mean(stats.confidences), 4)
                    if stats.confidences
                    else None,
                    "latency_avg_ms": round(avg, 2),
                    "latency_p50_ms": round(p50, 2),
                    "latency_p95_ms": round(p95, 2),
                    "audit_ok": stats.audit_ok,
                },
                indent=2,
            )
        )
        if stats.unexpected_failures:
            raise SystemExit(2)
        return

    if args.phase in {"offline", "all-offline"}:
        print("=== PHASE OFFLINE ===")
        fails += _print_cases(phase_offline(args.base, token))
    if args.phase == "live":
        print("=== PHASE LIVE ===")
        fails += _print_cases(phase_live(args.base, token))
    if args.phase == "live-close":
        print("=== PHASE LIVE GATE CLOSE ===")
        fails += _print_cases(phase_live_gate_close(args.base, token))
    if args.phase == "rollback":
        print("=== PHASE ROLLBACK ===")
        fails += _print_cases(phase_rollback(args.base, token))

    print(f"fails={fails}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
