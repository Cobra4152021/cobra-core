#!/usr/bin/env python3
"""Readiness probe: authenticated GET /health (loopback)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    host = os.environ.get("COBRA_CORE_HOST") or os.environ.get("COBRA_PROTOCOL_HOST") or "127.0.0.1"
    port = os.environ.get("COBRA_CORE_PORT") or os.environ.get("COBRA_PROTOCOL_PORT") or "8080"
    token = os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip()
    if not token:
        print("COBRA_CORE_AUTH_SECRET required", file=sys.stderr)
        return 2
    url = f"http://{host}:{port}/health"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode())
    except Exception as exc:
        print(f"not_ready: {exc.__class__.__name__}", file=sys.stderr)
        return 1
    reason = body.get("reason")
    if status == 200 and reason in {"ok", "model_not_loaded", "model_unavailable"}:
        print(f"ready reason={reason}")
        return 0 if reason == "ok" else 1
    print("not_ready", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
