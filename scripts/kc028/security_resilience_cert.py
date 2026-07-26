#!/usr/bin/env python3
"""KC-028 security + resilience staging probes (no secrets/bodies logged)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = os.environ.get("COBRA_CORE_BASE_URL", "https://cobra-core-staging.cobra4152020.workers.dev")
ORG = "org_staging_smoke"
UA = "CobraKC0281Cert/1.0 (compatible; Mozilla/5.0)"


def _token() -> str:
    env = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    if env:
        return env
    return (
        (Path(os.environ.get("TEMP", os.environ.get("TMP", "."))) / "kc018-core-auth.txt")
        .read_text(encoding="utf-8")
        .strip()
    )


def _req(method: str, url: str, *, token: str | None, body: dict | None = None, timeout=60.0):
    headers = {"User-Agent": UA, "X-Cobra-Org-Id": ORG, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
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
            return int(exc.code), {"raw_prefix": raw[:120]}


def _no_secrets(obj: Any) -> bool:
    blob = json.dumps(obj).lower()
    token = _token().lower()
    forbidden = ["x-hidden-grid-key", "bearer ", token]
    # Never require vault token presence; just ensure Core auth secret not echoed.
    return not any(f and f in blob for f in forbidden if f != "bearer ")


def main() -> int:
    token = _token()
    fails = 0
    print(f"KC-028 security/resilience base={BASE}")

    # Wrong / missing auth
    for name, tok, expect in [
        ("missing_bearer", None, 401),
        ("wrong_bearer", "not-the-real-secret", 401),
    ]:
        st, body = _req("GET", f"{BASE}/kef/diagnostics", token=tok)
        ok = st == expect and _no_secrets(body)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: http={st}")
        fails += 0 if ok else 1

    # Metrics / audit must not contain tokens
    for path in ("/kef/metrics", "/kef/audit", "/kef/status", "/kef/diagnostics"):
        st, body = _req("GET", f"{BASE}{path}", token=token, timeout=120)
        ok = st == 200 and _no_secrets(body)
        print(f"  [{'PASS' if ok else 'FAIL'}] no_secret_leak:{path}: http={st}")
        fails += 0 if ok else 1

    # Governance: live=false stays closed
    st, health = _req("GET", f"{BASE}/health", token=token)
    kef = health.get("kefGate") if isinstance(health, dict) else {}
    ok = st == 200 and kef.get("liveGateOpen") is False and kef.get("allowRequestSeed") is False
    print(
        f"  [{'PASS' if ok else 'FAIL'}] governance_gates: live={kef.get('liveGateOpen')} seed={kef.get('allowRequestSeed')}"
    )
    fails += 0 if ok else 1

    # Resilience: vault health remains healthy under repeated probes
    healths = []
    for _ in range(5):
        st, body = _req("GET", f"{BASE}/kef/connectors/evidence-vault/health", token=token)
        healths.append((st, body.get("health") if isinstance(body, dict) else None))
    ok = all(h == "healthy" for _, h in healths)
    print(f"  [{'PASS' if ok else 'FAIL'}] vault_health_repeat: {healths}")
    fails += 0 if ok else 1

    # Document comparison cardinality (two refs)
    fixtures = json.loads(
        (Path(__file__).with_name("staging_fixtures.json")).read_text(encoding="utf-8")
    )
    by_name = {f["filename"]: f["manifestKey"] for f in fixtures}
    st, body = _req(
        "POST",
        f"{BASE}/isf/execute",
        token=token,
        body={
            "skill_id": "document_comparison",
            "evidence": [
                {"evidence_type": "document_pair", "ref_id": by_name["kc028-doc-a.txt"]},
                {"evidence_type": "document_pair", "ref_id": by_name["kc028-doc-b.txt"]},
            ],
            "profile_id": "default",
        },
        timeout=120,
    )
    prop = body.get("proposal") if isinstance(body, dict) else {}
    status = str((prop or {}).get("status") or "")
    ok = st == 200 and status == "pending_approval"
    print(f"  [{'PASS' if ok else 'FAIL'}] document_comparison_vault: status={status}")
    fails += 0 if ok else 1

    print(f"fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
