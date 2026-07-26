#!/usr/bin/env python3
"""
KC-016 staging edge for Cobra Core RC1.

Certified Core (ec400d83…) binds loopback only. This edge:
  - starts Protocol V1 Core on 127.0.0.1
  - exposes HTTPS-facing HTTP on 0.0.0.0:$PORT (TLS terminated by Fly/proxy)
  - adds GET /version
  - enriches GET /health with ops status/version while preserving Protocol V1 fields
  - proxies /v1/chat/completions and /metrics with Bearer auth passthrough

Does not replace Computer org isolation / RBAC.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

CERTIFIED_VERSION = "v0.9.0-rc1"
CERTIFIED_REVISION = "ec400d83a9cc8105557bda2105f177cc619638b2"
# Bump when staging_edge diagnostics change — proves which image is serving.
STAGING_EDGE_BUILD = "kc028-edge-20260726a"

logger = logging.getLogger("cobra_core.staging_edge")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _prepare_core_env() -> tuple[str, int]:
    """Pin certified revision and loopback Core bind."""
    os.environ.setdefault("COBRA_INFERENCE_MODE", "mock")
    os.environ.setdefault("COBRA_PROTOCOL_VERSION", "1")
    os.environ.setdefault("COBRA_COMPATIBILITY_VERSION", "1")
    os.environ.setdefault("COBRA_CORE_METRICS_ENABLED", "true")
    os.environ.setdefault("COBRA_CORE_MAX_CONCURRENT", "2")
    os.environ.setdefault("COBRA_CORE_ENABLED", "true")
    os.environ["COBRA_CORE_REVISION"] = CERTIFIED_REVISION
    os.environ["COBRA_CORE_GIT_SHA"] = CERTIFIED_REVISION
    os.environ["COBRA_CORE_HOST"] = "127.0.0.1"
    core_port = int(_env("COBRA_CORE_INTERNAL_PORT", "18080") or "18080")
    os.environ["COBRA_CORE_PORT"] = str(core_port)
    if not _env("COBRA_CORE_AUTH_SECRET"):
        print("COBRA_CORE_AUTH_SECRET is required", file=sys.stderr)
        raise SystemExit(2)
    return "127.0.0.1", core_port


def _start_core() -> None:
    from cobra_core.protocol_v1.config import load_config
    from cobra_core.protocol_v1.server import serve_forever

    cfg = load_config()
    # Fail closed if pin drifted.
    rev = (cfg.revision or "").strip().lower()
    if not (rev == CERTIFIED_REVISION.lower() or rev.startswith(CERTIFIED_REVISION[:12].lower())):
        print(
            f"revision pin failed: configured={cfg.revision!r} required={CERTIFIED_REVISION}",
            file=sys.stderr,
        )
        raise SystemExit(3)
    serve_forever(cfg)


def _proxy(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: bytes | None = None,
    timeout: float = 120.0,
) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in headers.items():
        if v is not None:
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            out_headers = {
                "Content-Type": resp.headers.get("Content-Type") or "application/json",
                "x-request-id": resp.headers.get("x-request-id") or "",
            }
            return int(resp.status), out_headers, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        out_headers = {
            "Content-Type": exc.headers.get("Content-Type") or "application/json",
            "x-request-id": exc.headers.get("x-request-id") or "",
        }
        return int(exc.code), out_headers, raw


class StagingEdgeHandler(BaseHTTPRequestHandler):
    core_base: str = "http://127.0.0.1:18080"
    require_org_header: bool = True
    auth_secret: str = ""

    def log_message(self, fmt: str, *args: Any) -> None:
        msg = fmt % args
        if "authorization" in msg.lower() or "bearer " in msg.lower():
            msg = "[redacted]"
        logger.info("%s - %s", self.address_string(), msg)

    def _send(self, status: int, body: bytes, headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        hdrs = headers or {"Content-Type": "application/json"}
        for k, v in hdrs.items():
            if v:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, obj: dict[str, Any], request_id: str = "") -> None:
        data = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if request_id:
            headers["x-request-id"] = request_id
        self._send(status, data, headers)

    def _auth_ok(self) -> bool:
        auth = self.headers.get("Authorization") or ""
        expected = f"Bearer {self.auth_secret}"
        return bool(self.auth_secret) and auth == expected

    def _org_ok(self) -> bool:
        if not self.require_org_header:
            return True
        org = (self.headers.get("X-Cobra-Org-Id") or "").strip()
        return bool(org)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/version":
            if not self._auth_ok():
                self._send_json(
                    401,
                    {
                        "error": {
                            "code": "auth_failed",
                            "message": "Cobra Core authentication failed",
                        }
                    },
                )
                return
            self._send_json(
                200,
                {
                    "version": CERTIFIED_VERSION,
                    "revision": CERTIFIED_REVISION,
                    "branch": "kc-rc1-certification",
                    "tag": "v0.9.0-rc1",
                    "protocolVersion": "1",
                    "compatibilityVersion": "1",
                },
            )
            return

        if path in {
            "/health",
            "/metrics",
            "/air/catalog",
            "/air/audit",
            "/air/metrics",
            "/isf/skills",
            "/isf/audit",
            "/isf/metrics",
            "/rrf/audit",
            "/rrf/metrics",
        }:
            # No anonymous requests — Bearer required for all staging edge GETs.
            if not self._auth_ok():
                self._send_json(
                    401,
                    {
                        "error": {
                            "code": "auth_failed",
                            "message": "Cobra Core authentication failed",
                        },
                        "status": "unhealthy",
                        "version": CERTIFIED_VERSION,
                        "revision": CERTIFIED_REVISION,
                    },
                )
                return
            # Kill switch at edge (also enforced by Core).
            # COBRA_CORE_KILL_SWITCH=true is an explicit alias used by Cloudflare Workers vars.
            if _env("COBRA_CORE_ENABLED", "true").lower() in {"0", "false", "no", "off"} or _env(
                "COBRA_CORE_KILL_SWITCH", "false"
            ).lower() in {"1", "true", "yes", "on"}:
                self._send_json(
                    503,
                    {
                        "status": "unhealthy",
                        "version": CERTIFIED_VERSION,
                        "revision": CERTIFIED_REVISION,
                        "reason": "kill_switch",
                    },
                )
                return
            headers = {"Authorization": self.headers.get("Authorization") or ""}
            rid = self.headers.get("x-request-id")
            if rid:
                headers["x-request-id"] = rid
            # Preserve query string for /air/audit and /isf/audit.
            proxy_path = (
                self.path
                if path.startswith("/air/")
                or path.startswith("/isf/")
                or path.startswith("/rrf/")
                else path
            )
            status, resp_headers, raw = _proxy(
                "GET",
                f"{self.core_base}{proxy_path}",
                headers=headers,
                timeout=15.0,
            )
            if path == "/health" and status == 200:
                try:
                    core_body = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._send(status, raw, resp_headers)
                    return
                if not isinstance(core_body, dict):
                    self._send(status, raw, resp_headers)
                    return
                # Ops shape + Protocol V1 fields Computer expects.
                healthy = str(core_body.get("reason") or "") in {
                    "ok",
                    "model_not_loaded",
                    "model_unavailable",
                } and bool(core_body.get("authenticated"))
                # KC-021/023: safe CIAL/AIR gate visibility (no secrets / no prompts).
                cial_gate: dict[str, object] = {"error": "cial_unavailable"}
                air_gate: dict[str, object] = {"error": "air_unavailable"}
                isf_gate: dict[str, object] = {"error": "isf_unavailable"}
                rrf_gate: dict[str, object] = {"error": "rrf_unavailable"}
                kef_gate: dict[str, object] = {"error": "kef_unavailable"}
                try:
                    from cobra_core.cial.config import load_cial_config

                    cfg = load_cial_config()
                    profile = cfg.resolved_profile()
                    from cobra_core.cial.providers import openai_compatible as oai_mod
                    from cobra_core.cial.types import GenerateRequest

                    uses_mct = hasattr(oai_mod, "_uses_max_completion_tokens") and (
                        oai_mod._uses_max_completion_tokens(profile.model_id)
                    )
                    token_field = "unknown"
                    if cfg.openai_configured:
                        probe = oai_mod.OpenAICompatibleProvider(
                            api_key="probe",
                            model_id=profile.model_id,
                            base_url=cfg.openai_base_url,
                        )
                        built = probe._build_payload(
                            GenerateRequest(
                                messages=[{"role": "user", "content": "x"}],
                                max_tokens=16,
                                model_id=profile.model_id,
                            )
                        )
                        if "max_completion_tokens" in built:
                            token_field = "max_completion_tokens"
                        elif "max_tokens" in built:
                            token_field = "max_tokens"
                    cial_gate = {
                        "edgeBuild": STAGING_EDGE_BUILD,
                        "enabled": cfg.enabled,
                        "appEnv": cfg.app_env,
                        "profile": cfg.active_profile,
                        "resolvedProvider": profile.provider_id,
                        "resolvedModel": profile.model_id,
                        "liveFlag": cfg.live_provider_enabled,
                        "openaiConfigured": cfg.openai_configured,
                        "openaiBaseUrlHost": (
                            cfg.openai_base_url.split("://", 1)[-1].split("/", 1)[0]
                            if cfg.openai_base_url
                            else ""
                        ),
                        "canUseLive": cfg.can_use_live_provider,
                        "hasGpt5TokenHelper": hasattr(oai_mod, "_uses_max_completion_tokens"),
                        "usesMaxCompletionTokens": bool(uses_mct),
                        "payloadTokenField": token_field,
                    }
                    from cobra_core.air.bridge import catalog_for_config
                    from cobra_core.cial.engine import _air_enabled
                    from cobra_core.isf.enabled import isf_enabled
                    from cobra_core.isf.registry import SKILL_REGISTRY

                    air_reg = catalog_for_config(cfg)
                    air_gate = {
                        "edgeBuild": STAGING_EDGE_BUILD,
                        "airEnabled": _air_enabled(),
                        "policyId": os.environ.get("AIR_POLICY_ID", "default_v1"),
                        "excludeProviders": [
                            p.strip()
                            for p in os.environ.get("AIR_EXCLUDE_PROVIDERS", "").split(",")
                            if p.strip()
                        ],
                        "catalogProviders": [p.provider_id for p in air_reg.list_providers()],
                        "liveGateOpen": cfg.can_use_live_provider,
                        "activeProfile": cfg.active_profile,
                    }
                    isf_gate = {
                        "edgeBuild": STAGING_EDGE_BUILD,
                        "isfEnabled": isf_enabled(),
                        "skillCount": len(SKILL_REGISTRY),
                        "airEnabled": _air_enabled(),
                        "liveGateOpen": cfg.can_use_live_provider,
                        "activeProfile": cfg.active_profile,
                    }
                    from cobra_core.resilience.config import rrf_enabled

                    rrf_gate = {
                        "edgeBuild": STAGING_EDGE_BUILD,
                        "rrfEnabled": rrf_enabled(),
                        "isfEnabled": isf_enabled(),
                        "airEnabled": _air_enabled(),
                        "liveGateOpen": cfg.can_use_live_provider,
                        "activeProfile": cfg.active_profile,
                    }
                    from cobra_core.kef.config import kef_enabled
                    from cobra_core.kef.registry import CONNECTOR_REGISTRY

                    from cobra_core.kef.config import load_kef_config

                    kef_cfg = load_kef_config()
                    vault_host = ""
                    if kef_cfg.vault_base_url:
                        vault_host = kef_cfg.vault_base_url.split("://", 1)[-1].split("/", 1)[0]
                    kef_gate = {
                        "edgeBuild": STAGING_EDGE_BUILD,
                        "kefEnabled": kef_enabled(),
                        "vaultEnabled": kef_cfg.vault_enabled,
                        "allowRequestSeed": kef_cfg.allow_request_seed,
                        "vaultBaseUrlHost": vault_host,
                        "vaultTokenConfigured": bool(kef_cfg.vault_auth_token),
                        "connectors": CONNECTOR_REGISTRY.list_ids(),
                        "connectorHealth": CONNECTOR_REGISTRY.health_snapshot(),
                        "isfEnabled": isf_enabled(),
                        "airEnabled": _air_enabled(),
                        "rrfEnabled": rrf_enabled(),
                        "liveGateOpen": cfg.can_use_live_provider,
                        "activeProfile": cfg.active_profile,
                    }
                except Exception as exc:  # noqa: BLE001 — diagnostic only
                    cial_gate = {"error": type(exc).__name__}
                    air_gate = {"error": type(exc).__name__}
                    isf_gate = {"error": type(exc).__name__}
                    rrf_gate = {"error": type(exc).__name__}
                    kef_gate = {"error": type(exc).__name__}
                enriched = {
                    **core_body,
                    "status": "healthy" if healthy else "degraded",
                    "version": CERTIFIED_VERSION,
                    "revision": CERTIFIED_REVISION,
                    "gitSha": CERTIFIED_REVISION,
                    "cialGate": cial_gate,
                    "airGate": air_gate,
                    "isfGate": isf_gate,
                    "rrfGate": rrf_gate,
                    "kefGate": kef_gate,
                }
                self._send_json(200, enriched, request_id=str(enriched.get("requestId") or ""))
                return
            self._send(status, raw, resp_headers)
            return

        self._send_json(404, {"error": {"code": "bad_request", "message": "Not found"}})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/v1/chat/completions", "/air/route", "/isf/execute"}:
            self._send_json(404, {"error": {"code": "bad_request", "message": "Not found"}})
            return
        if not self._auth_ok():
            self._send_json(
                401,
                {
                    "error": {
                        "code": "auth_failed",
                        "message": "Cobra Core authentication failed",
                    }
                },
            )
            return
        if _env("COBRA_CORE_ENABLED", "true").lower() in {"0", "false", "no", "off"} or _env(
            "COBRA_CORE_KILL_SWITCH", "false"
        ).lower() in {"1", "true", "yes", "on"}:
            self._send_json(
                503,
                {
                    "error": {
                        "code": "provider_disabled",
                        "message": "Cobra Core kill switch is active",
                    }
                },
            )
            return
        if path == "/v1/chat/completions" and not self._org_ok():
            # Defense-in-depth header gate. Membership checks remain on Computer.
            self._send_json(
                403,
                {
                    "error": {
                        "code": "org_required",
                        "message": "X-Cobra-Org-Id header required for staging Core",
                    }
                },
            )
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > 2_000_000:
            self._send_json(400, {"error": {"code": "bad_request", "message": "Invalid body"}})
            return
        body = self.rfile.read(length)
        headers = {
            "Authorization": self.headers.get("Authorization") or "",
            "Content-Type": self.headers.get("Content-Type") or "application/json",
        }
        rid = self.headers.get("x-request-id")
        if rid:
            headers["x-request-id"] = rid
        org = (self.headers.get("X-Cobra-Org-Id") or "").strip()
        if org:
            headers["X-Cobra-Org-Id"] = org
        timeout_ms = int(_env("COBRA_CORE_TIMEOUT_MS", "120000") or "120000")
        status, resp_headers, raw = _proxy(
            "POST",
            f"{self.core_base}{path}",
            headers=headers,
            body=body,
            timeout=max(5.0, timeout_ms / 1000.0),
        )
        self._send(status, raw, resp_headers)

    def do_PUT(self) -> None:  # noqa: N802
        self._send_json(405, {"error": {"code": "bad_request", "message": "Method not allowed"}})

    def do_DELETE(self) -> None:  # noqa: N802
        self._send_json(405, {"error": {"code": "bad_request", "message": "Method not allowed"}})


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    host, core_port = _prepare_core_env()
    secret = _env("COBRA_CORE_AUTH_SECRET")
    require_org = _env("COBRA_CORE_REQUIRE_ORG_HEADER", "true").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }

    core_thread = threading.Thread(target=_start_core, name="protocol-v1-core", daemon=True)
    core_thread.start()

    # Wait briefly for Core loopback bind.
    import time

    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            status, _, _ = _proxy(
                "GET",
                f"http://{host}:{core_port}/health",
                headers={"Authorization": f"Bearer {secret}"},
                timeout=2.0,
            )
            if status in {200, 401, 503}:
                break
        except Exception:
            time.sleep(0.2)
    else:
        print("Core failed to become reachable on loopback", file=sys.stderr)
        return 4

    public_host = _env("COBRA_STAGING_HOST", "0.0.0.0") or "0.0.0.0"
    public_port = int(_env("PORT", _env("COBRA_STAGING_PORT", "8080")) or "8080")

    class Bound(StagingEdgeHandler):
        core_base = f"http://{host}:{core_port}"
        require_org_header = require_org
        auth_secret = secret

    httpd = ThreadingHTTPServer((public_host, public_port), Bound)
    httpd.daemon_threads = True
    logger.info(
        "staging edge listening on %s:%s (core=%s:%s revision=%s)",
        public_host,
        public_port,
        host,
        core_port,
        CERTIFIED_REVISION,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
