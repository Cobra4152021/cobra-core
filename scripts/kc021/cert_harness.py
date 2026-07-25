#!/usr/bin/env python3
"""
KC-021 certification harness.

Default mode: simulated transport failures (no network, no secrets required).
Optional live mode: --live or CIAL_KC021_LIVE=1 with OPENAI_* in the environment.
Never prints API keys, prompts, or full model responses.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.cial.config import load_cial_config  # noqa: E402
from cobra_core.cial.errors import CialError, CialErrorCode  # noqa: E402
from cobra_core.cial.health import HealthState  # noqa: E402
from cobra_core.cial.providers.http_transport import HttpResponse  # noqa: E402
from cobra_core.cial.providers.openai_compatible import (  # noqa: E402
    OpenAICompatibleProvider,
    map_http_status_to_cial,
)
from cobra_core.cial.types import GenerateRequest  # noqa: E402


@dataclass
class CaseResult:
    name: str
    mode: str  # simulated | live
    ok: bool
    detail: str


class FakeTransport:
    def __init__(self, script: list[HttpResponse | Exception]) -> None:
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        self.calls.append({"method": method, "body": body})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _completion_body(content: str) -> bytes:
    return json.dumps(
        {
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }
    ).encode("utf-8")


def _safe(detail: str) -> str:
    return detail[:160]


def run_simulated() -> list[CaseResult]:
    out: list[CaseResult] = []

    t = FakeTransport([HttpResponse(200, _completion_body("ok"), {})])
    p = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t, max_retries=0)
    p.set_health(HealthState.HEALTHY)
    r = p.generate(
        GenerateRequest(messages=[{"role": "user", "content": "ping"}], max_tokens=16, model_id="m")
    )
    out.append(CaseResult("plain_text", "simulated", r.content == "ok", "completion"))

    t2 = FakeTransport([HttpResponse(200, _completion_body('{"x":1}'), {})])
    p2 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t2, max_retries=0)
    p2.set_health(HealthState.HEALTHY)
    p2.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "j"}],
            max_tokens=16,
            model_id="m",
            metadata={"json_mode": True},
        )
    )
    out.append(
        CaseResult(
            "json_mode",
            "simulated",
            b"json_object" in (t2.calls[0]["body"] or b""),
            "response_format set",
        )
    )

    out.append(
        CaseResult(
            "auth_401",
            "simulated",
            map_http_status_to_cial(401) == CialErrorCode.AUTHENTICATION_FAILED,
            "taxonomy",
        )
    )

    t3 = FakeTransport([HttpResponse(503, b"{}", {}), HttpResponse(200, _completion_body("r"), {})])
    p3 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t3, max_retries=1)
    p3.set_health(HealthState.HEALTHY)
    r3 = p3.generate(
        GenerateRequest(messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="m")
    )
    out.append(CaseResult("retry_5xx", "simulated", r3.content == "r", f"calls={len(t3.calls)}"))

    t4 = FakeTransport([HttpResponse(400, b"{}", {})])
    p4 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t4, max_retries=3)
    p4.set_health(HealthState.HEALTHY)
    try:
        p4.generate(
            GenerateRequest(messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="m")
        )
        out.append(CaseResult("non_retry_4xx", "simulated", False, "expected error"))
    except CialError as exc:
        out.append(
            CaseResult(
                "non_retry_4xx",
                "simulated",
                exc.code == CialErrorCode.INFERENCE_FAILED and len(t4.calls) == 1,
                exc.code.value,
            )
        )

    t5 = FakeTransport([HttpResponse(200, b"not-json", {})])
    p5 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t5, max_retries=0)
    p5.set_health(HealthState.HEALTHY)
    try:
        p5.generate(
            GenerateRequest(messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="m")
        )
        out.append(CaseResult("invalid_json", "simulated", False, "expected error"))
    except CialError as exc:
        out.append(
            CaseResult(
                "invalid_json",
                "simulated",
                exc.code == CialErrorCode.INVALID_RESPONSE,
                exc.code.value,
            )
        )

    t6 = FakeTransport([TimeoutError()])
    p6 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t6, max_retries=0)
    p6.set_health(HealthState.HEALTHY)
    try:
        p6.generate(
            GenerateRequest(messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="m")
        )
        out.append(CaseResult("timeout", "simulated", False, "expected error"))
    except CialError as exc:
        out.append(
            CaseResult("timeout", "simulated", exc.code == CialErrorCode.TIMEOUT, exc.code.value)
        )

    t7 = FakeTransport([OSError("boom")])
    p7 = OpenAICompatibleProvider(api_key="k", model_id="m", transport=t7, max_retries=0)
    p7.set_health(HealthState.HEALTHY)
    try:
        p7.generate(
            GenerateRequest(messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="m")
        )
        out.append(CaseResult("connection", "simulated", False, "expected error"))
    except CialError as exc:
        out.append(
            CaseResult(
                "connection",
                "simulated",
                exc.code == CialErrorCode.PROVIDER_UNAVAILABLE,
                exc.code.value,
            )
        )

    out.append(
        CaseResult(
            "model_not_found_404",
            "simulated",
            map_http_status_to_cial(404) == CialErrorCode.MODEL_NOT_FOUND,
            "taxonomy",
        )
    )

    th = FakeTransport([HttpResponse(200, b'{"data":[]}', {})])
    ph = OpenAICompatibleProvider(api_key="k", transport=th, max_retries=0)
    out.append(
        CaseResult("health_healthy", "simulated", ph.probe_health() == HealthState.HEALTHY, "probe")
    )
    return out


def run_live() -> list[CaseResult]:
    cfg = load_cial_config()
    out: list[CaseResult] = []
    if not cfg.openai_configured:
        out.append(CaseResult("live_precheck", "live", False, "OPENAI_API_KEY unset"))
        return out
    if not cfg.can_use_live_provider:
        out.append(
            CaseResult(
                "live_precheck",
                "live",
                False,
                "live gate closed (need staging + CIAL_LIVE_PROVIDER_ENABLED + openai)",
            )
        )
        return out

    provider = OpenAICompatibleProvider(
        api_key=cfg.openai_api_key,
        base_url=cfg.openai_base_url,
        model_id=cfg.openai_model,
        timeout_seconds=cfg.openai_timeout_seconds,
        max_retries=cfg.openai_max_retries,
    )
    t0 = time.perf_counter()
    health = provider.probe_health()
    latency_ms = int((time.perf_counter() - t0) * 1000)
    out.append(
        CaseResult(
            "live_health",
            "live",
            health in {HealthState.HEALTHY, HealthState.DEGRADED},
            f"state={health.value} latency_ms={latency_ms}",
        )
    )
    if health in {HealthState.UNAVAILABLE, HealthState.DISABLED}:
        return out

    try:
        result = provider.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "Reply with the single word: pong"}],
                max_tokens=8,
                model_id=cfg.openai_model,
            )
        )
        out.append(
            CaseResult(
                "live_plain_text",
                "live",
                bool(result.content),
                f"chars={len(result.content)} tokens_out={result.completion_tokens} ms={result.inference_ms}",
            )
        )
    except CialError as exc:
        out.append(CaseResult("live_plain_text", "live", False, exc.code.value))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="KC-021 CIAL certification harness")
    parser.add_argument(
        "--live", action="store_true", help="Also run live checks (requires secrets)"
    )
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    live_env = os.environ.get("CIAL_KC021_LIVE", "").strip().lower() in {"1", "true", "yes", "on"}

    results = run_simulated()
    if args.live or live_env:
        results.extend(run_live())

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    summary: dict[str, Any] = {
        "passed": passed,
        "failed": failed,
        "results": [asdict(r) for r in results],
        "note": "No secrets, prompts, or full responses included.",
    }
    print(json.dumps({"passed": passed, "failed": failed, "count": len(results)}, indent=2))
    for r in results:
        mark = "PASS" if r.ok else "FAIL"
        print(f"[{mark}] {r.mode}:{r.name} — {_safe(r.detail)}")

    if args.json_out:
        args.json_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
