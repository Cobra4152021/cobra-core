"""
KC-036 — Public API & SDK Framework (PASF).

Stable public integration surface under /api/v1/.
Uses existing ISPF authentication. No GraphQL/gRPC/streaming.
"""

from cobra_core.api.router import API_GATEWAY, ApiGateway, handle_public_api
from cobra_core.api.versioning import CURRENT_VERSION, ApiVersionInfo

__all__ = [
    "API_GATEWAY",
    "ApiGateway",
    "ApiVersionInfo",
    "CURRENT_VERSION",
    "handle_public_api",
]
