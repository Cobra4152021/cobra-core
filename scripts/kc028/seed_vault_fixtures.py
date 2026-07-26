#!/usr/bin/env python3
"""Upload minimal KC-028 staging Evidence Vault fixtures via POST /api/upload."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

BASE = os.environ.get(
    "EVIDENCE_VAULT_BASE_URL", "https://hidden-grid-os-staging.cobra4152020.workers.dev"
)
UA = "CobraKC028Cert/1.0 (compatible; Mozilla/5.0)"

FIXTURES = [
    ("kc028-policy.txt", b"KC-028 staging policy fixture."),
    ("kc028-contract.txt", b"KC-028 staging contract fixture."),
    ("kc028-budget.csv", b"line,amount\nstaff,1000\nequip,500\n"),
    ("kc028-doc-a.txt", b"Document A for comparison."),
    ("kc028-doc-b.txt", b"Document B for comparison."),
    ("kc028-timeline.txt", b"2026-01-01 event one\n2026-01-02 event two\n"),
    ("kc028-bundle.txt", b"Mixed evidence summary source text."),
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


def multipart(filename: str, content: bytes, content_type: str) -> tuple[bytes, str]:
    boundary = f"----kc028{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def main() -> None:
    key = load_key()
    uploaded: list[dict[str, str]] = []
    for name, content in FIXTURES:
        ctype = "text/csv" if name.endswith(".csv") else "text/plain"
        raw, ct = multipart(name, content, ctype)
        req = Request(
            f"{BASE}/api/upload",
            data=raw,
            method="POST",
            headers={
                "X-Hidden-Grid-Key": key,
                "User-Agent": UA,
                "Content-Type": ct,
            },
        )
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        file_rec = data.get("file") or {}
        print("uploaded", name, file_rec.get("manifestKey"))
        uploaded.append(
            {
                "filename": name,
                "manifestKey": str(file_rec.get("manifestKey") or ""),
                "id": str(file_rec.get("id") or ""),
            }
        )
    out = Path(__file__).resolve().parent / "staging_fixtures.json"
    out.write_text(json.dumps(uploaded, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
