# RELEASE NOTES — Phase 3F

**Tag:** `phase-3f-qualified`  
**Evidence commit:** `0a2af49ee86451c374a600579d3644c811cd12c0`  
**Freeze generated:** 2026-07-24T00:55:15.244149+00:00  
**Outcome:** A — Cloud Linux runtime fully qualified

## Infrastructure used

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud |
| Pod ID | `txw75nv9hn96hu` (adopted; no second pod created) |
| GPU | NVIDIA A40 48 GB |
| Displayed hourly rate | $0.44/hr |
| System RAM | 50 GB |
| Storage | 50 GB volume + 30 GB container (model/repo on `/workspace`) |
| OS / kernel | Ubuntu 24.04 template base / `5.15.0-94-generic` |
| Access | SSH over exposed TCP (runpodctl key) after `PUBLIC_KEY` injection |
| Estimated spend | ~$1.38 over ~3.14 h (ceiling $10 respected) |
| Cleanup | Pod terminated; zero remaining billable Phase 3F resources |

## Qualification results

| Gate | Result |
| --- | --- |
| Native CUDA / bitsandbytes backend | pass |
| Initial full load | pass |
| Initial synthetic generation | pass |
| 3/3 fresh-process qualification | pass |
| Extended session (5 prompts) | pass |
| Full-load budget used | 6 / 6 |
| Peak VRAM | ~5.88 GiB |
| Model revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Model inventory hash | `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f` |
| Runtime candidate | `evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json` |

CobraBench was **not** executed. Prepared rc2 protocol remains `prepared-not-run`.  
Official CobraBench v0.1 score remains **0.840**.

## Dependency changes

Cloud lock aligned to the validated Python 3.12 inference freeze before install:

* `huggingface-hub` corrected from `0.34.4` → `1.24.0` (required by `transformers==5.14.1`, `>=1.5.0`)
* `tokenizers` `0.22.1` → `0.22.2`
* `safetensors` `0.5.3` → `0.8.0`
* `numpy` `2.2.6` → `2.5.1`
* `psutil` `7.0.0` → `7.2.2`
* `pytest` `8.4.1` → `8.4.2`
* torch installed as `2.6.0+cu124` from the official cu124 wheel index

Pinned stack used in qualification: Python 3.12.3, torch 2.6.0+cu124, transformers 5.14.1, accelerate 1.14.0, bitsandbytes 0.49.2.

## Known limitations

* Qualification used synthetic smoke prompts only (not CobraBench cases).
* Runtime candidate is prospective; it is not added to a frozen runtime registry beyond this release package.
* Adopted GPU was A40 (user pod), not the originally preferred L4 SKU; still within the $10 / 8h authorization.
* Host overlay disk (~30 GB) is insufficient for model + venv; Linux-native `/workspace` storage was required.
* Phase 3G (controlled CobraBench v0.2-rc2 on this locked runtime) is authorized next but **not started**.

## Next authorized phase

**Phase 3G — controlled CobraBench v0.2-rc2 execution on the locked cloud runtime**

Do not train, deploy, or designate Cobra Core without a separate authorization.
