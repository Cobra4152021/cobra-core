#!/usr/bin/env python3
"""Minimal bitsandbytes / CUDA diagnostics without loading Qwen3-8B."""

from __future__ import annotations

import json
import traceback
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "evaluations/reports/BITSANDBYTES_WINDOWS_DIAGNOSTIC.md"
OUT_JSON = (
    ROOT / "evaluations/diagnostics/qwen3-8b-windows-load-isolation/bitsandbytes_diagnostic.json"
)


def main() -> int:
    result: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "import_status": "fail",
        "warnings": [],
        "errors": [],
    }
    try:
        result["bitsandbytes_version"] = metadata.version("bitsandbytes")
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"metadata: {exc}")

    try:
        import bitsandbytes as bnb
        import torch

        result["import_status"] = "pass"
        result["torch_version"] = torch.__version__
        result["cuda_available"] = bool(torch.cuda.is_available())
        result["torch_cuda"] = torch.version.cuda
        if torch.cuda.is_available():
            result["device_name"] = torch.cuda.get_device_name(0)
            result["compute_capability"] = ".".join(
                str(x) for x in torch.cuda.get_device_capability(0)
            )
        # Library path hints
        result["bnb_file"] = getattr(bnb, "__file__", None)
        try:
            compiled = getattr(bnb, "compiled_with_cuda", None)
            result["compiled_with_cuda"] = compiled() if callable(compiled) else compiled
        except Exception as exc:  # noqa: BLE001
            result["warnings"].append(f"compiled_with_cuda: {exc}")

        # Minimal quantized linear if CUDA available
        if torch.cuda.is_available():
            try:
                from bitsandbytes.nn import Linear4bit

                layer = Linear4bit(64, 64, bias=False, compress_statistics=True, quant_type="nf4")
                layer = layer.to("cuda")
                x = torch.randn(2, 64, device="cuda", dtype=torch.float16)
                y = layer(x)
                result["linear4bit_smoke"] = {
                    "ok": True,
                    "out_shape": list(y.shape),
                    "out_dtype": str(y.dtype),
                }
                del y, x, layer
                torch.cuda.empty_cache()
            except Exception as exc:  # noqa: BLE001
                result["linear4bit_smoke"] = {"ok": False, "error": str(exc)}
                result["errors"].append(f"linear4bit: {exc}")
        else:
            result["linear4bit_smoke"] = {"ok": False, "error": "cuda_unavailable"}
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(str(exc))
        result["traceback"] = traceback.format_exc()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    md = f"""# bitsandbytes Windows Diagnostic (Phase 3C)

**Timestamp:** {result["timestamp"]}

## Summary

| Item | Value |
| --- | --- |
| Import | `{result.get("import_status")}` |
| bitsandbytes | `{result.get("bitsandbytes_version")}` |
| torch | `{result.get("torch_version")}` |
| CUDA available | `{result.get("cuda_available")}` |
| torch CUDA | `{result.get("torch_cuda")}` |
| GPU | `{result.get("device_name")}` |
| Compute capability | `{result.get("compute_capability")}` |
| Linear4bit smoke | `{result.get("linear4bit_smoke")}` |

## Warnings

{chr(10).join(f"- {w}" for w in result.get("warnings") or []) or "- none"}

## Errors

{chr(10).join(f"- {e}" for e in result.get("errors") or []) or "- none"}

## Interpretation note

Presence of bitsandbytes does **not** prove it caused the Qwen3-8B `0xC0000005` crash.
This report only records whether the backend initializes and whether a tiny Linear4bit op succeeds.
"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "import_status": result["import_status"],
                "linear4bit": result.get("linear4bit_smoke"),
            },
            indent=2,
        )
    )
    return 0 if result["import_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
