#!/usr/bin/env python3
"""Run local Cobra Protocol V1 server (loopback only). No GPU required for mock mode."""

from __future__ import annotations

import logging
import os
import sys


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    if not os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip():
        print("COBRA_CORE_AUTH_SECRET is required", file=sys.stderr)
        return 2
    os.environ.setdefault("COBRA_INFERENCE_MODE", "mock")
    os.environ.setdefault("COBRA_CORE_HOST", os.environ.get("COBRA_PROTOCOL_HOST", "127.0.0.1"))
    os.environ.setdefault("COBRA_PROTOCOL_VERSION", "1")
    os.environ.setdefault("COBRA_COMPATIBILITY_VERSION", "1")

    from cobra_core.protocol_v1.cli import main as cli_main

    cli_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
