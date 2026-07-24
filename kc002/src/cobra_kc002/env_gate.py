"""Hard environment gates for KC-002 real-weight runs."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import torch


class EnvironmentGateError(RuntimeError):
    pass


@dataclass
class EnvReport:
    python: str
    platform: str
    torch: str
    cuda_available: bool
    torch_cuda: str | None
    gpu_name: str | None
    gpu_capability: list[int] | None
    vram_gb: float | None
    min_vram_gb: float
    disk_free_gb: float | None
    allow_surrogate: bool
    bitsandbytes: str | None
    transformers: str | None
    peft: str | None
    accelerate: str | None
    flash_attn: str | None
    triton: str | None
    ok: bool
    failures: list[str]


def _pkg(name: str) -> str | None:
    try:
        mod = __import__(name)
        return getattr(mod, "__version__", "present")
    except Exception:
        return None


def collect_env(min_vram_gb: float | None = None) -> EnvReport:
    min_v = float(os.environ.get("COBRA_MIN_VRAM_GB", min_vram_gb or 20))
    allow = os.environ.get("COBRA_ALLOW_SURROGATE", "0").strip() in {"1", "true", "yes"}
    failures: list[str] = []

    cuda_ok = torch.cuda.is_available()
    torch_cuda = getattr(torch.version, "cuda", None)
    is_cpu_wheel = "cpu" in torch.__version__.lower() or torch_cuda is None

    gpu_name = None
    capability = None
    vram_gb = None
    if cuda_ok:
        gpu_name = torch.cuda.get_device_name(0)
        capability = list(torch.cuda.get_device_capability(0))
        vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)

    disk_free = None
    try:
        disk_free = round(shutil.disk_usage(Path.cwd()).free / (1024**3), 2)
    except Exception:
        pass

    require_cuda = os.environ.get("COBRA_REQUIRE_CUDA", "1").strip() not in {"0", "false", "no"}
    if require_cuda and not allow:
        if is_cpu_wheel:
            failures.append("PyTorch is CPU-only")
        if not cuda_ok:
            failures.append("CUDA unavailable")
        if vram_gb is None or vram_gb < min_v:
            failures.append(f"VRAM {vram_gb}GB < required {min_v}GB")
        if disk_free is not None and disk_free < 40:
            failures.append(f"disk free {disk_free}GB < 40GB recommended for model cache")

    return EnvReport(
        python=sys.version.split()[0],
        platform=platform.platform(),
        torch=torch.__version__,
        cuda_available=cuda_ok,
        torch_cuda=torch_cuda,
        gpu_name=gpu_name,
        gpu_capability=capability,
        vram_gb=vram_gb,
        min_vram_gb=min_v,
        disk_free_gb=disk_free,
        allow_surrogate=allow,
        bitsandbytes=_pkg("bitsandbytes"),
        transformers=_pkg("transformers"),
        peft=_pkg("peft"),
        accelerate=_pkg("accelerate"),
        flash_attn=_pkg("flash_attn"),
        triton=_pkg("triton"),
        ok=len(failures) == 0,
        failures=failures,
    )


def require_real_weight_env() -> EnvReport:
    report = collect_env()
    if not report.ok:
        raise EnvironmentGateError(
            "KC-002 environment gate failed: " + "; ".join(report.failures)
        )
    if report.allow_surrogate:
        raise EnvironmentGateError(
            "COBRA_ALLOW_SURROGATE must be 0 for KC-002 real-weight validation"
        )
    return report


def nvidia_smi_text() -> str:
    try:
        out = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.STDOUT)
        return out
    except Exception as exc:
        return f"nvidia-smi failed: {exc}"


def write_env_artifact(path: Path) -> EnvReport:
    path.parent.mkdir(parents=True, exist_ok=True)
    report = collect_env()
    payload = asdict(report)
    payload["nvidia_smi"] = nvidia_smi_text()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report
