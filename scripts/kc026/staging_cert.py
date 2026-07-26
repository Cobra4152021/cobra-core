#!/usr/bin/env python3
"""KC-026 RRF staging certification harness (never logs secrets/prompts)."""

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
UA = "CobraKC026Cert/1.0 (compatible; Mozilla/5.0)"


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
    latencies_ms: list[float] = field(default_factory=list)


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
            if raw.startswith("{"):
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
    base: str, token: str, payload: dict[str, Any], *, rid: str
) -> tuple[int, dict[str, Any]]:
    st, body = _req("POST", f"{base}/isf/execute", token=token, body=payload, request_id=rid)
    return st, body if isinstance(body, dict) else {"raw": str(body)[:80]}


def phase_offline(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    rrf = health.get("rrfGate") if isinstance(health, dict) else None
    air = health.get("airGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "rrf_enabled",
            st == 200 and isinstance(rrf, dict) and rrf.get("rrfEnabled") is True,
            _safe(json.dumps(rrf)),
        )
    )
    out.append(
        CaseResult(
            "catalog_mock_only",
            (air or {}).get("catalogProviders") == ["mock"],
            _safe(str((air or {}).get("catalogProviders"))),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "rrf_fx_1"}],
        },
        rid="kc026_off_sum",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "mock_pending_approval",
            st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
            and prop.get("selected_provider") == "mock",
            _safe(
                json.dumps(
                    {
                        "status": (prop or {}).get("status"),
                        "p": (prop or {}).get("selected_provider"),
                    }
                )
            ),
        )
    )
    st, body = _execute(
        base,
        token,
        {"skill_id": "vehicle_damage_assessment", "evidence": []},
        rid="kc026_off_miss",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "missing_evidence_before_provider",
            st == 422
            and isinstance(prop, dict)
            and prop.get("execution_status") == "missing_required_evidence",
            _safe(str((prop or {}).get("execution_status"))),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "vehicle_damage_assessment",
            "evidence": [{"evidence_type": "vehicle_photos", "ref_id": "p1"}],
        },
        rid="kc026_off_vision",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "vision_fail_closed",
            st == 422 and isinstance(err, dict) and err.get("code") == "routing_failed",
            _safe(str(err)),
        )
    )
    st, metrics = _req("GET", f"{base}/rrf/metrics", token=token)
    out.append(
        CaseResult(
            "rrf_metrics",
            st == 200 and isinstance(metrics, dict) and metrics.get("rrf_enabled") is True,
            _safe(str(list(metrics.keys())[:8] if isinstance(metrics, dict) else metrics)),
        )
    )
    st, audit = _req("GET", f"{base}/rrf/audit?limit=5", token=token)
    out.append(
        CaseResult(
            "rrf_audit",
            st == 200 and isinstance(audit, dict) and "entries" in audit,
            _safe(f"count={audit.get('count') if isinstance(audit, dict) else None}"),
        )
    )
    return out


def phase_live(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "live_gate",
            isinstance(air, dict)
            and air.get("liveGateOpen") is True
            and "openai" in (air.get("catalogProviders") or []),
            _safe(
                json.dumps(
                    {
                        "live": (air or {}).get("liveGateOpen"),
                        "cat": (air or {}).get("catalogProviders"),
                    }
                )
            ),
        )
    )
    for skill, evidence in [
        ("evidence_summary", [{"evidence_type": "evidence_bundle", "ref_id": "live_sum"}]),
        ("policy_compliance_review", [{"evidence_type": "policy_document", "ref_id": "live_pol"}]),
        ("timeline_construction", [{"evidence_type": "timeline_source", "ref_id": "live_tl"}]),
        (
            "document_comparison",
            [
                {
                    "evidence_type": "document_pair",
                    "ref_id": "live_docs",
                    "metadata": {"document_count": 2},
                }
            ],
        ),
        ("vehicle_damage_assessment", [{"evidence_type": "vehicle_photos", "ref_id": "live_vda"}]),
    ]:
        st, body = _execute(
            base,
            token,
            {"skill_id": skill, "evidence": evidence, "profile_id": "research"},
            rid=f"kc026_live_{skill}",
        )
        prop = body.get("proposal") if isinstance(body, dict) else None
        out.append(
            CaseResult(
                f"live_{skill}",
                st == 200
                and isinstance(prop, dict)
                and prop.get("status") == "pending_approval"
                and isinstance(prop.get("structured_result"), dict)
                and prop.get("human_approval_required") is True,
                _safe(
                    json.dumps(
                        {
                            "http": st,
                            "status": (prop or {}).get("status"),
                            "provider": (prop or {}).get("selected_provider"),
                            "model": (prop or {}).get("selected_model"),
                        }
                    )
                ),
            )
        )
    return out


def phase_rollback(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    rrf = health.get("rrfGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "rrf_disabled",
            st == 200 and isinstance(rrf, dict) and rrf.get("rrfEnabled") is False,
            _safe(json.dumps(rrf)),
        )
    )
    st, body = _execute(
        base,
        token,
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "rb_1"}],
        },
        rid="kc026_rb_sum",
    )
    prop = body.get("proposal") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "kc025_path_pending",
            st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
            and prop.get("selected_provider") == "mock",
            _safe(str((prop or {}).get("status"))),
        )
    )
    return out


def run_soak(base: str, token: str, n: int) -> SoakStats:
    stats = SoakStats()
    for i in range(n):
        t0 = time.perf_counter()
        # Mix: mostly success, some expected vision fail-closed
        if i % 10 == 9:
            payload = {
                "skill_id": "vehicle_damage_assessment",
                "evidence": [{"evidence_type": "vehicle_photos", "ref_id": f"soak_v_{i}"}],
            }
            expect_ok = False
        else:
            payload = {
                "skill_id": "evidence_summary",
                "evidence": [{"evidence_type": "evidence_bundle", "ref_id": f"soak_s_{i}"}],
            }
            expect_ok = True
        st, body = _execute(base, token, payload, rid=f"kc026_soak_{n}_{i}")
        stats.total += 1
        stats.latencies_ms.append((time.perf_counter() - t0) * 1000)
        prop = body.get("proposal") if isinstance(body, dict) else None
        err = body.get("error") if isinstance(body, dict) else None
        ok = (
            expect_ok
            and st == 200
            and isinstance(prop, dict)
            and prop.get("status") == "pending_approval"
        )
        exp_fail = (not expect_ok) and (st == 422 or isinstance(err, dict))
        if ok:
            stats.successes += 1
        elif exp_fail:
            stats.expected_failures += 1
        else:
            stats.unexpected_failures += 1
            print("UNEXPECTED", i, st, _safe(json.dumps(body)))
    return stats


def _print(cases: list[CaseResult]) -> int:
    fails = 0
    for c in cases:
        mark = "PASS" if c.ok else "FAIL"
        if not c.ok:
            fails += 1
        print(f"  [{mark}] {c.name}: {c.detail}")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("COBRA_CORE_STAGING_URL", DEFAULT_BASE))
    ap.add_argument("--phase", choices=["offline", "live", "rollback"], default="offline")
    ap.add_argument("--soak", type=int, default=0)
    args = ap.parse_args()
    token = _load_token()
    print(f"KC-026 cert base={args.base} phase={args.phase} soak={args.soak}")
    if args.soak:
        stats = run_soak(args.base, token, args.soak)
        lats = sorted(stats.latencies_ms)
        p50 = lats[len(lats) // 2] if lats else 0
        p95 = lats[int(len(lats) * 0.95)] if lats else 0
        print(
            json.dumps(
                {
                    "total": stats.total,
                    "successes": stats.successes,
                    "expected_failures": stats.expected_failures,
                    "unexpected_failures": stats.unexpected_failures,
                    "latency_avg_ms": round(statistics.mean(lats), 2) if lats else 0,
                    "latency_p50_ms": round(p50, 2),
                    "latency_p95_ms": round(p95, 2),
                },
                indent=2,
            )
        )
        raise SystemExit(2 if stats.unexpected_failures else 0)
    fails = 0
    if args.phase == "offline":
        fails = _print(phase_offline(args.base, token))
    elif args.phase == "live":
        fails = _print(phase_live(args.base, token))
    else:
        fails = _print(phase_rollback(args.base, token))
    print(f"fails={fails}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
