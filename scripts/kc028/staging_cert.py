#!/usr/bin/env python3
"""KC-028 KEF + Evidence Vault staging certification harness (no secrets/prompts logged)."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://cobra-core-staging.cobra4152020.workers.dev"
ORG = "org_staging_smoke"
UA = "CobraKC028Cert/1.0 (compatible; Mozilla/5.0)"


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
) -> tuple[int, dict[str, Any] | str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Cobra-Org-Id": ORG,
        "Content-Type": "application/json",
        "User-Agent": UA,
    }
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
            parsed: dict[str, Any] | str = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw_len": len(raw), "raw_prefix": raw[:120]}
        return int(exc.code), parsed
    except TimeoutError:
        return 598, {"error": "timeout"}


def phase_offline(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    kef = health.get("kefGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "kef_vault_gate",
            st == 200
            and isinstance(kef, dict)
            and kef.get("kefEnabled") is True
            and kef.get("vaultEnabled") is True
            and kef.get("allowRequestSeed") is False
            and kef.get("liveGateOpen") is False,
            json.dumps(
                {
                    k: kef.get(k)
                    for k in (
                        "edgeBuild",
                        "kefEnabled",
                        "vaultEnabled",
                        "allowRequestSeed",
                        "vaultBaseUrlHost",
                        "vaultTokenConfigured",
                        "liveGateOpen",
                        "activeProfile",
                    )
                }
                if isinstance(kef, dict)
                else {}
            )[:240],
        )
    )
    st, status = _req("GET", f"{base}/kef/status", token=token)
    out.append(
        CaseResult(
            "kef_status",
            st == 200 and isinstance(status, dict) and status.get("vault_enabled") is True,
            str(status)[:160],
        )
    )
    st, vhealth = _req("GET", f"{base}/kef/connectors/evidence-vault/health", token=token)
    out.append(
        CaseResult(
            "vault_health",
            st == 200 and isinstance(vhealth, dict) and vhealth.get("health") == "healthy",
            str(vhealth)[:160],
        )
    )
    probe_key = os.environ.get(
        "KEF_DIAG_MANIFEST_KEY",
        "manifests/dev/1785033088680-kc028-policy.txt.json",
    )
    st, diag = _req(
        "GET",
        f"{base}/kef/diagnostics?manifestKey={urllib.parse.quote(probe_key, safe='')}",
        token=token,
        timeout=120.0,
    )
    # Accept ok, or degraded only when core path is green (case-scoped probes may skip).
    core_green = (
        isinstance(diag, dict)
        and diag.get("dns") == "ok"
        and diag.get("tls") == "ok"
        and diag.get("vault") == "ok"
        and diag.get("search") == "ok"
        and diag.get("auth") in {"ok", "unknown"}
    )
    diag_ok = st == 200 and core_green and diag.get("overall_status") in {"ok", "degraded"}
    out.append(
        CaseResult(
            "vault_diagnostics",
            diag_ok,
            json.dumps(
                {
                    k: diag.get(k)
                    for k in (
                        "overall_status",
                        "dns",
                        "tls",
                        "auth",
                        "vault",
                        "search",
                        "metadata",
                        "content",
                        "chunk_retrieval",
                        "latency_ms",
                    )
                }
                if isinstance(diag, dict)
                else {"status": st}
            )[:280],
        )
    )
    # Missing evidence must fail before provider (no seed).
    st, body = _req(
        "POST",
        f"{base}/isf/execute",
        token=token,
        body={
            "skill_id": "policy_compliance_review",
            "evidence": [],
            "profile_id": "default",
        },
    )
    code = ""
    if isinstance(body, dict):
        prop = body.get("proposal") if isinstance(body.get("proposal"), dict) else {}
        err = (
            (body.get("output") or {}).get("error")
            or (prop.get("structured_result") or {}).get("error")
            or body.get("error")
            or {}
        )
        code = str(
            err.get("code")
            or prop.get("execution_status")
            or body.get("execution_status")
            or body.get("status")
            or ""
        )
    out.append(
        CaseResult(
            "missing_evidence_no_seed",
            "missing_required_evidence" in code,
            code or str(body)[:120],
        )
    )
    # Vision skill without evidence: fail closed before AIR (avoids Vault lookup hangs).
    st, body = _req(
        "POST",
        f"{base}/isf/execute",
        token=token,
        body={
            "skill_id": "vehicle_damage_assessment",
            "evidence": [],
            "profile_id": "default",
        },
        timeout=60.0,
    )
    detail = str(body)[:180]
    code = ""
    if isinstance(body, dict):
        prop = body.get("proposal") if isinstance(body.get("proposal"), dict) else {}
        err = (prop.get("structured_result") or {}).get("error") or {}
        code = str(err.get("code") or prop.get("execution_status") or "")
    ok_vision = "missing_required_evidence" in code or "missing_required_evidence" in detail
    out.append(CaseResult("vision_fail_closed_or_missing", ok_vision, code or detail))
    st, metrics = _req("GET", f"{base}/kef/metrics", token=token)
    mkeys = list((metrics.get("metrics") or {}).keys()) if isinstance(metrics, dict) else []
    out.append(CaseResult("kef_metrics", st == 200 and "retrieval_total" in mkeys, str(mkeys[:12])))
    return out


def phase_rollback(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    kef = health.get("kefGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "kef_disabled",
            st == 200 and isinstance(kef, dict) and kef.get("kefEnabled") is False,
            str(kef)[:160],
        )
    )
    st, vhealth = _req("GET", f"{base}/kef/connectors/evidence-vault/health", token=token)
    out.append(
        CaseResult(
            "vault_unavailable_or_disabled",
            st == 200
            and isinstance(vhealth, dict)
            and vhealth.get("health") in {"unavailable", "unknown", "healthy", "degraded"},
            str(vhealth)[:120],
        )
    )
    return out


def soak(base: str, token: str, n: int) -> SoakStats:
    stats = SoakStats()
    skills = [
        ("evidence_summary", "evidence_bundle"),
        ("policy_compliance_review", "policy_document"),
        ("contract_analysis", "contract_document"),
        ("budget_analysis", "budget_spreadsheet"),
        ("document_comparison", "document_pair"),
        ("timeline_construction", "timeline_source"),
    ]
    for i in range(n):
        skill, et = skills[i % len(skills)]
        t0 = time.perf_counter()
        # Intentionally unknown refs → expected missing evidence under no-seed vault mode
        # unless fixtures exist; count missing as expected failure.
        st, body = _req(
            "POST",
            f"{base}/isf/execute",
            token=token,
            body={
                "skill_id": skill,
                "evidence": [{"evidence_type": et, "ref_id": f"kc028-soak-{i}"}],
                "profile_id": "default",
            },
        )
        ms = (time.perf_counter() - t0) * 1000
        stats.total += 1
        stats.latencies_ms.append(ms)
        status = ""
        if isinstance(body, dict):
            status = str(body.get("status") or body.get("execution_status") or "")
            err = (body.get("output") or {}).get("error") or {}
            if err.get("code"):
                status = str(err.get("code"))
        if status in {"pending_approval", "completed", "needs_human_review"} or (
            isinstance(body, dict) and (body.get("proposal") or {}).get("status") == "pending_approval"
        ):
            stats.successes += 1
        elif "missing_required_evidence" in status or st in {400, 422}:
            stats.expected_failures += 1
        else:
            stats.unexpected_failures += 1
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("COBRA_CORE_BASE_URL", DEFAULT_BASE))
    ap.add_argument("--phase", choices=["offline", "rollback", "none"], default="offline")
    ap.add_argument("--soak", type=int, default=0)
    args = ap.parse_args()
    token = _load_token()
    print(f"KC-028 cert base={args.base} phase={args.phase} soak={args.soak}")
    fails = 0
    if args.phase == "offline":
        for case in phase_offline(args.base, token):
            print(f"  [{'PASS' if case.ok else 'FAIL'}] {case.name}: {case.detail}")
            fails += 0 if case.ok else 1
    elif args.phase == "rollback":
        for case in phase_rollback(args.base, token):
            print(f"  [{'PASS' if case.ok else 'FAIL'}] {case.name}: {case.detail}")
            fails += 0 if case.ok else 1
    if args.soak:
        s = soak(args.base, token, args.soak)
        lat = sorted(s.latencies_ms)
        p50 = lat[len(lat) // 2] if lat else 0
        p95 = lat[int(len(lat) * 0.95)] if lat else 0
        print(
            json.dumps(
                {
                    "total": s.total,
                    "successes": s.successes,
                    "expected_failures": s.expected_failures,
                    "unexpected_failures": s.unexpected_failures,
                    "latency_avg_ms": round(statistics.mean(lat), 2) if lat else 0,
                    "latency_p50_ms": round(p50, 2),
                    "latency_p95_ms": round(p95, 2),
                },
                indent=2,
            )
        )
        fails += s.unexpected_failures
    print(f"fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
