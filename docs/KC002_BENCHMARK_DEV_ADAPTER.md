# KC-002 — Benchmark Lab Development Adapter (spec only)

**Do not** connect to production or the weekly scheduler.

## Proposed selection

| Field | Value |
|-------|--------|
| Selection ID | `cobra-core-vision-dev` |
| Provider | `cobra_core` |
| Auth | mTLS or service token (internal) |
| Concurrency | 1 (dev) |

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/healthz` | GPU warm/cold + VRAM |
| GET | `/v1/model` | checkpoint ID + revisions |
| POST | `/v1/chat/completions` | text and multimodal (OpenAI-like content parts) |

## Limits

- Timeout: 120s default  
- Max images: 4  
- Max bytes/pixels: KC-001 safety limits  
- Cost: GPU-seconds meter → Benchmark Lab ledger  

## Failure classes

Reuse Benchmark Lab taxonomy: timeout, OOM, provider_5xx, malformed_image, context_overflow.
