# Qwen Acquisition Plan (Phase 2A)

**Status:** Documented only. **Do not execute** without separate authorization.  
**Related ADR:** `docs/decisions/ADR-0001-qwen-baseline-selection.md`

## 1. Which model to download first

**First acquisition:** `Qwen/Qwen3-32B`  
Pinned revision / Hub commit: `9216db5781bf21249d130ec9da846c4624c16137`  
Manifest: `model-cards/qwen/qwen3-32b.manifest.json`

## 2. Why it was selected

- Strongest practical dense Qwen3 checkpoint for full CobraBench  
- Hybrid thinking / non-thinking in one model  
- Apache-2.0 license with official LICENSE file  
- Official Transformers / vLLM / SGLang / llama.cpp support paths  
- Better early LoRA practicality than MoE flagships  

See `docs/QWEN_CANDIDATE_ANALYSIS.md` and ADR-0001.

## 3. Expected storage requirements

| Item | Value | Class |
| --- | --- | --- |
| BF16 parameter footprint | ≈ 32.8B × 2 bytes ≈ **66 GB** | Estimate |
| Full Hub snapshot (weights + tokenizer + configs + LICENSE + README) | **~70–80 GB** allowing metadata overhead | Estimate |
| Recommended free disk headroom | **≥ 100 GB** on the acquisition volume | Engineering assumption |
| Optional AWQ-INT4 working set later | Much smaller; do not acquire until BF16 baseline integrity is proven | Assumption |

Official Hugging Face shard byte sizes were **not returned** by the Hub API in this intake environment — treat disk figures as estimates until `huggingface-cli download` reports actual bytes.

## 4. Expected hardware requirements

| Mode | Expectation | Class / source |
| --- | --- | --- |
| BF16 Transformers short context | ~**62,751 MB** GPU memory | Verified — [Qwen speed benchmark](https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html) (NVIDIA H20) |
| BF16 long context | Higher due to KV cache | Estimate |
| AWQ-INT4 Transformers short context | ~**19,109 MB** | Verified — same official table |
| CPU-only BF16 | Not recommended for CobraBench | Estimate |

## 5. Preferred initial precision / quantization

1. **Preferred first run:** official **BF16 safetensors** (method `none` in manifest).  
2. **Fallback if VRAM insufficient:** official/community **AWQ-INT4** only after documenting a separate manifest revision.  
3. Do **not** start with unverified GGUF as the primary integrity target.

## 6. Preferred initial inference framework

| Priority | Framework | Rationale |
| --- | --- | --- |
| 1 | **Transformers** | Official quickstart path; simplest provenance for first smoke + artifact validation |
| 2 | **vLLM** | Officially documented for Qwen3 serving / OpenAI-compatible eval harness later |
| 3 | **SGLang** | Officially documented; strong for throughput once baseline exists |
| Deferred | llama.cpp / MLX | Useful for quantized local loops; not the first integrity path |

Phase 2A does **not** implement runners; this is acquisition guidance only.

## 7. How exact revisions will be pinned

1. Record Hub commit SHA in `model_revision` and `source_commit` (already done for candidates).  
2. Download with explicit revision, e.g. `huggingface-cli download Qwen/Qwen3-32B --revision 9216db5781bf21249d130ec9da846c4624c16137`.  
3. After download, re-query Hub API / local `.cache` refs and refuse promotion if SHA drifts.  
4. Never use floating refs (`main`, `latest`) for evaluation.

## 8. How every downloaded artifact will be hashed

1. For each file listed in the manifest (and any additional files present), compute **SHA256**.  
2. Update artifact entries: `verification_state=verified`, `sha256=<digest>`, `size_bytes=<n>`.  
3. Set `acquisition_status=acquired` and `acquisition_date` only after **all** required artifacts verify.  
4. Store a machine-readable hash ledger beside weights (outside git), e.g. `SHA256SUMS`.

## 9. Where weights will be stored (outside git)

Recommended layout (local, gitignored):

```text
D:/cobra-models/   # or $COBRA_MODEL_ROOT
  qwen/
    Qwen3-32B/
      9216db5781bf21249d130ec9da846c4624c16137/
        <hub files>
        SHA256SUMS
        INTAKE.json   # copy of manifest after acquisition
```

`.gitignore` already blocks `*.safetensors`, `models/`, `weights/`, etc. Never commit shards.

## 10. How license files and model cards will be preserved

1. Keep upstream `LICENSE` and `README.md` next to weights.  
2. Copy LICENSE text into `model-cards/qwen/licenses/` **only if** needed for offline audit (text, not weights).  
3. Retain `license_url` pointing at the official Hub raw/blob LICENSE.  
4. Do not re-license Cobra Core as Apache solely because the base model is Apache.

## 11. How provenance will be recorded

Minimum provenance bundle per acquisition:

- Updated `ModelManifest` (status, hashes, dates)  
- Hub model id + commit SHA  
- Download tool + version + timestamp  
- Host OS / GPU / driver notes  
- Pointer to offline weight path  
- Optional: `huggingface-cli` or `git-lfs` logs (redact tokens)

## 12. Detecting partial or interrupted downloads

1. Compare on-disk file set to Hub sibling list for the pinned revision.  
2. Compare sizes to Hub metadata when available.  
3. Fail if any safetensors shard is missing or hash mismatches.  
4. Treat incomplete index/shard sets as **failed** acquisition — do not evaluate.

## 13. Quarantine if validation fails

1. Set `acquisition_status=quarantined` (or `failed`).  
2. Move tree to `.../quarantine/<model>/<commit>-<timestamp>/`.  
3. Do not delete immediately — retain for forensics.  
4. Block evaluation runners from quarantined paths.  
5. Record failure reason in manifest `notes`.

## 14. Removal and cleanup

1. Delete only quarantined or superseded trees after hash ledger archival.  
2. Keep the manifest history in git (status transitions).  
3. Secure-delete is optional; standard delete is acceptable for non-sensitive public weights.  
4. Clear Hugging Face cache entries deliberately (`huggingface-cli delete-cache` or manual) to avoid silent reuse of wrong revisions.

## Acquisition order (when authorized)

1. `Qwen3-32B` (primary)  
2. `Qwen3-8B` (development / CI)  
3. `Qwen3-30B-A3B-Thinking-2507` (reasoning challenger)

## Explicit non-actions

- No download in this phase  
- No inference  
- No fine-tuning  
- No deployment  
- No designation of any model as Cobra Core
