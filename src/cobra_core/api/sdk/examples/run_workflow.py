"""Example: Run Workflow via Public API SDK."""

from __future__ import annotations

import os

from cobra_core.api.sdk.python.cobra_sdk import CobraClient


def main() -> None:
    client = CobraClient(
        os.environ.get("COBRA_API_BASE", "http://127.0.0.1:8080"),
        token=os.environ["COBRA_CORE_AUTH_SECRET"],
        organization_id=os.environ.get("COBRA_ORG_ID", "org_demo"),
        principal_id=os.environ.get("COBRA_PRINCIPAL_ID", "user_demo"),
    )
    print(client.run_workflow("default"))


if __name__ == "__main__":
    main()
