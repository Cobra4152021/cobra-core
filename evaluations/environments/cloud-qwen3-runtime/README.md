# Cloud Qwen3-8B runtime (Phase 3F qualified / Phase 3G P1 hardened)

**Qualified baseline:** tag `phase-3f-qualified`  
**Phase 3G P1:** ops, pins, provisioning/cleanup tooling — **no inference behavior changes**

## Canonical files

| File | Purpose |
| --- | --- |
| `requirements-cloud-runtime.txt` | Production inference pins |
| `requirements-cloud-dev.txt` | Runtime + pytest |
| `requirements-cloud-lock.txt` | Compatibility alias (= runtime pins) |
| `torch-pin.json` | Exact torch wheel + index |
| `container-image-pin.json` | RunPod image tag + digests |
| `dependency-lock.sha256` | SHA-256 of lock files |
| `VRAM_ENVELOPE.md` | Validated ~6 GiB peak / ≥16 GB policy |
| `GPU_COST_RECOMMENDATIONS.md` | Lowest-cost supported SKUs |
| `creation-commands.md` | Reproducible bring-up |

## Operator scripts

* `scripts/phase3g_ssh_bootstrap.py`
* `scripts/phase3g_provision_preflight.py`
* `scripts/phase3g_cleanup_verify.py`
* `scripts/phase3g_verify_env.py`

CobraBench remains `prepared-not-run`. Official score remains **0.840**.
