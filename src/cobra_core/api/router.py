"""
Public API Gateway — /api/v1/*

Client → Public REST API → API Gateway → ISPF Authorization → subsystems
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

from cobra_core.api.audit import API_AUDIT
from cobra_core.api.config import ApiConfig, load_api_config
from cobra_core.api.errors import ApiError, ApiErrorCode, error_response
from cobra_core.api.metrics import API_METRICS
from cobra_core.api.openapi import build_openapi_document
from cobra_core.api import resources
from cobra_core.api.rate_limit import RATE_LIMITER, RateLimiter
from cobra_core.api.versioning import (
    CURRENT_VERSION,
    is_supported_version,
    parse_api_version,
    version_prefix,
)


@dataclass
class ApiRequest:
    method: str
    path: str
    query: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    request_id: str = ""
    authenticated: bool = False
    principal_id: str = ""
    organization_id: str = ""
    api_client_id: str = ""


@dataclass
class ApiResponse:
    status: int
    body: dict[str, Any] | list[Any] | str
    headers: dict[str, str] = field(default_factory=dict)


Handler = Callable[[ApiRequest], dict[str, Any]]


class ApiGateway:
    def __init__(
        self,
        *,
        config: ApiConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.config = config or load_api_config()
        self.rate_limiter = rate_limiter if rate_limiter is not None else RATE_LIMITER
        if config is not None:
            self.rate_limiter.org_limit = config.org_rate_limit
            self.rate_limiter.client_limit = config.client_rate_limit
            self.rate_limiter.window_seconds = config.rate_window_seconds

    def reset_for_tests(self) -> None:
        self.config = load_api_config()
        self.rate_limiter.reset_for_tests()
        API_METRICS.clear()
        API_AUDIT.clear()

    def dispatch(self, request: ApiRequest) -> ApiResponse:
        t0 = time.perf_counter()
        extra_headers: dict[str, str] = {}
        sdk_ver = request.headers.get("x-cobra-sdk-version") or request.headers.get(
            "X-Cobra-Sdk-Version"
        )
        if sdk_ver:
            API_METRICS.record_sdk_version(sdk_ver)

        try:
            if not self.config.enabled:
                raise ApiError(ApiErrorCode.FORBIDDEN, "Public API disabled", status=503)

            version = parse_api_version(request.path)
            if version is None:
                raise ApiError(ApiErrorCode.NOT_FOUND, "Not found", status=404)
            if not is_supported_version(version):
                raise ApiError(
                    ApiErrorCode.VERSION_UNSUPPORTED,
                    f"unsupported API version: {version}",
                    status=400,
                )

            prefix = version_prefix(version)
            rel = request.path[len(prefix) :] or "/"
            if not rel.startswith("/"):
                rel = "/" + rel

            # Health is public (still counted)
            needs_auth = rel != "/health"
            if needs_auth and not request.authenticated:
                raise ApiError(
                    ApiErrorCode.UNAUTHENTICATED,
                    "Bearer authentication required",
                    status=401,
                )

            org_id = (
                request.organization_id
                or request.headers.get("x-cobra-org-id")
                or request.headers.get("X-Cobra-Org-Id")
                or ""
            ).strip()
            client_id = (
                request.api_client_id
                or request.principal_id
                or request.headers.get("x-cobra-api-client")
                or ""
            ).strip()

            if needs_auth:
                try:
                    rl = self.rate_limiter.check(
                        organization_id=org_id or "_none",
                        api_client_id=client_id or "_none",
                    )
                    extra_headers.update(rl.headers())
                except ApiError:
                    API_METRICS.record_rate_limit()
                    raise

            body = self._route(request, rel=rel, organization_id=org_id)
            latency = (time.perf_counter() - t0) * 1000
            API_METRICS.record_request(latency_ms=latency, error=False)
            API_AUDIT.record(
                api_client=client_id or "anonymous",
                organization_id=org_id,
                endpoint=f"{request.method} {request.path}",
                result="ok",
                latency_ms=latency,
                authorization=str((body or {}).get("authorization") or ""),
                request_id=request.request_id,
            )
            return ApiResponse(status=200, body=body, headers=extra_headers)

        except ApiError as exc:
            latency = (time.perf_counter() - t0) * 1000
            API_METRICS.record_request(latency_ms=latency, error=True)
            if exc.error_code == ApiErrorCode.RATE_LIMITED:
                API_METRICS.record_rate_limit()
                if exc.details:
                    extra_headers.setdefault(
                        "X-RateLimit-Limit", str(exc.details.get("limit", ""))
                    )
                    extra_headers.setdefault(
                        "X-RateLimit-Reset", str(exc.details.get("reset", ""))
                    )
                    extra_headers.setdefault("X-RateLimit-Remaining", "0")
            API_AUDIT.record(
                api_client=request.api_client_id or request.principal_id or "anonymous",
                organization_id=request.organization_id,
                endpoint=f"{request.method} {request.path}",
                result=exc.error_code.value,
                latency_ms=latency,
                authorization="",
                request_id=request.request_id,
            )
            exc.request_id = request.request_id or exc.request_id
            return ApiResponse(
                status=exc.status,
                body=exc.public_dict(),
                headers=extra_headers,
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - t0) * 1000
            API_METRICS.record_request(latency_ms=latency, error=True)
            status, body = error_response(
                error_code=ApiErrorCode.INTERNAL_ERROR,
                message="internal error",
                request_id=request.request_id,
                status=500,
                details={"type": type(exc).__name__},
            )
            return ApiResponse(status=status, body=body, headers=extra_headers)

    def _route(
        self, request: ApiRequest, *, rel: str, organization_id: str
    ) -> dict[str, Any]:
        method = request.method.upper()
        principal = request.principal_id or "sys_cobra"

        if rel == "/health" and method == "GET":
            return resources.handle_health()
        if rel == "/status" and method == "GET":
            return resources.handle_status()
        if rel == "/openapi.json" and method == "GET":
            return build_openapi_document()

        if rel == "/organizations" and method == "GET":
            return resources.handle_organizations_list(query=request.query)
        if rel.startswith("/organizations/") and method == "GET":
            org_id = rel.removeprefix("/organizations/").split("/")[0]
            return resources.handle_organization_get(org_id)

        if rel == "/cases" and method == "GET":
            return resources.handle_cases_list(
                query=request.query, organization_id=organization_id
            )
        if rel == "/cases" and method == "POST":
            return resources.handle_case_create(
                request.body,
                principal_id=principal,
                organization_id=organization_id,
            )
        if rel.startswith("/cases/") and method == "GET":
            case_id = rel.removeprefix("/cases/").split("/")[0]
            return resources.handle_case_get(case_id)

        if rel == "/workflows" and method == "GET":
            return resources.handle_workflows_list(
                query=request.query, organization_id=organization_id
            )
        if rel.startswith("/workflows/") and rel.endswith("/run") and method == "POST":
            mid = rel.removeprefix("/workflows/").removesuffix("/run")
            return resources.handle_workflow_run(
                mid,
                request.body,
                principal_id=principal,
                organization_id=organization_id,
            )

        if rel == "/evidence" and method == "GET":
            return resources.handle_evidence_list(
                query=request.query, organization_id=organization_id
            )
        if rel.startswith("/evidence/") and method == "GET":
            eid = rel.removeprefix("/evidence/").split("/")[0]
            return resources.handle_evidence_get(
                eid, principal_id=principal, organization_id=organization_id
            )

        if rel == "/plugins" and method == "GET":
            return resources.handle_plugins_list(query=request.query)
        if rel == "/benchmark/datasets" and method == "GET":
            return resources.handle_benchmark_datasets(query=request.query)
        if rel == "/operations/status" and method == "GET":
            return resources.handle_operations_status()
        if rel == "/security/status" and method == "GET":
            return resources.handle_security_status()
        if rel.startswith("/reports/") and method == "GET":
            rid = rel.removeprefix("/reports/").split("/")[0]
            return resources.handle_report_get(rid)

        raise ApiError(ApiErrorCode.NOT_FOUND, "Not found", status=404)


API_GATEWAY = ApiGateway()


def handle_public_api(
    *,
    method: str,
    path: str,
    query: str = "",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    request_id: str = "",
    authenticated: bool = False,
    principal_id: str = "",
    organization_id: str = "",
) -> ApiResponse:
    req = ApiRequest(
        method=method,
        path=urlparse(path).path if "://" in path else path.split("?")[0],
        query=query,
        headers={k: v for k, v in (headers or {}).items()},
        body=body,
        request_id=request_id,
        authenticated=authenticated,
        principal_id=principal_id,
        organization_id=organization_id,
        api_client_id=principal_id,
    )
    return API_GATEWAY.dispatch(req)
