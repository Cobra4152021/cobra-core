"""Sample policy report extension."""

from __future__ import annotations

from typing import Any


def register() -> dict[str, Any]:
    return {
        "extension_id": "sample.policy_report.v1",
        "report_id": "policy_compliance_summary",
        "title": "Policy Compliance Summary (Demo)",
        "format": "markdown",
        "template": "# Policy Compliance\n\nStatus: {{compliance_status}}\n",
    }
