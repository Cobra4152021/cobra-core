"""Minimal Protocol V1 HTTP server — only /health and /v1/chat/completions."""

from __future__ import annotations

import json
import logging
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from cobra_core.api.identity import verify_identity_assertion
from cobra_core.protocol_v1.auth import verify_bearer
from cobra_core.protocol_v1.config import ConfigError, ServerConfig, load_config
from cobra_core.protocol_v1.errors import normalized_error
from cobra_core.protocol_v1.handlers import dumps, handle_chat_completions, handle_health
from cobra_core.protocol_v1.inference_service import InferenceService
from cobra_core.protocol_v1.logging_util import log_event
from cobra_core.protocol_v1.request_id import new_request_id
from cobra_core.protocol_v1.runtime_state import RuntimeState

logger = logging.getLogger("cobra_core.protocol_v1")


class ProtocolV1Handler(BaseHTTPRequestHandler):
    server_version = "CobraProtocolV1/1"
    config: ServerConfig
    state: RuntimeState
    service: InferenceService

    def log_message(self, fmt: str, *args: Any) -> None:
        # Never log Authorization or bodies via base class access log.
        msg = fmt % args
        if "authorization" in msg.lower() or "bearer " in msg.lower():
            msg = "[redacted]"
        logger.info("%s - %s", self.address_string(), msg)

    def _send(
        self,
        status: int,
        body: dict[str, Any],
        request_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        if getattr(self, "_response_started", False):
            return
        # Client disconnect: avoid writing after cancel.
        if getattr(self, "_cancelled", False):
            return
        data = dumps(body)
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("x-request-id", request_id)
            for hk, hv in (extra_headers or {}).items():
                if hv is not None and str(hv) != "":
                    self.send_header(hk, str(hv))
            self.end_headers()
            self.wfile.write(data)
            self._response_started = True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self._cancelled = True

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        if length > 2_000_000:
            return None
        raw = self.rfile.read(length)
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(obj, dict):
            return None
        return obj

    def do_GET(self) -> None:  # noqa: N802
        self._cancelled = False
        self._response_started = False
        parsed = urlparse(self.path)
        path = parsed.path
        auth = self.headers.get("Authorization")
        rid_h = self.headers.get("x-request-id")
        if path == "/metrics":
            rid = new_request_id(rid_h)
            if not self.config.metrics_enabled:
                self._send(
                    404,
                    normalized_error(code="bad_request", message="Not found", request_id=rid),
                    rid,
                )
                return
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            text = self.service.metrics.render_prometheus().encode("utf-8")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.send_header("Content-Length", str(len(text)))
                self.send_header("x-request-id", rid)
                self.end_headers()
                self.wfile.write(text)
                self._response_started = True
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                self._cancelled = True
            return
        if path in {"/air/catalog", "/air/audit", "/air/metrics"}:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.air.http_api import (
                handle_air_audit,
                handle_air_catalog,
                handle_air_metrics_json,
            )

            if path == "/air/catalog":
                body = handle_air_catalog()
            elif path == "/air/metrics":
                body = handle_air_metrics_json()
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                limit_raw = (qs.get("limit") or ["50"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 50
                corr = (qs.get("correlation_id") or [""])[0]
                body = handle_air_audit(limit=limit, correlation_id=corr or None)
            self._send(200, body, rid)
            return
        if path in {"/rrf/audit", "/rrf/metrics"}:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.resilience.http_api import handle_rrf_audit, handle_rrf_metrics_json

            if path == "/rrf/metrics":
                body = handle_rrf_metrics_json()
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                limit_raw = (qs.get("limit") or ["50"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 50
                body = handle_rrf_audit(limit=limit)
            self._send(200, body, rid)
            return
        if path in {
            "/kef/metrics",
            "/kef/audit",
            "/kef/connectors",
            "/kef/status",
            "/kef/connectors/evidence-vault/health",
            "/kef/diagnostics",
        }:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.kef.http_api import (
                handle_kef_audit,
                handle_kef_connectors,
                handle_kef_diagnostics,
                handle_kef_metrics_json,
                handle_kef_status,
                handle_vault_health,
            )

            if path == "/kef/metrics":
                body = handle_kef_metrics_json()
            elif path == "/kef/connectors":
                body = handle_kef_connectors()
            elif path == "/kef/status":
                body = handle_kef_status()
            elif path == "/kef/connectors/evidence-vault/health":
                body = handle_vault_health()
            elif path == "/kef/diagnostics":
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                probe_key = (qs.get("manifestKey") or qs.get("probe_manifest_key") or [""])[0]
                body = handle_kef_diagnostics(probe_manifest_key=str(probe_key or ""))
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                limit_raw = (qs.get("limit") or ["50"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 50
                body = handle_kef_audit(limit=limit)
            self._send(200, body, rid)
            return
        if path in {
            "/operations/status",
            "/operations/health",
            "/operations/usage",
            "/operations/alerts",
            "/operations/feature-flags",
            "/operations/metrics",
            "/operations/audit",
        }:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.operations.http_api import (
                handle_operations_alerts,
                handle_operations_audit,
                handle_operations_feature_flags,
                handle_operations_health,
                handle_operations_metrics,
                handle_operations_status,
                handle_operations_usage,
            )

            if path == "/operations/status":
                body = handle_operations_status()
            elif path == "/operations/health":
                body = handle_operations_health()
            elif path == "/operations/usage":
                body = handle_operations_usage()
            elif path == "/operations/alerts":
                body = handle_operations_alerts()
            elif path == "/operations/feature-flags":
                body = handle_operations_feature_flags()
            elif path == "/operations/metrics":
                body = handle_operations_metrics()
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                limit_raw = (qs.get("limit") or ["50"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 50
                body = handle_operations_audit(limit=limit)
            self._send(200, body, rid)
            return
        if path in {
            "/production/status",
            "/production/health",
            "/production/diagnostics",
            "/production/startup-report",
            "/production/metrics",
            "/production/integrity",
            "/production/security-review",
            "/production/migrations/dry-run",
            "/production/audit",
        }:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.production.http_api import (
                handle_production_audit,
                handle_production_diagnostics,
                handle_production_health,
                handle_production_integrity,
                handle_production_metrics,
                handle_production_migrations_dry_run,
                handle_production_security_review,
                handle_production_startup_report,
                handle_production_status,
            )

            if path == "/production/status":
                body = handle_production_status()
            elif path == "/production/health":
                body = handle_production_health()
            elif path == "/production/diagnostics":
                body = handle_production_diagnostics()
            elif path == "/production/startup-report":
                body = handle_production_startup_report()
            elif path == "/production/metrics":
                body = handle_production_metrics()
            elif path == "/production/integrity":
                body = handle_production_integrity()
            elif path == "/production/security-review":
                body = handle_production_security_review()
            elif path == "/production/migrations/dry-run":
                body = handle_production_migrations_dry_run()
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                try:
                    limit = int((qs.get("limit") or ["50"])[0])
                except ValueError:
                    limit = 50
                body = handle_production_audit(limit=limit)
            self._send(200, body, rid)
            return
        if path.startswith("/api/"):
            rid = new_request_id(rid_h)
            authenticated = verify_bearer(auth, self.config.auth_secret)
            from cobra_core.api.router import handle_public_api

            identity = None
            if path != "/api/v1/health":
                identity = verify_identity_assertion(
                    headers={k: v for k, v in self.headers.items()},
                    secret=self.config.auth_secret,
                    method=self.command,
                    path=path,
                )
                if identity is None:
                    self._send(
                        401,
                        normalized_error(
                            code="auth_failed",
                            message="Verified identity assertion required",
                            request_id=rid,
                        ),
                        rid,
                    )
                    return
            principal = identity.principal_id if identity else ""
            org = identity.organization_id if identity else ""
            resp = handle_public_api(
                method="GET",
                path=path,
                query=parsed.query or "",
                headers={k: v for k, v in self.headers.items()},
                request_id=rid,
                authenticated=authenticated,
                identity_verified=identity is not None,
                principal_id=principal,
                organization_id=org,
            )
            body = resp.body if isinstance(resp.body, dict) else {"data": resp.body}
            self._send(resp.status, body, rid, extra_headers=resp.headers)
            return
        if path == "/organizations" or path.startswith("/organizations/"):
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.organizations.http_api import (
                handle_organization_departments,
                handle_organization_get,
                handle_organization_members,
                handle_organization_metrics,
                handle_organization_status,
                handle_organizations_list,
            )

            if path == "/organizations":
                self._send(200, handle_organizations_list(), rid)
                return
            parts = path.strip("/").split("/")
            # organizations/{id}[/{members|departments|status|metrics}]
            if len(parts) == 2:
                status, body = handle_organization_get(parts[1])
                self._send(status, body, rid)
                return
            if len(parts) == 3:
                org_id, suffix = parts[1], parts[2]
                if suffix == "members":
                    status, body = handle_organization_members(org_id)
                elif suffix == "departments":
                    status, body = handle_organization_departments(org_id)
                elif suffix == "status":
                    status, body = handle_organization_status(org_id)
                elif suffix == "metrics":
                    status, body = handle_organization_metrics(org_id)
                else:
                    self._send(
                        404,
                        normalized_error(
                            code="bad_request", message="Not found", request_id=rid
                        ),
                        rid,
                    )
                    return
                self._send(status, body, rid)
                return
            self._send(
                404,
                normalized_error(code="bad_request", message="Not found", request_id=rid),
                rid,
            )
            return
        if path in {
            "/security/status",
            "/security/roles",
            "/security/permissions",
            "/security/policies",
            "/security/sessions",
        }:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.security.http_api import (
                handle_security_permissions,
                handle_security_policies,
                handle_security_roles,
                handle_security_sessions,
                handle_security_status,
            )

            if path == "/security/status":
                body = handle_security_status()
            elif path == "/security/roles":
                body = handle_security_roles()
            elif path == "/security/permissions":
                body = handle_security_permissions()
            elif path == "/security/policies":
                body = handle_security_policies()
            else:
                body = handle_security_sessions()
            self._send(200, body, rid)
            return
        if path in {"/plugins", "/plugins/status"} or (
            path.startswith("/plugins/") and path.count("/") == 2
        ):
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.plugins.http_api import (
                handle_plugin_get,
                handle_plugins_list,
                handle_plugins_status,
            )

            if path == "/plugins":
                self._send(200, handle_plugins_list(), rid)
            elif path == "/plugins/status":
                self._send(200, handle_plugins_status(), rid)
            else:
                plugin_id = path.removeprefix("/plugins/")
                status, body = handle_plugin_get(plugin_id)
                self._send(status, body, rid)
            return
        if path in {"/isf/skills", "/isf/audit", "/isf/metrics"}:
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.isf.http_api import (
                handle_isf_audit,
                handle_isf_metrics_json,
                handle_isf_skills,
            )

            if path == "/isf/skills":
                body = handle_isf_skills()
            elif path == "/isf/metrics":
                body = handle_isf_metrics_json()
            else:
                from urllib.parse import parse_qs

                qs = parse_qs(parsed.query or "")
                limit_raw = (qs.get("limit") or ["50"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 50
                corr = (qs.get("correlation_id") or [""])[0]
                body = handle_isf_audit(limit=limit, correlation_id=corr or None)
            self._send(200, body, rid)
            return
        if path != "/health":
            rid = new_request_id(rid_h)
            self._send(
                404,
                normalized_error(code="bad_request", message="Not found", request_id=rid),
                rid,
            )
            return
        status, body, rid = handle_health(
            self.config,
            authorization=auth,
            request_id_header=rid_h,
            state=self.state,
            service=self.service,
        )
        self._send(status, body, rid)

    def do_POST(self) -> None:  # noqa: N802
        self._cancelled = False
        self._response_started = False
        path = urlparse(self.path).path
        auth = self.headers.get("Authorization")
        rid_h = self.headers.get("x-request-id")
        if path == "/air/route":
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            payload = self._read_json()
            if payload is None:
                self._send(
                    400,
                    normalized_error(
                        code="bad_request",
                        message="Malformed JSON body",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.air.http_api import handle_air_route

            status, body = handle_air_route(payload, correlation_id=rid)
            self._send(status, body, rid)
            return
        if path == "/isf/execute":
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            payload = self._read_json()
            if payload is None:
                self._send(
                    400,
                    normalized_error(
                        code="bad_request",
                        message="Malformed JSON body",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.isf.http_api import handle_isf_execute

            status, body = handle_isf_execute(payload or {}, correlation_id=rid)
            self._send(status, body, rid)
            return
        if path.startswith("/api/"):
            rid = new_request_id(rid_h)
            authenticated = verify_bearer(auth, self.config.auth_secret)
            from cobra_core.api.router import handle_public_api

            identity = None
            if path != "/api/v1/health":
                identity = verify_identity_assertion(
                    headers={k: v for k, v in self.headers.items()},
                    secret=self.config.auth_secret,
                    method=self.command,
                    path=path,
                )
                if identity is None:
                    self._send(
                        401,
                        normalized_error(
                            code="auth_failed",
                            message="Verified identity assertion required",
                            request_id=rid,
                        ),
                        rid,
                    )
                    return
            principal = identity.principal_id if identity else ""
            org = identity.organization_id if identity else ""
            payload = self._read_json() if int(self.headers.get("Content-Length") or "0") > 0 else {}
            if payload is None:
                self._send(
                    400,
                    normalized_error(
                        code="bad_request",
                        message="Malformed JSON body",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            resp = handle_public_api(
                method="POST",
                path=path,
                query=urlparse(self.path).query or "",
                headers={k: v for k, v in self.headers.items()},
                body=payload,
                request_id=rid,
                authenticated=authenticated,
                identity_verified=identity is not None,
                principal_id=principal,
                organization_id=org,
            )
            body = resp.body if isinstance(resp.body, dict) else {"data": resp.body}
            self._send(resp.status, body, rid, extra_headers=resp.headers)
            return
        if path.startswith("/plugins/") and (
            path.endswith("/enable") or path.endswith("/disable")
        ):
            rid = new_request_id(rid_h)
            if not verify_bearer(auth, self.config.auth_secret):
                self._send(
                    401,
                    normalized_error(
                        code="auth_failed",
                        message="Cobra Core authentication failed",
                        request_id=rid,
                    ),
                    rid,
                )
                return
            from cobra_core.plugins.http_api import handle_plugin_disable, handle_plugin_enable

            # Body optional — empty POST is allowed (no upload / no remote install).
            _ = self._read_json() if int(self.headers.get("Content-Length") or "0") > 0 else {}
            if path.endswith("/enable"):
                plugin_id = path.removeprefix("/plugins/").removesuffix("/enable")
                status, body = handle_plugin_enable(plugin_id, actor="admin")
            else:
                plugin_id = path.removeprefix("/plugins/").removesuffix("/disable")
                status, body = handle_plugin_disable(plugin_id, actor="admin")
            self._send(status, body, rid)
            return
        if path != "/v1/chat/completions":
            rid = new_request_id(rid_h)
            self._send(
                404,
                normalized_error(code="bad_request", message="Not found", request_id=rid),
                rid,
            )
            return
        payload = self._read_json()
        if payload is None:
            rid = new_request_id(rid_h)
            self._send(
                400,
                normalized_error(
                    code="bad_request",
                    message="Malformed JSON body",
                    request_id=rid,
                ),
                rid,
            )
            return
        cancel = threading.Event()
        status, body, rid = handle_chat_completions(
            self.config,
            authorization=auth,
            request_id_header=rid_h,
            payload=payload,
            state=self.state,
            service=self.service,
            cancel_event=cancel,
        )
        # Cancellation is cooperative via cancel_event (tests / future disconnect hooks).
        # Broken pipe on write sets _cancelled and skips a late response body.
        self._send(status, body, rid)

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        rid = new_request_id(self.headers.get("x-request-id"))
        self._send(
            405,
            normalized_error(code="bad_request", message="Method not allowed", request_id=rid),
            rid,
        )


def make_server(config: ServerConfig | None = None) -> ThreadingHTTPServer:
    cfg = config or load_config()
    if not cfg.auth_configured:
        raise ConfigError("COBRA_CORE_AUTH_SECRET is required")
    if cfg.host not in {"127.0.0.1", "localhost", "::1"}:
        # Local-only guard (no public exposure in this phase).
        raise RuntimeError("COBRA_CORE_HOST/COBRA_PROTOCOL_HOST must be loopback")

    state = RuntimeState(inference_mode=cfg.inference_mode)
    service = InferenceService(cfg, state)
    if cfg.inference_mode in {"mock", "echo", "test"}:
        state.mark_loaded()
    elif cfg.eager_load:
        try:
            service.ensure_runtime()
        except Exception:
            log_event("startup", status="model_unavailable", model=cfg.model)

    bound_cfg = cfg
    bound_state = state
    bound_service = service

    class BoundHandler(ProtocolV1Handler):
        config = bound_cfg
        state = bound_state
        service = bound_service

    httpd = ThreadingHTTPServer((cfg.host, cfg.port), BoundHandler)
    httpd.daemon_threads = True
    return httpd


def serve_forever(config: ServerConfig | None = None) -> None:
    cfg = config or load_config()
    logging.getLogger().setLevel(getattr(logging, cfg.log_level, logging.INFO))
    httpd = make_server(cfg)

    def _shutdown(signum: int, frame: Any) -> None:
        del signum, frame
        log_event("shutdown", status="graceful")
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    try:
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
    except (ValueError, OSError):
        # Signals may be unavailable on some Windows/thread contexts.
        pass

    log_event(
        "startup",
        host=cfg.host,
        port=cfg.port,
        inference_mode=cfg.inference_mode,
        protocolVersion=cfg.protocol_version,
        compatibilityVersion=cfg.compatibility_version,
        model=cfg.model,
        revision=cfg.revision,
    )
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        log_event("shutdown", status="closed")
