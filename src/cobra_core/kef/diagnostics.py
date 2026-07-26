"""Authenticated KEF → Evidence Vault connectivity diagnostics (no secrets/bodies)."""

from __future__ import annotations

import socket
import ssl
import time
from typing import Any
from urllib.parse import urlparse

from cobra_core.kef.config import load_kef_config
from cobra_core.kef.connectors.evidence_vault import EvidenceVaultConnector
from cobra_core.kef.registry import CONNECTOR_REGISTRY
from cobra_core.kef.vault_http import UrllibVaultTransport, vault_request_headers


def _step(name: str, status: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"step": name, "status": status}
    out.update(extra)
    return out


def run_vault_diagnostics(*, probe_manifest_key: str = "") -> dict[str, Any]:
    """
    Instrument DNS → TLS → auth → vault ops.

    Never returns tokens, full URLs with secrets, or document bodies.
    """
    cfg = load_kef_config()
    t0 = time.perf_counter()
    steps: list[dict[str, Any]] = []
    latencies: dict[str, int] = {}

    overall = "ok"
    if not cfg.enabled:
        return {
            "ok": False,
            "overall_status": "kef_disabled",
            "connector_enabled": False,
            "steps": [_step("connector", "disabled")],
            "latency_ms": 0,
        }
    if not cfg.vault_enabled:
        return {
            "ok": False,
            "overall_status": "vault_disabled",
            "connector_enabled": False,
            "steps": [_step("connector", "disabled")],
            "latency_ms": 0,
        }

    steps.append(
        _step(
            "connector",
            "ok",
            vault_enabled=True,
            token_configured=bool(cfg.vault_auth_token),
            base_host=(urlparse(cfg.vault_base_url).hostname or ""),
            timeout_ms=cfg.vault_timeout_ms,
        )
    )

    parsed = urlparse(cfg.vault_base_url)
    host = parsed.hostname or ""
    port = parsed.port or 443

    # DNS
    dns_t0 = time.perf_counter()
    ipv4: list[str] = []
    ipv6: list[str] = []
    try:
        for family, _t, _p, _c, sockaddr in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
            ip = sockaddr[0]
            if family == socket.AF_INET:
                ipv4.append(ip)
            elif family == socket.AF_INET6:
                ipv6.append(ip)
        dns_ms = int((time.perf_counter() - dns_t0) * 1000)
        latencies["dns_ms"] = dns_ms
        if not ipv4 and not ipv6:
            steps.append(_step("dns", "fail", latency_ms=dns_ms))
            overall = "fail"
        else:
            steps.append(
                _step(
                    "dns",
                    "ok",
                    latency_ms=dns_ms,
                    ipv4_count=len(set(ipv4)),
                    ipv6_count=len(set(ipv6)),
                )
            )
    except OSError as exc:
        dns_ms = int((time.perf_counter() - dns_t0) * 1000)
        latencies["dns_ms"] = dns_ms
        steps.append(_step("dns", "fail", latency_ms=dns_ms, error_type=type(exc).__name__))
        overall = "fail"

    # TLS
    tls_t0 = time.perf_counter()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=min(10.0, cfg.vault_timeout_ms / 1000)) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                tls_ms = int((time.perf_counter() - tls_t0) * 1000)
                latencies["tls_ms"] = tls_ms
                steps.append(
                    _step(
                        "tls",
                        "ok",
                        latency_ms=tls_ms,
                        version=ssock.version() or "unknown",
                        sni=host,
                    )
                )
    except OSError as exc:
        tls_ms = int((time.perf_counter() - tls_t0) * 1000)
        latencies["tls_ms"] = tls_ms
        steps.append(_step("tls", "fail", latency_ms=tls_ms, error_type=type(exc).__name__))
        overall = "fail"

    # HTTP ops via transport (auth + vault)
    transport = UrllibVaultTransport(
        cfg.vault_base_url,
        timeout_ms=cfg.vault_timeout_ms,
        allow_private_hosts=cfg.vault_allow_private_hosts,
    )
    headers = vault_request_headers(cfg.vault_auth_token)

    def probe(name: str, path: str, query: dict[str, str] | None = None) -> None:
        nonlocal overall
        op_t0 = time.perf_counter()
        try:
            status, body = transport.request("GET", path, query, headers)
            ms = int((time.perf_counter() - op_t0) * 1000)
            latencies[f"{name}_ms"] = ms
            if status == 401:
                steps.append(_step(name, "auth_fail", http_status=status, latency_ms=ms))
                overall = "fail"
            elif status == 403:
                steps.append(_step(name, "forbidden", http_status=status, latency_ms=ms))
                overall = "fail"
            elif 200 <= status < 300:
                kind = "ok"
                if isinstance(body, str) and ("Just a moment" in body or "cf-browser-verification" in body):
                    kind = "challenge"
                    overall = "fail"
                steps.append(
                    _step(
                        name,
                        kind,
                        http_status=status,
                        latency_ms=ms,
                        body_type="json" if isinstance(body, dict) else "text",
                    )
                )
            else:
                steps.append(_step(name, "http_error", http_status=status, latency_ms=ms))
                if overall == "ok":
                    overall = "degraded"
        except TimeoutError:
            ms = int((time.perf_counter() - op_t0) * 1000)
            latencies[f"{name}_ms"] = ms
            steps.append(_step(name, "timeout", latency_ms=ms))
            overall = "fail"
        except Exception as exc:  # noqa: BLE001 — diagnostic surface
            ms = int((time.perf_counter() - op_t0) * 1000)
            latencies[f"{name}_ms"] = ms
            steps.append(_step(name, "fail", latency_ms=ms, error_type=type(exc).__name__))
            overall = "fail"

    if overall != "fail" or any(s.get("step") == "tls" and s.get("status") == "ok" for s in steps):
        probe("health", "/api/r2-health")
        probe("auth", "/api/r2-health")  # same path; status encodes auth
        probe("search", "/api/search", {"q": "kc028"})
        # evidence-search requires a case scope; without one, mark skipped (not infra failure).
        steps.append(
            _step(
                "evidence_search",
                "skipped",
                reason="case_scoped_endpoint; use /api/search for global probe",
            )
        )
        if probe_manifest_key:
            # Metadata + chunk/content path use the same Vault file record endpoint
            # the connector uses for lookup/read (no separate extract required).
            probe("metadata", "/api/file", {"manifestKey": probe_manifest_key})
            probe("content", "/api/file", {"manifestKey": probe_manifest_key})
            probe("chunk", "/api/file", {"manifestKey": probe_manifest_key})
        else:
            steps.append(_step("metadata", "skipped", reason="no_probe_manifest_key"))
            steps.append(_step("content", "skipped", reason="no_probe_manifest_key"))
            steps.append(_step("chunk", "skipped", reason="no_probe_manifest_key"))

    # Compact top-level summary (KC-028.1 example shape)
    by_name = {s["step"]: s["status"] for s in steps}
    total_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "ok": overall == "ok",
        "overall_status": overall,
        "connector_enabled": True,
        "dns": by_name.get("dns", "unknown"),
        "tls": by_name.get("tls", "unknown"),
        "auth": by_name.get("auth", by_name.get("health", "unknown")),
        "authorization": by_name.get("health", "unknown"),
        "vault": by_name.get("health", "unknown"),
        "search": by_name.get("search", "unknown"),
        "evidence_search": by_name.get("evidence_search", "unknown"),
        "metadata": by_name.get("metadata", "unknown"),
        "content": by_name.get("content", "unknown"),
        "chunk_retrieval": by_name.get("chunk", "unknown"),
        "response_parsing": (
            "ok"
            if overall == "ok"
            else ("fail" if overall == "fail" else "degraded")
        ),
        "latency_ms": total_ms,
        "latencies": latencies,
        "steps": steps,
        "topology": {
            "mode": "public_https",
            "service_binding": False,
            "note": "Container egress uses public HTTPS to Computer Vault; "
            "Worker service binding is documented as optional future topology.",
        },
        "registry_health": CONNECTOR_REGISTRY.health_snapshot(),
        "connector_class": EvidenceVaultConnector.__name__,
    }
