#!/usr/bin/env python3
"""Run local Cobra Protocol V1 server (loopback only). No GPU required for mock mode."""

from __future__ import annotations

import logging
import os
import sys


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # Ensure src on path when run as script without install.
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    if not os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip():
        print("COBRA_CORE_AUTH_SECRET is required", file=sys.stderr)
        return 2
    os.environ.setdefault("COBRA_INFERENCE_MODE", "mock")
    os.environ.setdefault("COBRA_PROTOCOL_HOST", "127.0.0.1")

    from cobra_core.protocol_v1.server import serve_forever

    serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
