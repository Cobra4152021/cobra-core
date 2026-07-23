"""Schemas and helpers for Qwen3-8B Windows load isolation (Phase 3C)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[3]
DIAG_ROOT = ROOT / "evaluations/diagnostics/qwen3-8b-windows-load-isolation"
MANIFEST_PATH = ROOT / "model-cards/qwen/qwen3-8b.manifest.json"
PHASE3B_INVENTORY = ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json"

MAX_LIVE_LOAD_ATTEMPTS = 6
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
ACCESS_VIOLATION = 3221225477  # 0xC0000005

ConfigId = Literal["A", "B", "C", "D", "E", "F", "QUAL"]

CONFIGS: dict[str, dict[str, Any]] = {
    "A": {
        "name": "reproduce_known_failure",
        "quantization": "4bit-nf4-double",
        "device_map": "auto",
        "max_memory": {0: "8GiB", "cpu": "14GiB"},
        "low_cpu_mem_usage": True,
        "offload_state_dict": True,
        "generate": False,
        "live_load": True,
    },
    "B": {
        "name": "explicit_gpu_placement",
        "quantization": "4bit-nf4-double",
        "device_map": {"": 0},
        "max_memory": None,
        "low_cpu_mem_usage": True,
        "offload_state_dict": False,
        "generate": False,
        "live_load": True,
    },
    "C": {
        "name": "reduced_loader_memory_pressure",
        "quantization": "4bit-nf4-double",
        # Keep device_map=auto but remove CPU offload reservation / state-dict offload.
        "device_map": "auto",
        "max_memory": {0: "10GiB"},
        "low_cpu_mem_usage": True,
        "offload_state_dict": False,
        "generate": False,
        "live_load": True,
    },
    "D": {
        "name": "8bit_diagnostic",
        "quantization": "8bit",
        "device_map": {"": 0},
        "max_memory": None,
        "low_cpu_mem_usage": True,
        "offload_state_dict": False,
        "generate": False,
        "live_load": True,
    },
    "E": {
        "name": "cpu_metadata_and_safetensors_scan",
        "quantization": "none",
        "device_map": None,
        "generate": False,
        "live_load": False,
        "metadata_only": True,
    },
    "QUAL": {
        "name": "smoke_qualification_generation",
        "quantization": "4bit-nf4-double",
        "device_map": {"": 0},
        "max_memory": None,
        "low_cpu_mem_usage": True,
        "offload_state_dict": False,
        "generate": True,
        "live_load": True,
        "max_new_tokens": 64,
    },
}

SMOKE_PROMPT = (
    "Using only the three fictional evidence statements below, write 2-3 sentences. "
    "Cite [SRC-A], [SRC-B], or [SRC-C] for each factual claim. "
    "State one uncertainty explicitly.\n\n"
    "[SRC-A] The river gauge at Station North read 2.4 meters at 08:00.\n"
    "[SRC-B] A maintenance crew replaced the filter cartridge on 2026-03-12.\n"
    "[SRC-C] The lab notebook does not record humidity for that morning.\n"
)


def windows_status_hex(exit_code: int | None) -> str | None:
    if exit_code is None:
        return None
    if exit_code < 0:
        # Python may surface signed 32-bit
        exit_code = exit_code & 0xFFFFFFFF
    return f"0x{exit_code:08X}"


def is_access_violation(exit_code: int | None) -> bool:
    if exit_code is None:
        return False
    code = exit_code & 0xFFFFFFFF
    return code == ACCESS_VIOLATION


def system_memory() -> dict[str, Any]:
    info: dict[str, Any] = {
        "total_ram_bytes": None,
        "available_ram_bytes": None,
        "page_file_or_swap": None,
    }
    if sys.platform == "win32":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                info["total_ram_bytes"] = int(stat.ullTotalPhys)
                info["available_ram_bytes"] = int(stat.ullAvailPhys)
                info["page_file_or_swap"] = {
                    "total_page_file_bytes": int(stat.ullTotalPageFile),
                    "available_page_file_bytes": int(stat.ullAvailPageFile),
                    "commit_charge_approx_bytes": int(
                        stat.ullTotalPageFile - stat.ullAvailPageFile
                    ),
                }
        except Exception as exc:  # noqa: BLE001
            info["error"] = str(exc)
    return info


def nvidia_smi_snapshot() -> dict[str, Any]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=driver_version,name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=30,
        ).strip()
        parts = [p.strip() for p in out.split(",")]
        return {
            "raw": out,
            "driver_version": parts[0] if parts else None,
            "gpu_name": parts[1] if len(parts) > 1 else None,
            "memory_total_mib": float(parts[2]) if len(parts) > 2 else None,
            "memory_used_mib": float(parts[3]) if len(parts) > 3 else None,
            "memory_free_mib": float(parts[4]) if len(parts) > 4 else None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def attempt_schema(
    *,
    attempt_id: str,
    configuration_id: str,
    pid: int | None,
    started_at: str,
    ended_at: str | None,
    exit_code: int | None,
    load_stage: str,
    success: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "schema": "cobra.diagnostics.load_attempt.v1",
        "attempt_id": attempt_id,
        "configuration_id": configuration_id,
        "process_id": pid,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "windows_status_code": windows_status_hex(exit_code),
        "access_violation": is_access_violation(exit_code),
        "load_stage_reached": load_stage,
        "success": success,
        "benchmark_prompt_used": False,
        "benchmark_run_created": False,
    }
    if extra:
        record.update(extra)
    return record


def classify_qualification(successes: int, attempts: int = 3) -> str:
    if successes == attempts:
        return "smoke-qualified"
    if successes > 0:
        return "unstable"
    return "failed"


def count_live_loads(attempt_records: list[dict[str, Any]]) -> int:
    return sum(1 for r in attempt_records if r.get("live_load") and not r.get("metadata_only"))
