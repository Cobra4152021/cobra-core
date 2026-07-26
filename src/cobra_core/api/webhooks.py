"""Webhook framework reserved — no delivery implementation (KC-036)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class WebhookEvent(StrEnum):
    CASE_CREATED = "case.created"
    WORKFLOW_COMPLETED = "workflow.completed"
    FINDING_APPROVED = "finding.approved"


RESERVED_EVENTS: tuple[str, ...] = tuple(e.value for e in WebhookEvent)


def webhook_catalog() -> dict[str, Any]:
    return {
        "status": "reserved",
        "delivery": False,
        "events": list(RESERVED_EVENTS),
        "note": "Webhook delivery is out of scope for KC-036; event names are reserved.",
    }
