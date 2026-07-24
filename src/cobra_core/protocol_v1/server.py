"""Minimal Protocol V1 HTTP server — only /health and /v1/chat/completions."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from cobra_core.protocol_v1.config import ServerConfig, load_config
from cobra_core.protocol_v1.errors import normalized_error
from cobra_core.protocol_v1.handlers import (
    dumps,
    handle_chat_completions,
    handle_health,
    new_request_id,
)

logger = logging.getLogger("cobra_core.protocol_v1")


class ProtocolV1Handler(BaseHTTPRequestHandler):
    server_version = "CobraProtocolV1/1"
    config: ServerConfig

    def log_message(self, fmt: str, *args: Any) -> None:
        # Never log Authorization or bodies.
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, status: int, body: dict[str, Any], request_id: str) -> None:
        data = dumps(body)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("x-request-id", request_id)
        self.end_headers()
        self.wfile.write(data)

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
        path = urlparse(self.path).path
        auth = self.headers.get("Authorization")
        rid_h = self.headers.get("x-request-id")
        if path != "/health":
            rid = new_request_id(rid_h)
            self._send(
                404,
                normalized_error(code="bad_request", message="Not found", request_id=rid),
                rid,
            )
            return
        status, body, rid = handle_health(self.config, authorization=auth, request_id_header=rid_h)
        self._send(status, body, rid)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        auth = self.headers.get("Authorization")
        rid_h = self.headers.get("x-request-id")
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
        status, body, rid = handle_chat_completions(
            self.config,
            authorization=auth,
            request_id_header=rid_h,
            payload=payload,
        )
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
    if cfg.host not in {"127.0.0.1", "localhost", "::1"}:
        # Local-only guard for Phase 5B.1-CORE (no public exposure).
        raise RuntimeError("COBRA_PROTOCOL_HOST must be loopback for Phase 5B.1-CORE")

    class BoundHandler(ProtocolV1Handler):
        config = cfg

    httpd = ThreadingHTTPServer((cfg.host, cfg.port), BoundHandler)
    return httpd


def serve_forever(config: ServerConfig | None = None) -> None:
    cfg = config or load_config()
    httpd = make_server(cfg)
    logger.info(
        "Protocol V1 listening on http://%s:%s (inference_mode=%s)",
        cfg.host,
        cfg.port,
        cfg.inference_mode,
    )
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
