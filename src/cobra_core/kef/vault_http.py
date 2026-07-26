"""Minimal, bounded HTTP transport for the Computer Evidence Vault."""

from __future__ import annotations

import ipaddress
import json
import socket
from collections.abc import Mapping
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


class VaultHttpTransport(Protocol):
    def request(
        self, method: str, path: str, query: Mapping[str, str] | None, headers: Mapping[str, str]
    ) -> tuple[int, dict[str, Any] | str]: ...


class UrllibVaultTransport:
    """HTTP client which validates its fixed base URL before every request."""

    def __init__(
        self, base_url: str, *, timeout_ms: int, allow_private_hosts: bool = False
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = timeout_ms
        self.allow_private_hosts = allow_private_hosts
        self._validate_base_url()

    def _validate_base_url(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" and not self.allow_private_hosts:
            raise ValueError("Evidence Vault requires HTTPS")
        host = parsed.hostname
        if not host:
            raise ValueError("Evidence Vault URL host is required")
        if self.allow_private_hosts:
            return
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
        except socket.gaierror as exc:
            raise ValueError("Evidence Vault host cannot be resolved") from exc
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise ValueError("Evidence Vault private host is not allowed")

    def request(
        self, method: str, path: str, query: Mapping[str, str] | None, headers: Mapping[str, str]
    ) -> tuple[int, dict[str, Any] | str]:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("invalid Evidence Vault path")
        parsed = urlparse(self.base_url)
        url = urlunparse((parsed.scheme, parsed.netloc, path, "", urlencode(query or {}), ""))
        request = Request(url, method=method.upper(), headers=dict(headers))
        try:
            with urlopen(request, timeout=self.timeout_ms / 1000) as response:
                raw = response.read()
                return response.status, _decode(raw)
        except HTTPError as exc:
            return exc.code, _decode(exc.read())
        except URLError as exc:
            raise TimeoutError("Evidence Vault request failed") from exc


def _decode(raw: bytes) -> dict[str, Any] | str:
    text = raw.decode("utf-8", errors="replace")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return text
    return value if isinstance(value, dict) else text


class DeterministicVaultAdapter:
    """Fixture transport for tests; responses are keyed by ``path`` or scenario."""

    def __init__(self, scenario: str = "success", *, records: dict[str, Any] | None = None) -> None:
        self.scenario = scenario
        self.records = records or {}
        self.calls: list[tuple[str, str]] = []

    def request(
        self, method: str, path: str, query: Mapping[str, str] | None, headers: Mapping[str, str]
    ) -> tuple[int, dict[str, Any] | str]:
        self.calls.append((method, path))
        _ = (query, headers)
        if self.scenario == "timeout":
            raise TimeoutError("simulated timeout")
        status = {"401": 401, "403": 403, "429": 429, "500": 500}.get(self.scenario)
        if status:
            return status, {"error": self.scenario}
        if self.scenario == "malformed":
            return 200, "not-json"
        if path == "/api/r2-health":
            return 200, {"ok": True}
        if self.scenario == "deleted":
            return 404, {"error": "not found"}
        records = list(self.records.values())
        if self.scenario == "permission_denied":
            records = [{**r, "deny": True} for r in records]
        if self.scenario == "hash_mismatch":
            records = [{**r, "integrityState": "mismatch"} for r in records]
        if self.scenario == "duplicates" and records:
            records.append(dict(records[0]))
        if self.scenario == "oversized":
            records = [{**r, "size": 10**9} for r in records]
        if path == "/api/search":
            return 200, {"files": records}
        key = (query or {}).get("manifestKey", "")
        record = self.records.get(key)
        if record is None:
            return 404, {"error": "not found"}
        out = dict(record)
        if self.scenario == "permission_denied":
            out["deny"] = True
        if self.scenario == "hash_mismatch":
            out["integrityState"] = "mismatch"
        if self.scenario == "oversized":
            out["size"] = 10**9
        return 200, {"file": out}
