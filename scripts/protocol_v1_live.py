#!/usr/bin/env python3
"""Liveness probe: TCP connect to Protocol V1 bind address."""

from __future__ import annotations

import os
import socket
import sys


def main() -> int:
    host = os.environ.get("COBRA_CORE_HOST") or os.environ.get("COBRA_PROTOCOL_HOST") or "127.0.0.1"
    port = int(os.environ.get("COBRA_CORE_PORT") or os.environ.get("COBRA_PROTOCOL_PORT") or "8080")
    try:
        with socket.create_connection((host, port), timeout=2.0):
            print(f"live {host}:{port}")
            return 0
    except OSError as exc:
        print(f"not_live: {exc.__class__.__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
