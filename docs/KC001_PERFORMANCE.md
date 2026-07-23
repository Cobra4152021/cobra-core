# KC-001 — Performance Profile

## Host

| Item | Value |
|------|--------|
| GPU | RTX 4070 12GB present (`nvidia-smi`) |
| PyTorch build used in KC-001 run | `2.13.0+cpu` (CUDA wheel not active in this Python env) |
| RAM | system-dependent (not exclusive) |
| OS | Windows 11 (10.0.22621) |

## Surrogate measurements

Captured via `make smoke-text`, `make smoke-vision`, `make overfit` (see `kc001/artifacts/experiments/`).

| Metric | Text-only tiny | +1 image tiny | Notes |
|--------|----------------|---------------|-------|
| Model load | &lt;1s | &lt;1s | Random init |
| Preprocess | n/a | resize 112 (surrogate) / 384 (SigLIP) | PIL |
| Encoder | n/a | stub conv → 64 tokens | Real SigLIP: 729 tokens |
| Projector | n/a | MLP | |
| Forward latency | ~33ms (2× text) | ~75ms (vision) | CPU wheel measurement |
| Overfit 80 steps | — | ~3.8s | train_acc 1.0 |
| Peak VRAM | n/a (CPU) | n/a (CPU) | Install CUDA torch for GPU profile |

## Full GPT-OSS-20B estimates (not measured here)

| Mode | VRAM (order) | Source |
|------|--------------|--------|
| MXFP4 text inference | ~16GB | OpenAI gpt-oss announcement |
| BF16 merged vision preview | ~40GB | Kaufmann model card |
| QLoRA 4-bit train + SigLIP CPU | ~24–48GB class / 128GB unified (Spark) | community |

## Batch scaling

Not profiled on real weights in KC-001. Surrogate supports batch&gt;1 in projector tests.

## Storage

| Artifact | Estimate |
|----------|----------|
| GPT-OSS-20B weights | tens of GB |
| SigLIP-SO400M | ~1–3GB |
| KC-001 code/docs | &lt;50MB |
