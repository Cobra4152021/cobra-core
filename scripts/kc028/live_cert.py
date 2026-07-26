#!/usr/bin/env python3
"""KC-028 live Vault-backed skill probes (staging). No secrets logged."""

from __future__ import annotations

import json
import os
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = os.environ.get(
    "COBRA_CORE_BASE_URL", "https://cobra-core-staging.cobra4152020.workers.dev"
)
ORG = "org_staging_smoke"
UA = "CobraKC0281Cert/1.0 (compatible; Mozilla/5.0)"
FIXTURES = Path(__file__).with_name("staging_fixtures.json")


def _token() -> str:
    env = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    if env:
        return env
    path = Path(os.environ.get("TEMP", os.environ.get("TMP", "."))) / "kc018-core-auth.txt"
    return path.read_text(encoding="utf-8").strip()


def _req(method: str, url: str, body: dict[str, Any] | None = None, timeout: float = 120.0):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {_token()}",
        "X-Cobra-Org-Id": ORG,
        "Content-Type": "application/json",
        "User-Agent": UA,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), json.loads(raw) if raw.startswith("{") else raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return int(exc.code), json.loads(raw)
        except json.JSONDecodeError:
            return int(exc.code), {"raw_prefix": raw[:160]}
    except TimeoutError:
        return 598, {"error": "timeout"}


def _status(body: Any) -> str:
    if not isinstance(body, dict):
        return ""
    prop = body.get("proposal") if isinstance(body.get("proposal"), dict) else {}
    err = (
        (body.get("output") or {}).get("error")
        or (prop.get("structured_result") or {}).get("error")
        or body.get("error")
        or {}
    )
    if isinstance(err, dict) and err.get("code"):
        return str(err["code"])
    return str(
        prop.get("status")
        or prop.get("execution_status")
        or body.get("status")
        or body.get("execution_status")
        or ""
    )


def main() -> int:
    fixtures = {f["filename"]: f["manifestKey"] for f in json.loads(FIXTURES.read_text())}
    cases = [
        ("policy_compliance_review", "policy_document", fixtures["kc028-policy.txt"]),
        ("contract_analysis", "contract_document", fixtures["kc028-contract.txt"]),
        ("budget_analysis", "budget_spreadsheet", fixtures["kc028-budget.csv"]),
        ("timeline_construction", "timeline_source", fixtures["kc028-timeline.txt"]),
        ("evidence_summary", "evidence_bundle", fixtures["kc028-bundle.txt"]),
    ]
    print(f"KC-028 live cert base={BASE}")
    fails = 0
    latencies: list[float] = []
    for skill, et, key in cases:
        t0 = time.perf_counter()
        st, body = _req(
            "POST",
            f"{BASE}/isf/execute",
            {
                "skill_id": skill,
                "evidence": [{"evidence_type": et, "ref_id": key}],
                "profile_id": "default",
            },
        )
        ms = (time.perf_counter() - t0) * 1000
        latencies.append(ms)
        status = _status(body)
        ok = status in {
            "pending_approval",
            "completed",
            "needs_human_review",
        } or (
            isinstance(body, dict)
            and (body.get("proposal") or {}).get("status") == "pending_approval"
        )
        # Mock provider + governance: pending_approval is the success path.
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {skill}: http={st} status={status} "
            f"latency_ms={ms:.0f}"
        )
        fails += 0 if ok else 1

    # Security: invented citation / missing token already covered offline; deny path.
    st, body = _req(
        "POST",
        f"{BASE}/isf/execute",
        {
            "skill_id": "policy_compliance_review",
            "evidence": [
                {
                    "evidence_type": "policy_document",
                    "ref_id": "manifests/dev/does-not-exist-kc028.json",
                }
            ],
            "profile_id": "default",
        },
    )
    status = _status(body)
    ok = "missing_required_evidence" in status or st in {400, 422}
    print(f"  [{'PASS' if ok else 'FAIL'}] missing_vault_ref: status={status}")
    fails += 0 if ok else 1

    # Auth: no bearer
    req = urllib.request.Request(f"{BASE}/kef/diagnostics", method="GET")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = int(resp.status)
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
    ok = code == 401
    print(f"  [{'PASS' if ok else 'FAIL'}] diagnostics_requires_auth: http={code}")
    fails += 0 if ok else 1

    lat = sorted(latencies)
    print(
        json.dumps(
            {
                "live_skill_count": len(cases),
                "latency_avg_ms": round(statistics.mean(lat), 2) if lat else 0,
                "latency_p50_ms": round(lat[len(lat) // 2], 2) if lat else 0,
                "latency_p95_ms": round(lat[max(0, int(len(lat) * 0.95) - 1)], 2) if lat else 0,
            },
            indent=2,
        )
    )
    print(f"fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
