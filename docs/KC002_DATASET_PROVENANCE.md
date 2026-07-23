# KC-002 — Dataset Provenance

## Policy

Only original Cobra-created synthetic images and annotations.  
**Not used:** LLaVA-Instruct, Infinity-MM, COCO downloads, scraped web images.

## Location

- Manifest: `data/kc002/manifest.jsonl`
- Images: `data/kc002/images/*.png`
- Generator: `kc002/scripts/generate_micro_dataset.py`

## Summary

| Field | Value |
|-------|--------|
| Items | 32 (24 train-pattern + 8 eval-pattern from generator; 16 count + 16 color) |
| License | Apache-2.0 (original synthetic; redistributable) |
| Creator | Cobra Core KC-002 |
| Categories | color, counting_color_shape |
| PII | None |
| Faces | None |
| External photos | None |

## Per-item fields

Each JSONL row includes: `id`, `split`, `image_relpath`, `image_source`, `creator`, `license`, `creation_date`, `sha256`, `category`, `question`, `expected_answer`, `acceptable_variants`.

## Commercial suitability

**A — ACCEPTABLE** for research and commercial training of Cobra Core adapters (original synthetic works owned/created in this repo).
