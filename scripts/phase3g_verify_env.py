#!/usr/bin/env python3
"""Verify cloud runtime env matches Phase 3F/3G pins (safe to run on pod or locally)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TORCH_PIN = ROOT / "evaluations/environments/cloud-qwen3-runtime/torch-pin.json"
OUT_DEFAULT = ROOT / "evaluations/diagnostics/phase-3g-p1/env-verify.json"

EXPECTED = {
    "transformers": "5.14.1",
    "accelerate": "1.14.0",
    "bitsandbytes": "0.49.2",
    "numpy": "2.5.1",
    "psutil": "7.2.2",
}


def main() -> int:
    torch_pin = json.loads(TORCH_PIN.read_text(encoding="utf-8"))
    report: dict = {
        "schema": "cobra.cloud.env_verify.v1",
        "ok": False,
        "python": sys.version.split()[0],
        "checks": {},
        "versions": {},
    }
    try:
        import accelerate
        import bitsandbytes
        import numpy
        import psutil
        import torch
        import transformers
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"{type(exc).__name__}: {exc}"
        OUT_DEFAULT.parent.mkdir(parents=True, exist_ok=True)
        OUT_DEFAULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("ENV_VERIFY_FAIL import", flush=True)
        return 2

    report["versions"] = {
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "accelerate": accelerate.__version__,
        "bitsandbytes": bitsandbytes.__version__,
        "numpy": numpy.__version__,
        "psutil": psutil.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    checks = report["checks"]
    checks["torch_pin"] = torch.__version__.startswith(torch_pin["torch"].split("+")[0])
    # Allow +cu124 suffix match
    checks["torch_exact_or_cu124"] = torch.__version__ == torch_pin["torch"] or (
        torch.__version__.startswith("2.6.0") and "cu124" in torch.__version__
    )
    for name, expected in EXPECTED.items():
        mod = {
            "transformers": transformers,
            "accelerate": accelerate,
            "bitsandbytes": bitsandbytes,
            "numpy": numpy,
            "psutil": psutil,
        }[name]
        checks[name] = mod.__version__ == expected
    checks["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        x = torch.zeros(1, device="cuda")
        checks["cuda_micro_op"] = float((x + 1).item()) == 1.0
    report["ok"] = all(bool(v) for v in checks.values())
    OUT_DEFAULT.parent.mkdir(parents=True, exist_ok=True)
    OUT_DEFAULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("ENV_VERIFY_OK" if report["ok"] else "ENV_VERIFY_FAIL", flush=True)
    print(json.dumps(report["versions"], indent=2), flush=True)
    return 0 if report["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
