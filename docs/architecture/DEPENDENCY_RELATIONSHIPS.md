# Dependency relationship diagram

Pinned cloud runtime stack for Phase 3F equivalence. **Do not upgrade versions in Phase 3G.5** (docs-only phase).

## Relationship map

```mermaid
flowchart TB
  IMG["container-image-pin.json<br/>RunPod pytorch template digest"]
  TORCH["torch-pin.json<br/>torch==2.6.0+cu124"]
  RT["requirements-cloud-runtime.txt<br/>transformers / accelerate / bnb / …"]
  DEV["requirements-cloud-dev.txt<br/>pytest etc."]
  LOCK["requirements-cloud-lock.txt<br/>alias / freeze companion"]
  HASH["dependency-lock.sha256"]
  MAN["environment-manifest.json"]
  VENV[".venv-qwen-cloud on /workspace"]
  QUAL["_phase3f_linux_qualify_*"]
  CAND["runtime-candidate JSON"]

  IMG -.->|host base only; venv overrides torch| VENV
  TORCH --> VENV
  RT --> VENV
  DEV -.->|optional tests| VENV
  RT --> LOCK
  LOCK --> HASH
  TORCH --> MAN
  RT --> MAN
  HASH --> MAN
  VENV --> QUAL
  QUAL --> CAND
```

## Runtime vs development

| File | Install when | Includes pytest? |
| --- | --- | --- |
| `requirements-cloud-runtime.txt` | Always for qualification | No |
| `requirements-cloud-dev.txt` | Optional local/pod tests | Yes |
| `requirements-cloud-lock.txt` | Companion lock alias | Matches freeze discipline |

## Critical pins (qualified)

| Component | Version |
| --- | --- |
| Python | 3.12.x (3.11 OK; not 3.13) |
| torch | `2.6.0+cu124` (official cu124 index) |
| transformers | 5.14.1 |
| accelerate | 1.14.0 |
| bitsandbytes | 0.49.2 |
| huggingface-hub | 1.24.0 (required by transformers ≥1.5.0) |

## Change impact

| Change | Requalification |
| --- | --- |
| Docs / ops scripts only | None |
| Same versions, re-hash locks | Hash verify |
| Any runtime version bump | Full 6-load smoke |
| Quant / device_map / model revision | Full requal + treat as behavior-sensitive |
| GPU SKU only | Abbreviated smoke recommended |

## Integrity check

```bash
python scripts/phase3g_verify_env.py
```

Must pass before treating a pod as qualification-ready.
