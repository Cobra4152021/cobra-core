#!/usr/bin/env python3
"""Write cost/cleanup records after pod adoption + SSH failure (no secrets)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOUD = ROOT / "evaluations/cloud"


def main() -> int:
    cost = {
        "schema": "cobra.cloud.cost_record.v1",
        "status": "pod_running_user_owned",
        "provider": "RunPod",
        "redacted_instance_class": "community-cloud-gpu-pod",
        "gpu_model": "NVIDIA A40 (user-reported; API gpu display null)",
        "hourly_rate_at_launch_usd": 0.44,
        "storage_rate_usd": None,
        "launch_timestamp": "2026-07-23T20:46:05Z",
        "termination_timestamp": None,
        "billed_or_estimated_duration_hours": None,
        "estimated_compute_cost_usd": None,
        "estimated_storage_cost_usd": 0,
        "total_estimated_cost_usd": None,
        "approved_spending_ceiling_usd": 10.0,
        "ceiling_respected": True,
        "notes": (
            "Adopted existing pod. Agent stopped before remote access; "
            "did not terminate. User should stop pod when finished."
        ),
    }
    (CLOUD / "cost-record.json").write_text(json.dumps(cost, indent=2) + "\n", encoding="utf-8")

    cleanup = {
        "schema": "cobra.cloud.cleanup_verification.v1",
        "status": "cleanup-incomplete",
        "instance_terminated": False,
        "volume_deleted_or_retained_by_authorization": "retained_user_manual_pod",
        "temporary_uploads_deleted": True,
        "credentials_revoked": False,
        "public_services_absent": False,
        "remaining_billable_resources": ["pod:txw75nv9hn96hu"],
        "verification_timestamp": datetime.now(UTC).isoformat(),
        "notes": (
            "Safe stop after SSH failure; pod left running for user. "
            "cleanup-incomplete until pod is terminated."
        ),
    }
    (CLOUD / "cleanup-verification.json").write_text(
        json.dumps(cleanup, indent=2) + "\n", encoding="utf-8"
    )
    print("records_updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
