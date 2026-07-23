# Qwen3-8B Cloud Linux Runtime Qualification (Phase 3F)

## Windows failure history

Phases 3B–3D: full 4-bit Qwen3-8B load failed on Windows Python 3.11/3.12/3.13 with `0xC0000005` in `torch_cpu.dll`.

## WSL2 service blocker

Phase 3E Outcome E: `WSLService` Disabled (`Wsl/0x80070422`).

## Cloud authorization

**Authorized** (user chat, 2026-07-23):

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud GPU Pod |
| Primary GPU | NVIDIA L4 (1×, 24 GB VRAM) |
| Fallback GPU | NVIDIA RTX A5000 (1×) if L4 unavailable |
| System RAM | ≥ 50 GB |
| Hourly ceiling | $0.50 (L4) / $0.35 (A5000) |
| Published ref. L4 Community | **$0.44/hr** (≤ $0.50) |
| Spending ceiling | **$10.00** |
| Runtime ceiling | **8 hours** |
| Storage | ≤ 100 GB; no persistent volume beyond session |
| Region | United States preferred |
| Pricing mode | On-demand only (spot not authorized) |
| Instances | Max 1 |

## Provisioning status

**Blocked — authentication.** `RUNPOD_API_KEY` is not present in the agent environment. No pod was created. **Spend: $0.**

Price precheck (public RunPod pricing page) would allow launch of L4 Community at $0.44/hr; launch still requires live displayed-price verification at create time.

## Security / transfer / qualification

* Security manifest: authorized-not-provisioned; no ports opened; no secrets stored in repo.
* Transfer package remains ready under `artifacts/cloud-qwen3-runtime-qualification/`.
* Full-load attempts: **0**. No CobraBench.

## Cost / cleanup

* Cost record: `$0`, ceiling respected.
* Cleanup: N/A (no resources). Remaining billable resources: **none**.

## Outcome

**F — Cloud provisioning or transfer blocked** (missing RunPod API credentials).

## Next authorized phase

Provide `RUNPOD_API_KEY` to the agent environment (do not commit). Resume under the same ceilings: verify displayed hourly price → one pod → qualify only → export → terminate → confirm zero billable resources.

Official v0.1 score **0.840** unchanged. Protocol remains `prepared-not-run`.
