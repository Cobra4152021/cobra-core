"""Deterministic policy engine — who may do what on which resource."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.schemas import DecisionEffect, ResourceRef, ResourceType


@dataclass(frozen=True)
class PolicyRule:
    policy_id: str
    effect: DecisionEffect
    action: str  # "*" or concrete action
    resource_type: ResourceType | str  # "*" or ResourceType
    roles: tuple[str, ...] = ()  # empty = any role (still subject to other rules)
    principal_ids: tuple[str, ...] = ()  # empty = any principal
    conditions: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    priority: int = 100  # lower evaluates first; deny rules use low priority

    def matches(
        self,
        *,
        principal_id: str,
        roles: set[str],
        action: str,
        resource: ResourceRef,
    ) -> bool:
        if self.action != "*" and self.action != action:
            return False
        rtype = (
            self.resource_type.value
            if isinstance(self.resource_type, ResourceType)
            else str(self.resource_type)
        )
        if rtype != "*" and rtype != resource.resource_type.value:
            return False
        if self.principal_ids and principal_id not in self.principal_ids:
            return False
        if self.roles and not (set(self.roles) & roles):
            return False
        # Conditions: attribute equality only (deterministic).
        for key, expected in self.conditions.items():
            if key == "resource_id":
                if resource.resource_id != expected:
                    return False
            elif resource.attributes.get(key) != expected:
                return False
        return True

    def public_dict(self) -> dict[str, Any]:
        rtype = (
            self.resource_type.value
            if isinstance(self.resource_type, ResourceType)
            else str(self.resource_type)
        )
        return {
            "policy_id": self.policy_id,
            "effect": self.effect.value,
            "action": self.action,
            "resource_type": rtype,
            "roles": list(self.roles),
            "principal_ids": list(self.principal_ids),
            "conditions": dict(self.conditions),
            "description": self.description,
            "priority": self.priority,
        }


def builtin_policies() -> list[PolicyRule]:
    """Built-in examples: investigator/run_workflow allow; reviewer approve; observer evidence deny."""
    return [
        PolicyRule(
            policy_id="pol_observer_deny_retrieve_evidence",
            effect=DecisionEffect.DENY,
            action="retrieve_evidence",
            resource_type=ResourceType.EVIDENCE,
            roles=("observer",),
            description="Observer may not retrieve evidence",
            priority=10,
        ),
        PolicyRule(
            policy_id="pol_investigator_allow_run_workflow",
            effect=DecisionEffect.ALLOW,
            action="run_workflow",
            resource_type=ResourceType.WORKFLOW,
            roles=("investigator",),
            description="Investigator may run workflows",
            priority=50,
        ),
        PolicyRule(
            policy_id="pol_reviewer_allow_approve_findings",
            effect=DecisionEffect.ALLOW,
            action="approve_findings",
            resource_type=ResourceType.FINDING,
            roles=("reviewer",),
            description="Reviewer may approve findings",
            priority=50,
        ),
        PolicyRule(
            policy_id="pol_permission_grant_allow",
            effect=DecisionEffect.ALLOW,
            action="*",
            resource_type="*",
            description="Allow when principal holds required permission (evaluated in engine)",
            priority=80,
        ),
        PolicyRule(
            policy_id="pol_owner_conditional_close_case",
            effect=DecisionEffect.CONDITIONAL,
            action="close_case",
            resource_type=ResourceType.CASE,
            roles=("investigator", "supervisor"),
            conditions={},
            description="Close case allowed if resource.owner == principal",
            priority=60,
        ),
    ]


class PolicyEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rules: list[PolicyRule] = list(builtin_policies())

    def reset_for_tests(self) -> None:
        with self._lock:
            self._rules = list(builtin_policies())

    def add_rule(self, rule: PolicyRule) -> None:
        if not rule.policy_id.strip():
            raise SecurityError(SecurityErrorCode.POLICY_INVALID, "policy_id required")
        with self._lock:
            self._rules = [r for r in self._rules if r.policy_id != rule.policy_id]
            self._rules.append(rule)
            self._rules.sort(key=lambda r: (r.priority, r.policy_id))

    def list_policies(self) -> list[dict[str, Any]]:
        with self._lock:
            rules = sorted(self._rules, key=lambda r: (r.priority, r.policy_id))
            return [r.public_dict() for r in rules]

    def matching_rules(
        self,
        *,
        principal_id: str,
        roles: set[str],
        action: str,
        resource: ResourceRef,
    ) -> list[PolicyRule]:
        with self._lock:
            rules = sorted(self._rules, key=lambda r: (r.priority, r.policy_id))
            return [
                r
                for r in rules
                if r.policy_id != "pol_permission_grant_allow"
                and r.matches(
                    principal_id=principal_id,
                    roles=roles,
                    action=action,
                    resource=resource,
                )
            ]


POLICY_ENGINE = PolicyEngine()
