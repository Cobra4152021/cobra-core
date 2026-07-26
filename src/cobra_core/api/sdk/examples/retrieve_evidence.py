"""Example: Retrieve Evidence via Public API SDK."""

from __future__ import annotations

import os
import sys

from cobra_core.api.sdk.python.cobra_sdk import CobraClient


def main() -> None:
    evidence_id = sys.argv[1] if len(sys.argv) > 1 else "ev_demo"
    client = CobraClient(
        os.environ.get("COBRA_API_BASE", "http://127.0.0.1:8080"),
        token=os.environ["COBRA_CORE_AUTH_SECRET"],
        organization_id=os.environ.get("COBRA_ORG_ID", "org_demo"),
        principal_id=os.environ.get("COBRA_PRINCIPAL_ID", "user_demo"),
    )
    print(client.retrieve_evidence(evidence_id))


if __name__ == "__main__":
    main()
