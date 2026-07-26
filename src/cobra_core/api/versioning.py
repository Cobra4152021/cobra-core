"""API versioning — public surface lives under /api/vN/."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CURRENT_VERSION = "v1"
SUPPORTED_VERSIONS: tuple[str, ...] = ("v1",)
# Breaking changes require a new major version path (v2, …). No silent breaks.
DEPRECATED_VERSIONS: tuple[str, ...] = ()

API_PREFIX = "/api"
STABILITY = "stable"  # v1 stability guarantee for documented endpoints


@dataclass(frozen=True)
class ApiVersionInfo:
    current: str = CURRENT_VERSION
    supported: tuple[str, ...] = SUPPORTED_VERSIONS
    deprecated: tuple[str, ...] = DEPRECATED_VERSIONS
    stability: str = STABILITY
    deprecation_policy: str = (
        "Breaking changes require a new major version (e.g. /api/v2/). "
        "Deprecated versions remain available for at least one minor release cycle "
        "with documented migration notes. No silent breaking changes in a version."
    )

    def public_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "supported": list(self.supported),
            "deprecated": list(self.deprecated),
            "stability": self.stability,
            "deprecation_policy": self.deprecation_policy,
        }


def parse_api_version(path: str) -> str | None:
    """Return version segment if path starts with /api/vN/, else None."""
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api" and parts[1].startswith("v"):
        return parts[1]
    return None


def is_supported_version(version: str) -> bool:
    return version in SUPPORTED_VERSIONS


def version_prefix(version: str = CURRENT_VERSION) -> str:
    return f"{API_PREFIX}/{version}"
