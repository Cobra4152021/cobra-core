"""Fail-closed organization / membership validation."""

from __future__ import annotations

import re

from cobra_core.organizations.schemas import Classification, DepartmentKind, MembershipRole

_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-.]{1,63}$")


class OrganizationValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def require_id(value: str, *, field: str = "id") -> str:
    key = (value or "").strip()
    if not _ID.match(key):
        raise OrganizationValidationError("invalid_id", f"invalid {field}: {value!r}")
    return key


def require_name(value: str) -> str:
    name = (value or "").strip()
    if not name or len(name) > 200:
        raise OrganizationValidationError("invalid_name", "name required (1-200 chars)")
    return name


def parse_classification(value: str | Classification) -> Classification:
    if isinstance(value, Classification):
        return value
    try:
        return Classification(str(value).strip().lower())
    except ValueError as exc:
        raise OrganizationValidationError(
            "invalid_classification", f"unknown classification: {value!r}"
        ) from exc


def parse_department_kind(value: str | DepartmentKind) -> DepartmentKind:
    if isinstance(value, DepartmentKind):
        return value
    try:
        return DepartmentKind(str(value).strip().lower())
    except ValueError as exc:
        raise OrganizationValidationError(
            "invalid_department", f"unknown department kind: {value!r}"
        ) from exc


def parse_membership_role(value: str | MembershipRole) -> MembershipRole:
    if isinstance(value, MembershipRole):
        return value
    try:
        return MembershipRole(str(value).strip().lower())
    except ValueError as exc:
        raise OrganizationValidationError(
            "invalid_membership_role", f"unknown membership role: {value!r}"
        ) from exc
