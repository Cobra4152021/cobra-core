"""Collect local hardware/runtime inventory without guessing."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from cobra_core.schemas.runtime import DiskVolume, GpuDevice, RuntimeEnvironment
from cobra_core.storage.paths import get_model_home


def _pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _ram_bytes() -> tuple[int | None, int | None]:
    if os.name == "nt":
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
                return int(stat.ullTotalPhys), int(stat.ullAvailPhys)
        except Exception:
            return None, None
    return None, None


def _nvidia_smi() -> tuple[list[GpuDevice], str | None, list[str]]:
    unknowns: list[str] = []
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        unknowns.append("nvidia-smi not found")
        return [], None, unknowns
    if proc.returncode != 0:
        unknowns.append("nvidia-smi failed")
        return [], None, unknowns
    gpus: list[GpuDevice] = []
    driver: str | None = None
    for line in proc.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        idx = int(parts[0])
        name = parts[1]
        try:
            mem_mib = float(parts[2])
            mem_bytes = int(mem_mib * 1024 * 1024)
        except ValueError:
            mem_mib = None
            mem_bytes = None
        driver = parts[3]
        gpus.append(
            GpuDevice(
                index=idx,
                name=name,
                total_memory_bytes=mem_bytes,
                total_memory_mib=mem_mib,
            )
        )
    return gpus, driver, unknowns


def collect_runtime_environment(disk_path: str | Path = "D:\\") -> RuntimeEnvironment:
    """Probe the local machine and return a typed inventory."""
    unknowns: list[str] = []
    notes: list[str] = []
    path = Path(disk_path)
    usage = shutil.disk_usage(path if path.exists() else path.anchor or ".")
    fs_name: str | None = None
    large_files: bool | None = None
    large_note: str | None = None
    if os.name == "nt":
        try:
            proc = subprocess.run(
                ["fsutil", "fsinfo", "volumeinfo", str(path)[:2] + "\\"],
                check=False,
                capture_output=True,
                text=True,
            )
            for line in proc.stdout.splitlines():
                if "File System Name" in line:
                    fs_name = line.split(":")[-1].strip()
            if fs_name and fs_name.upper() in {"NTFS", "EXFAT", "REFS"}:
                large_files = True
                large_note = f"{fs_name} supports files larger than 4GB"
            elif fs_name and fs_name.upper() == "FAT32":
                large_files = False
                large_note = "FAT32 max file size is 4GB"
            else:
                unknowns.append("filesystem large-file support not fully determined")
        except Exception:
            unknowns.append("fsutil probe failed")
    else:
        unknowns.append("non-Windows filesystem large-file probe not implemented")

    gpus, driver, gpu_unknowns = _nvidia_smi()
    unknowns.extend(gpu_unknowns)
    ram_total, ram_avail = _ram_bytes()
    if ram_total is None:
        unknowns.append("RAM totals unavailable")

    torch_version = _pkg_version("torch")
    transformers_version = _pkg_version("transformers")
    cuda_available: bool | None = None
    cuda_version: str | None = None
    if torch_version:
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
            cuda_version = getattr(torch.version, "cuda", None)
        except Exception:
            unknowns.append("torch import failed while probing CUDA")
    else:
        notes.append("torch not installed at probe time")

    strategy = select_inference_strategy(
        gpu_memory_mib=gpus[0].total_memory_mib if gpus else None,
        model_bf16_memory_mib=16000.0,
    )

    strategy_notes = strategy["notes"]
    assert isinstance(strategy_notes, list)
    return RuntimeEnvironment(
        collected_at=datetime.now(UTC),
        os_name=platform.system(),
        os_version=platform.version(),
        python_version=sys.version.split()[0],
        python_executable=sys.executable,
        disk=DiskVolume(
            path=str(path),
            total_bytes=usage.total,
            free_bytes=usage.free,
            filesystem=fs_name,
            supports_large_files=large_files,
            supports_large_files_note=large_note,
        ),
        ram_total_bytes=ram_total,
        ram_available_bytes=ram_avail,
        gpu_count=len(gpus),
        gpus=gpus,
        cuda_available=cuda_available,
        cuda_version=cuda_version,
        nvidia_driver_version=driver,
        torch_version=torch_version,
        transformers_version=transformers_version,
        flash_attention_available=_pkg_version("flash-attn") is not None
        or _pkg_version("flash_attn") is not None,
        bitsandbytes_available=_pkg_version("bitsandbytes") is not None,
        accelerate_available=_pkg_version("accelerate") is not None,
        huggingface_hub_version=_pkg_version("huggingface_hub"),
        cobra_model_home=str(get_model_home()),
        selected_inference_runtime=str(strategy["runtime"]),
        selected_precision=str(strategy["precision"]),
        selection_rationale=str(strategy["rationale"]),
        unknowns=unknowns,
        notes=notes + [str(item) for item in strategy_notes],
    )


def select_inference_strategy(
    *,
    gpu_memory_mib: float | None,
    model_bf16_memory_mib: float = 16000.0,
) -> dict[str, list[str] | str]:
    """
    Choose safest initial runtime/precision for Qwen3-8B-class models.

    Prefers official Transformers artifacts. Uses load-time 4-bit when BF16
    cannot fit on the detected GPU.
    """
    notes: list[str] = []
    if gpu_memory_mib is None:
        return {
            "runtime": "transformers-cpu-or-unavailable",
            "precision": "unknown-pending-torch",
            "rationale": "No GPU memory measurement available; do not assume BF16 GPU fit.",
            "notes": notes,
        }
    if gpu_memory_mib + 512 >= model_bf16_memory_mib:
        return {
            "runtime": "transformers",
            "precision": "bf16-or-fp16",
            "rationale": "GPU memory appears sufficient for native precision.",
            "notes": notes,
        }
    notes.append(
        "Official Qwen3-8B BF16 Transformers short-context footprint is ~16GB; "
        f"detected GPU has ~{gpu_memory_mib:.0f} MiB."
    )
    notes.append(
        "Selected load-time bitsandbytes 4-bit against the official acquired BF16 "
        "checkpoint (not a third-party weight download)."
    )
    return {
        "runtime": "transformers",
        "precision": "bitsandbytes-4bit-from-official-bf16",
        "rationale": (
            "Native BF16 does not fit the detected GPU; use Transformers with "
            "bitsandbytes 4-bit on the official pinned BF16 artifacts."
        ),
        "notes": notes,
    }
