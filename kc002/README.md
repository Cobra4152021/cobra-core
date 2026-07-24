# KC-002 — Real-Weight Native Vision Validation

Validates King Cobra native vision on **real** `openai/gpt-oss-20b` + `google/siglip-so400m-patch14-384` weights.

## Hard rules

- `COBRA_ALLOW_SURROGATE=0` (default): surrogate Tiny MoE paths are **rejected**.
- Requires CUDA + ≥20GB visible VRAM (policy target ≥24GB).
- Does not commit weights.
- Does not use LLaVA / Infinity-MM / scraped sets.

## Quick start (on a rented ≥24GB GPU)

```bash
# Install CUDA PyTorch first (example cu124):
pip install torch --index-url https://download.pytorch.org/whl/cu124

cd kc002
cp .env.example .env
make setup
make validate-env   # must pass
make text-baseline
make siglip
make forward-gate   # mandatory gate
make overfit
make dependence
make regression
make moe
```

## Local 12GB machine

```bash
make test   # unit tests only (no real weights)
```

Do **not** run `forward-gate` / `overfit` on RTX 4070 12GB.
