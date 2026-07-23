# KC-001 — GPT-OSS Native Vision Audit

Research package for Project King Cobra. Validates whether a **native** vision path into GPT-OSS is technically sound — without modifying Cobra Computer production routing and without large-scale training.

## Quick start

```bash
cd kc001
make setup
make validate-env
make test
make smoke-text
make smoke-vision
make overfit
make image-dependence
```

## Important

- Full `openai/gpt-oss-20b` weights are **not** committed.
- On GPUs with &lt;16GB VRAM, architecture proofs use a **Tiny GPT-OSS-shaped MoE** surrogate with the same integration pattern (prepend projected visual tokens into `inputs_embeds`).
- Do not claim production native multimodal until image-dependence passes on the real GPT-OSS weights.

## Docs

See `../docs/KC001_*.md`.
