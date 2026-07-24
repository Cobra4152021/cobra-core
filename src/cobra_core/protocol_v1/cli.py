"""CLI entry for Protocol V1 server."""

from __future__ import annotations

import logging
import os
import sys


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if not os.environ.get("COBRA_CORE_AUTH_SECRET", "").strip():
        print("COBRA_CORE_AUTH_SECRET is required", file=sys.stderr)
        raise SystemExit(2)
    os.environ.setdefault("COBRA_INFERENCE_MODE", "mock")
    os.environ.setdefault("COBRA_PROTOCOL_HOST", "127.0.0.1")
    from cobra_core.protocol_v1.server import serve_forever

    serve_forever()


if __name__ == "__main__":
    main()
