"""Reference Python SDK — authentication, pagination, typed helpers, errors."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


SDK_VERSION = "0.1.0"


class CobraApiError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        request_id: str = "",
        status: int = 400,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.request_id = request_id
        self.status = status
        self.body = body or {}


@dataclass
class Page:
    data: list[Any]
    limit: int
    cursor: str | None
    next_cursor: str | None


class CobraClient:
    """Minimal urllib-based client for /api/v1."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str,
        organization_id: str = "",
        principal_id: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.organization_id = organization_id
        self.principal_id = principal_id
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Cobra-Sdk-Version": f"python/{SDK_VERSION}",
        }
        if self.organization_id:
            h["X-Cobra-Org-Id"] = self.organization_id
        if self.principal_id:
            h["X-Cobra-Principal-Id"] = self.principal_id
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in (query or {}).items() if v is not None})
        url = f"{self.base_url}{path}"
        if qs:
            url = f"{url}?{qs}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"message": raw}
            raise CobraApiError(
                error_code=str(payload.get("error_code") or "http_error"),
                message=str(payload.get("message") or exc.reason),
                request_id=str(payload.get("request_id") or ""),
                status=exc.code,
                body=payload if isinstance(payload, dict) else {},
            ) from exc

    def _page(self, path: str, *, limit: int = 25, cursor: str | None = None) -> Page:
        body = self.request("GET", path, query={"limit": limit, "cursor": cursor})
        pag = body.get("pagination") or {}
        return Page(
            data=list(body.get("data") or []),
            limit=int(pag.get("limit") or limit),
            cursor=pag.get("cursor"),
            next_cursor=pag.get("next_cursor"),
        )

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/api/v1/health")

    def status(self) -> dict[str, Any]:
        return self.request("GET", "/api/v1/status")

    def list_organizations(self, *, limit: int = 25, cursor: str | None = None) -> Page:
        return self._page("/api/v1/organizations", limit=limit, cursor=cursor)

    def create_case(self, *, organization_id: str | None = None, **fields: Any) -> dict[str, Any]:
        payload = dict(fields)
        if organization_id or self.organization_id:
            payload.setdefault("organization_id", organization_id or self.organization_id)
        return self.request("POST", "/api/v1/cases", body=payload)

    def run_workflow(self, workflow_id: str, **fields: Any) -> dict[str, Any]:
        payload = dict(fields)
        if self.organization_id:
            payload.setdefault("organization_id", self.organization_id)
        return self.request("POST", f"/api/v1/workflows/{workflow_id}/run", body=payload)

    def retrieve_evidence(self, evidence_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/v1/evidence/{evidence_id}")

    def get_report(self, report_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/v1/reports/{report_id}")

    def openapi(self) -> dict[str, Any]:
        return self.request("GET", "/api/v1/openapi.json")
