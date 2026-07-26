#!/usr/bin/env python3
"""Probe staging Computer Vault with local key (never prints the key)."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://hidden-grid-os-staging.cobra4152020.workers.dev"
UA = "CobraKC028Cert/1.0 (compatible; Mozilla/5.0)"


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
    raise SystemExit("no HIDDEN_GRID_DEV_KEY found")


def main() -> None:
    key = load_key()
    print("key_len", len(key))
    for path in ("/api/health", "/api/r2-health", "/api/files"):
        req = urllib.request.Request(
            BASE + path,
            headers={"X-Hidden-Grid-Key": key, "User-Agent": UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read(160)
                print(path, resp.status, body[:120])
        except urllib.error.HTTPError as exc:
            print(path, "HTTP", exc.code)
        except Exception as exc:  # noqa: BLE001
            print(path, type(exc).__name__)


if __name__ == "__main__":
    main()
