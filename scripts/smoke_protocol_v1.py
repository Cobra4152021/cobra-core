#!/usr/bin/env python3
"""Local Protocol V1 smoke test — mock inference, loopback only, no GPU/cloud."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

EVIDENCE = ROOT / "evaluations" / "diagnostics" / "protocol-v1-smoke"


def req(
    method: str,
    url: str,
    *,
    token: str | None,
    body: dict | None = None,
    request_id: str | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if request_id:
        headers["x-request-id"] = request_id
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:200]}
        return e.code, payload, dict(e.headers)


def main() -> int:
    os.environ["COBRA_CORE_AUTH_SECRET"] = (
        os.environ.get("COBRA_CORE_AUTH_SECRET") or "smoke-secret-protocol-v1"
    )
    os.environ["COBRA_INFERENCE_MODE"] = "mock"
    os.environ["COBRA_CORE_HOST"] = "127.0.0.1"
    os.environ["COBRA_CORE_PORT"] = os.environ.get("COBRA_CORE_PORT") or "18080"
    os.environ["COBRA_CORE_MAX_OUTPUT_TOKENS"] = "128"
    os.environ["COBRA_CORE_MAX_CONTEXT"] = "4096"
    os.environ["COBRA_CORE_TIMEOUT_MS"] = "5000"
    os.environ["COBRA_CORE_REVISION"] = "phase-5b1b-smoke"
    os.environ["COBRA_PROTOCOL_VERSION"] = "1"
    os.environ["COBRA_COMPATIBILITY_VERSION"] = "1"
    token = os.environ["COBRA_CORE_AUTH_SECRET"]

    from cobra_core.protocol_governance.schema_validate import validate_instance
    from cobra_core.protocol_v1.config import load_config
    from cobra_core.protocol_v1.server import make_server
    from cobra_core.protocol_v1.streaming import oneshot_stream_events

    cfg = load_config()
    httpd = make_server(cfg)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.15)
    base = f"http://{cfg.host}:{cfg.port}"
    results: list[tuple[str, bool, str]] = []
    schema_dir = ROOT / "protocol" / "v1" / "schemas"

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(("PASS" if ok else "FAIL"), name, detail)

    try:
        st, body, _ = req("GET", f"{base}/health", token="wrong")
        check(
            "missing_or_invalid_auth",
            st == 401 and body.get("code") == "auth_failed",
            f"status={st}",
        )

        st, body, hdrs = req("GET", f"{base}/health", token=None)
        check("missing_auth", st == 401, f"status={st}")

        st, body, hdrs = req("GET", f"{base}/health", token=token, request_id="cc_smoke_health")
        check(
            "health_ok",
            st == 200
            and body.get("protocolVersion") == "1"
            and body.get("compatibilityVersion") == "1"
            and body.get("reason") == "ok"
            and hdrs.get("x-request-id") == "cc_smoke_health",
            f"status={st}",
        )

        st, body, hdrs = req(
            "POST",
            f"{base}/v1/chat/completions",
            token=token,
            request_id="cc_smoke_complete",
            body={
                "model": "cobra-core-qwen3-8b",
                "stream": False,
                "max_tokens": 64,
                "messages": [
                    {"role": "system", "content": "Be brief."},
                    {"role": "user", "content": "ping"},
                ],
            },
        )
        text = (((body.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
        usage = body.get("usage") or {}
        latency = body.get("latency") or {}
        check(
            "completion_ok",
            st == 200 and bool(text.strip()) and usage.get("total_tokens", 0) > 0,
            f"status={st} text={text[:40]!r}",
        )
        check(
            "latency_fields",
            all(
                k in latency
                for k in ("queue_ms", "provider_latency_ms", "inference_ms", "total_ms")
            ),
            str(
                {
                    k: latency.get(k)
                    for k in ("queue_ms", "provider_latency_ms", "inference_ms", "total_ms")
                }
            ),
        )
        check("request_id_header", hdrs.get("x-request-id") == "cc_smoke_complete", "")
        check(
            "usage_fields",
            all(k in usage for k in ("prompt_tokens", "completion_tokens", "total_tokens")),
            str(usage),
        )

        # Protocol V1 streaming mode = one-shot wire + local event synthesis
        events = oneshot_stream_events(text=text, request_id="cc_smoke_complete")
        try:
            schema = json.loads(
                (schema_dir / "streaming.events.schema.json").read_text(encoding="utf-8")
            )
            validate_instance(events, schema, base_dir=schema_dir)
            check("streaming_v1_oneshot_events", True, "schema ok")
        except Exception as exc:
            check("streaming_v1_oneshot_events", False, str(exc)[:80])

        st, body, hdrs = req(
            "POST",
            f"{base}/v1/chat/completions",
            token=token,
            body={
                "model": "cobra-core-qwen3-8b",
                "stream": False,
                "max_tokens": 16,
                "messages": [{"role": "user", "content": "id"}],
            },
        )
        rid = hdrs.get("x-request-id") or body.get("requestId") or ""
        check("request_id_generated", st == 200 and str(rid).startswith("cc_"), str(rid))

        st, body, _ = req(
            "POST",
            f"{base}/v1/chat/completions",
            token=token,
            body={
                "model": "cobra-core-qwen3-8b",
                "stream": False,
                "max_tokens": 999999,
                "messages": [{"role": "user", "content": "x" * 20}],
            },
        )
        check("limits_output_cap", st == 200 and bool(body.get("choices")), f"status={st}")

        st, body, _ = req(
            "POST",
            f"{base}/v1/chat/completions",
            token=token,
            body={"model": "x", "stream": False, "max_tokens": 8, "messages": []},
        )
        check("errors_bad_request", st == 400 and body.get("code") == "bad_request", f"status={st}")
        check("safe_errors", "traceback" not in json.dumps(body).lower(), "")

        st, body, _ = req("GET", f"{base}/debug", token=token)
        check("no_debug", st == 404, f"status={st}")

    finally:
        httpd.shutdown()
        httpd.server_close()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    evidence = {
        "phase": "5B.1B",
        "mode": "mock",
        "host": "127.0.0.1",
        "results": [{"name": n, "pass": ok} for n, ok, _ in results],
        "secret_redacted": True,
    }
    (EVIDENCE / "smoke-summary.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )

    failed = [n for n, ok, _ in results if not ok]
    print("summary", f"{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
