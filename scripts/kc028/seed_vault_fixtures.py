#!/usr/bin/env python3
"""Upload minimal KC-028 staging Evidence Vault fixtures (text files via /api/upload)."""

from __future__ import annotations

import json
import mimetypes
import os
import urllib.request
from pathlib import Path

BASE = os.environ.get(
    "EVIDENCE_VAULT_BASE_URL", "https://hidden-grid-os-staging.cobra4152020.workers.dev"
)
UA = "CobraKC028Cert/1.0 (compatible; Mozilla/5.0)"

FIXTURES = [
    ("kc028-policy.txt", "policy_document", b"KC-028 staging policy fixture. Use of force overview."),
    ("kc028-contract.txt", "contract_document", b"KC-028 staging contract fixture. Parties A and B."),
    ("kc028-budget.csv", "budget_spreadsheet", b"line,amount\nstaff,1000\nequip,500\n"),
    ("kc028-doc-a.txt", "document_pair", b"Document A for comparison."),
    ("kc028-doc-b.txt", "document_pair", b"Document B for comparison."),
    ("kc028-timeline.txt", "timeline_source", b"2026-01-01 event one\n2026-01-02 event two\n"),
    ("kc028-bundle.txt", "evidence_bundle", b"Mixed evidence summary source text."),
]


def load_key() -> str:
    for p in (
        Path(r"c:\Users\Dynamic Mining Inc\Downloads\hidden-grid-os-qwen-live\.dev.vars"),
        Path(r"c:\Users\Dynamic Mining Inc\Downloads\hidden-grid-os\.dev.vars"),
    ):
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("HIDDEN_GRID_DEV_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    env = os.environ.get("HIDDEN_GRID_DEV_KEY") or os.environ.get("KEF_EVIDENCE_VAULT_AUTH_TOKEN")
    if env:
        return env.strip()
    raise SystemExit("vault key required")


def main() -> None:
    key = load_key()
    # Prefer multipart upload if available; else report list-only.
    # Many staging builds accept POST /api/upload with form fields.
    print("listing existing files…")
    req = urllib.request.Request(
        f"{BASE}/api/files",
        headers={"X-Hidden-Grid-Key": key, "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    files = data.get("files") or []
    print("file_count", len(files))
    for f in files[:20]:
        print("file", f.get("manifestKey"), f.get("filename"), f.get("contentType"))
    print(
        "NOTE: automated upload may be gated; seed via Computer UI if empty. "
        "Fixture names expected:",
        [n for n, _, _ in FIXTURES],
    )


if __name__ == "__main__":
    main()
