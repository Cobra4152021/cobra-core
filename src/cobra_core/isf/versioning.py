"""Skill version compatibility (semver-ish; fail closed on mismatch)."""

from __future__ import annotations

import re

from cobra_core.isf.errors import IsfError, IsfErrorCode

_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_semver(version: str) -> tuple[int, int, int]:
    raw = (version or "").strip()
    m = _SEMVER.match(raw)
    if not m:
        raise IsfError(
            IsfErrorCode.SKILL_VERSION_UNSUPPORTED,
            f"unsupported skill version format: {version!r}",
        )
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def assert_version_compatible(requested: str | None, registered: str) -> None:
    """
    Compatibility rules:
    - None / empty / '*' → accept registered version
    - Exact match → ok
    - Same major.minor, requested patch <= registered → ok
    - Otherwise → skill_version_unsupported
    """
    if requested is None or not str(requested).strip() or str(requested).strip() == "*":
        return
    req = str(requested).strip()
    if req == registered:
        return
    try:
        r_maj, r_min, r_pat = parse_semver(req)
        a_maj, a_min, a_pat = parse_semver(registered)
    except IsfError:
        raise
    if r_maj == a_maj and r_min == a_min and r_pat <= a_pat:
        return
    raise IsfError(
        IsfErrorCode.SKILL_VERSION_UNSUPPORTED,
        f"skill version {req!r} incompatible with registered {registered!r}",
    )
