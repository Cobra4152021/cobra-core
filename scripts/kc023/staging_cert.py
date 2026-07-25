#!/usr/bin/env python3
"""
KC-023 staging certification harness.

Talks to staging Core with Bearer auth. Never prints API keys, prompts,
evidence text, or provider response bodies.

Usage:
  set CORE_AUTH from %TEMP%\\kc018-core-auth.txt
  python scripts/kc023/staging_cert.py --phase 1
  python scripts/kc023/staging_cert.py --soak 10
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

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = "https://cobra-core-staging.cobra4152020.workers.dev"
ORG = "org_staging_smoke"


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
    providers: dict[str, int] = field(default_factory=dict)
    models: dict[str, int] = field(default_factory=dict)
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
    timeout: float = 60.0,
    request_id: str | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Cobra-Org-Id": ORG,
        "Content-Type": "application/json",
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


def _safe(s: str, n: int = 120) -> str:
    return (s or "")[:n]


def phase1(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else None
    out.append(
        CaseResult(
            "health_air_enabled",
            st == 200 and isinstance(air, dict) and air.get("airEnabled") is True,
            _safe(
                json.dumps(
                    {
                        "airEnabled": (air or {}).get("airEnabled"),
                        "catalog": (air or {}).get("catalogProviders"),
                    }
                )
            ),
        )
    )
    cats = (air or {}).get("catalogProviders") if isinstance(air, dict) else None
    out.append(
        CaseResult(
            "catalog_mock_only",
            cats == ["mock"] or cats == ["mock"],
            _safe(str(cats)),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["text", "offline"], "budget": "low", "latency": "fast"},
        request_id="kc023_p1_a",
    )
    dec = body.get("decision") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "route_text_offline_mock",
            st == 200 and isinstance(dec, dict) and dec.get("selected_provider") == "mock",
            _safe(str((dec or {}).get("selected_provider"))),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["reasoning", "vision"]},
        request_id="kc023_p1_b",
    )
    err = body.get("error") if isinstance(body, dict) else None
    out.append(
        CaseResult(
            "route_vision_fail_closed",
            st == 422 and isinstance(err, dict) and err.get("code") == "no_capability_match",
            _safe(str((err or {}).get("code"))),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/v1/chat/completions",
        token=token,
        body={
            "model": "cobra-core-qwen3-8b",
            "messages": [{"role": "user", "content": "kc023 phase1 ping"}],
            "max_tokens": 16,
        },
        request_id="kc023_p1_c",
    )
    content = ""
    if isinstance(body, dict):
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    out.append(
        CaseResult(
            "completion_mock",
            st == 200 and content.startswith("[mock]"),
            f"http={st} content_prefix={_safe(content, 24)}",
        )
    )

    st, audit = _req("GET", f"{base}/air/audit?limit=20", token=token)
    entries = audit.get("entries") if isinstance(audit, dict) else []
    out.append(
        CaseResult(
            "audit_present",
            st == 200 and isinstance(entries, list) and len(entries) >= 1,
            f"count={len(entries) if isinstance(entries, list) else 0}",
        )
    )

    st, metrics = _req("GET", f"{base}/metrics", token=token)
    text = metrics if isinstance(metrics, str) else ""
    out.append(
        CaseResult(
            "metrics_air_counters",
            st == 200 and "air_routing_total" in text,
            f"http={st} has_air={'air_routing_total' in text}",
        )
    )
    return out


def phase2(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else {}
    cats = set(air.get("catalogProviders") or [])
    out.append(
        CaseResult(
            "catalog_mock_and_openai",
            cats == {"mock", "openai"},
            _safe(str(sorted(cats))),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["reasoning", "vision"], "requires_live": True},
        request_id="kc023_p2_a",
    )
    dec = body.get("decision") if isinstance(body, dict) else {}
    out.append(
        CaseResult(
            "vision_openai",
            st == 200
            and dec.get("selected_provider") == "openai"
            and dec.get("selected_model") == "gpt-5.4-mini",
            _safe(f"{dec.get('selected_provider')}/{dec.get('selected_model')}"),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["text", "offline"]},
        request_id="kc023_p2_b",
    )
    dec = body.get("decision") if isinstance(body, dict) else {}
    out.append(
        CaseResult(
            "offline_still_mock",
            st == 200 and dec.get("selected_provider") == "mock",
            _safe(str(dec.get("selected_provider"))),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={
            "profile_id": "research",
            "capabilities": ["reasoning"],
            "requires_live": True,
        },
        request_id="kc023_p2_c",
    )
    dec = body.get("decision") if isinstance(body, dict) else {}
    reason = str(dec.get("selection_reason") or "")
    out.append(
        CaseResult(
            "research_live_preferred",
            st == 200 and dec.get("selected_provider") == "openai" and "live_preferred" in reason,
            _safe(reason, 80),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["audio"]},
        request_id="kc023_p2_d",
    )
    # unknown capability → 400; unsupported registered → 422
    err = body.get("error") if isinstance(body, dict) else {}
    out.append(
        CaseResult(
            "unknown_or_unsupported_fail_closed",
            st in {400, 422} and err.get("code") in {"unknown_capability", "no_capability_match"},
            _safe(f"http={st} code={err.get('code')}"),
        )
    )

    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={
            "capabilities": ["vision", "reasoning"],
            "excluded_providers": ["openai"],
            "requires_live": True,
            "allow_offline_fallback": False,
        },
        request_id="kc023_p2_e",
    )
    err = body.get("error") if isinstance(body, dict) else {}
    out.append(
        CaseResult(
            "exclude_openai_fail_closed",
            st == 422
            and err.get("code")
            in {"policy_excluded", "no_capability_match", "live_required_unavailable"},
            _safe(str(err.get("code"))),
        )
    )
    return out


def phase7(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else {}
    cats = air.get("catalogProviders") or []
    out.append(
        CaseResult(
            "openai_removed_from_catalog",
            cats == ["mock"],
            _safe(str(cats)),
        )
    )
    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["vision"]},
        request_id="kc023_p7_vision",
    )
    err = body.get("error") if isinstance(body, dict) else {}
    out.append(
        CaseResult(
            "vision_fail_closed_after_gate_close",
            st == 422 and err.get("code") == "no_capability_match",
            _safe(str(err.get("code"))),
        )
    )
    return out


def phase8(base: str, token: str) -> list[CaseResult]:
    out: list[CaseResult] = []
    st, health = _req("GET", f"{base}/health", token=token)
    air = health.get("airGate") if isinstance(health, dict) else {}
    out.append(
        CaseResult(
            "air_disabled",
            st == 200 and air.get("airEnabled") is False,
            _safe(str(air.get("airEnabled"))),
        )
    )
    st, body = _req(
        "POST",
        f"{base}/air/route",
        token=token,
        body={"capabilities": ["text", "offline"]},
        request_id="kc023_p8_route",
    )
    out.append(
        CaseResult(
            "air_route_unavailable",
            st == 503,
            f"http={st}",
        )
    )
    st, body = _req(
        "POST",
        f"{base}/v1/chat/completions",
        token=token,
        body={
            "model": "cobra-core-qwen3-8b",
            "messages": [{"role": "user", "content": "kc023 rollback ping"}],
            "max_tokens": 16,
        },
        request_id="kc023_p8_mock",
    )
    content = ""
    if isinstance(body, dict):
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    out.append(
        CaseResult(
            "legacy_mock_completion",
            st == 200 and content.startswith("[mock]"),
            f"http={st} prefix={_safe(content, 20)}",
        )
    )
    return out


def soak(base: str, token: str, n: int) -> SoakStats:
    """Mixed workload: 40% offline, 30% reasoning, 20% vision, 10% unsupported."""
    stats = SoakStats()
    mix = (
        (["text", "offline"], "mock", False),
        (["text", "offline"], "mock", False),
        (["text", "offline"], "mock", False),
        (["text", "offline"], "mock", False),
        (["reasoning"], "openai", False),
        (["reasoning"], "openai", False),
        (["reasoning"], "openai", False),
        (["reasoning", "vision"], "openai", False),
        (["reasoning", "vision"], "openai", False),
        (["audio"], None, True),
    )
    for i in range(n):
        caps, expect_provider, expect_fail = mix[i % len(mix)]
        rid = f"kc023_soak_{n}_{i}"
        t0 = time.perf_counter()
        body_payload: dict[str, Any] = {"capabilities": caps}
        if expect_provider == "openai":
            body_payload["requires_live"] = True
        st, body = _req(
            "POST",
            f"{base}/air/route",
            token=token,
            body=body_payload,
            request_id=rid,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        stats.total += 1
        stats.latencies_ms.append(elapsed)
        if expect_fail:
            ok = st == 422 or st == 400
            if ok:
                stats.expected_failures += 1
                stats.successes += 1  # expected outcome
            else:
                stats.unexpected_failures += 1
            continue
        dec = body.get("decision") if isinstance(body, dict) else {}
        provider = dec.get("selected_provider")
        model = dec.get("selected_model")
        if st == 200 and provider == expect_provider:
            stats.successes += 1
            stats.providers[str(provider)] = stats.providers.get(str(provider), 0) + 1
            stats.models[str(model)] = stats.models.get(str(model), 0) + 1
        else:
            stats.unexpected_failures += 1
        # audit completeness
        _, audit = _req("GET", f"{base}/air/audit?correlation_id={rid}", token=token)
        entries = audit.get("entries") if isinstance(audit, dict) else []
        if isinstance(entries, list) and entries:
            stats.audit_ok += 1
    return stats


def _print_results(phase: str, results: list[CaseResult]) -> int:
    fails = 0
    print(f"\n=== {phase} ===")
    for r in results:
        mark = "PASS" if r.ok else "FAIL"
        if not r.ok:
            fails += 1
        print(f"  [{mark}] {r.name}: {r.detail}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("COBRA_CORE_BASE_URL", DEFAULT_BASE))
    ap.add_argument("--phase", type=int, choices=[1, 2, 7, 8], default=None)
    ap.add_argument("--soak", type=int, default=0, help="run soak with N requests")
    args = ap.parse_args()
    token = _load_token()
    fails = 0
    if args.phase == 1:
        fails += _print_results("PHASE 1", phase1(args.base, token))
    elif args.phase == 2:
        fails += _print_results("PHASE 2", phase2(args.base, token))
    elif args.phase == 7:
        fails += _print_results("PHASE 7", phase7(args.base, token))
    elif args.phase == 8:
        fails += _print_results("PHASE 8", phase8(args.base, token))
    if args.soak:
        stats = soak(args.base, token, args.soak)
        lats = sorted(stats.latencies_ms) or [0.0]
        p50 = lats[len(lats) // 2]
        p95 = lats[max(0, int(len(lats) * 0.95) - 1)]
        print(
            json.dumps(
                {
                    "soak_n": args.soak,
                    "total": stats.total,
                    "successes": stats.successes,
                    "expected_failures": stats.expected_failures,
                    "unexpected_failures": stats.unexpected_failures,
                    "providers": stats.providers,
                    "models": stats.models,
                    "avg_latency_ms": round(statistics.mean(lats), 3),
                    "p50_ms": round(p50, 3),
                    "p95_ms": round(p95, 3),
                    "audit_ok": stats.audit_ok,
                },
                indent=2,
            )
        )
        if stats.unexpected_failures:
            fails += stats.unexpected_failures
    if args.phase is None and not args.soak:
        ap.print_help()
        return 2
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
