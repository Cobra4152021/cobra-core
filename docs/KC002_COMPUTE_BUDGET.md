# KC-002 — Compute Budget

**Phase:** Real-weight GPT-OSS + SigLIP validation  
**Approved ceiling (initial):** 8 GPU-hours · **$100 USD** total  
**Policy:** Stop before exceeding the ceiling. Do not leave rented GPUs unattended.

---

## Limits

| Control | Value |
|---------|--------|
| Maximum hourly GPU price | **$2.50 / hr** (prefer ≤ $1.50 / hr for 24–48GB) |
| Maximum GPU hours | **8.0** |
| Maximum total compute cost | **$100** |
| Idle timeout | **15 minutes** with no active job → shut down |
| Soft warning | At **6 GPU-hours** or **$75** spent |
| Hard stop | At **8 GPU-hours** or **$100** — terminate instance |

---

## Allowed GPU targets

| Class | Examples | Use |
|-------|----------|-----|
| Minimum | RTX 3090/4090 24GB, A5000 24GB | Inference + tiny QLoRA overfit |
| Preferred | A6000 48GB, L40S 48GB, A100 40/80GB | Comfortable QLoRA + SigLIP on GPU |
| **Forbidden for full KC-002** | Local RTX 4070 **12GB** | Unit tests / docs only |

---

## Automatic shutdown procedure

1. Export `KC002_MAX_GPU_HOURS=8` and `KC002_MAX_COST_USD=100` before launch.  
2. `kc002` runners write `artifacts/kc002/<id>/cost_meter.json` every step.  
3. If projected spend ≥ ceiling, scripts call `shutdown` hook (provider-specific) and exit non-zero.  
4. Operator must verify instance termination in the provider console within 5 minutes of job end.

### Provider hooks (fill when renting)

| Provider | Shutdown command |
|----------|------------------|
| RunPod | `runpodctl remove pod <id>` |
| Lambda | Console stop / API terminate |
| Vast.ai | `vastai destroy instance <id>` |
| Manual SSH | `sudo shutdown -h now` after syncing artifacts |

---

## Checkpoint upload procedure

1. Save projector + LoRA adapters only (not base GPT-OSS / SigLIP weights).  
2. Write checksums to `artifacts/kc002/<id>/checksums.json`.  
3. Sync to approved external storage (R2 / S3 / local NAS) via `scripts/sync_artifacts.sh`.  
4. Confirm checksums locally before destroying the GPU instance.

---

## Cost log template

| Timestamp UTC | GPU | Hours Δ | Rate | Cost Δ | Cumulative | Notes |
|---------------|-----|---------|------|--------|------------|-------|
| | | | | | | |

---

## Current status

| Item | Value |
|------|--------|
| Provider selected | **None yet** — no cloud GPU credentials in environment |
| Hours used | 0 |
| Spend | $0 |
| Blocker | Need rented ≥24GB CUDA instance within budget |
