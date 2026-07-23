# KC-002 — Environment Report

**Branch:** `kc-002-real-weight-validation`  
**Base branch:** `kc-001-gpt-oss-vision-audit`  
**Starting commit:** `e290292ab6ac877009c7290c1a9008b467466667`  
**Recorded:** 2026-07-23  

---

## Local development host (not a KC-002 execution host)

| Field | Value |
|-------|--------|
| OS | Windows 11 (10.0.22621) |
| Python | 3.13.5 |
| NVIDIA driver | 610.74 |
| CUDA UMD (driver) | 13.3 |
| GPU | NVIDIA GeForce RTX 4070 |
| GPU VRAM | **12282 MiB (12GB)** — below 24GB minimum |
| System RAM | ~32 GB |
| Free disk (C:) | **~8.5 GB** — insufficient for GPT-OSS-20B download |
| PyTorch | `2.13.0+cpu` |
| `torch.cuda.is_available()` | **False** |
| `torch.version.cuda` | `None` |
| Transformers | 5.14.1 |
| Accelerate | 1.14.0 |
| PEFT | 0.19.1 |
| bitsandbytes | 0.49.2 |
| Triton | not installed |
| flash-attention | not installed |

### Gate results (local)

| Check | Result |
|-------|--------|
| PyTorch CUDA build | **FAIL** (CPU-only wheel) |
| CUDA available | **FAIL** |
| ≥24GB VRAM visible | **FAIL** (12GB) |
| Disk for model cache | **FAIL** (~8.5GB free) |
| bitsandbytes import | PASS (package present; CUDA ops untested) |

**Local host disposition:** Allowed for unit tests, synthetic dataset prep, docs, and surrogate regression only. **Forbidden** for KC-002 real-weight training / full GPT-OSS load.

---

## Required execution host (not yet provisioned)

| Field | Requirement |
|-------|-------------|
| GPU VRAM | ≥24GB (prefer 40–48GB) |
| PyTorch | CUDA wheel matching driver (e.g. cu124 / cu128) |
| Disk | ≥100GB free for HF cache + adapters |
| Provider | TBD within `$100` / 8h ceiling (`KC002_COMPUTE_BUDGET.md`) |

### Provisioning status

| Item | Status |
|------|--------|
| Cloud GPU credentials in environment | **None found** |
| Stripe Projects CLI | Not installed |
| RunPod / Lambda / Vast tokens | Not present |
| GPU provider selected | **None** |

---

## Validation commands (run on execution host)

```bash
python - <<'PY'
import torch, platform, sys
print("python", sys.version)
print("platform", platform.platform())
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("torch.version.cuda", torch.version.cuda)
assert torch.cuda.is_available(), "CUDA required"
print("name", torch.cuda.get_device_name(0))
print("capability", torch.cuda.get_device_capability(0))
print("vram_gb", round(torch.cuda.get_device_properties(0).total_memory/1024**3, 2))
assert torch.cuda.get_device_properties(0).total_memory >= 20 * 1024**3, "Need >=20GB visible"
PY
nvidia-smi
df -h
pip freeze > artifacts/kc002/env/requirements.freeze.txt
```

---

## Environment status for KC-002

**BLOCKED** pending rental of a ≥24GB CUDA host and installation of a CUDA PyTorch wheel there.

The `kc002` package encodes these checks and will refuse real-weight runs until they pass.
