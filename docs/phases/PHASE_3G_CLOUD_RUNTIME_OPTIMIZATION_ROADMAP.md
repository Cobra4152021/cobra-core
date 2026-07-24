# Phase 3G — Cloud Runtime Optimization Roadmap

**Status:** Draft — awaiting approval (no implementation authorized)  
**Baseline freeze:** tag `phase-3f-qualified` → `0a2af49ee86451c374a600579d3644c811cd12c0`  
**Freeze package:** `docs/releases/phase-3f/`  
**Date:** 2026-07-23

## Objective

Optimize Cobra Core’s **qualified cloud Linux runtime** for production readiness **without** changing model behavior or benchmark results.

## Hard constraints (non-negotiable)

| Constraint | Required state |
| --- | --- |
| Functional equivalence to Phase 3F qualified runtime | Preserve load/generate semantics |
| Model revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Model inventory hash | `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f` |
| Quantization path | bitsandbytes 4-bit NF4 + double quant, float16 compute, `device_map={"": 0}` |
| CobraBench v0.2-rc2 | remains `prepared-not-run` |
| Official CobraBench v0.1 score | remains **0.840** |
| Training / fine-tuning | forbidden |
| Benchmark execution | forbidden in Phase 3G |
| Deployment / public endpoint | forbidden in Phase 3G |
| Cobra Core designation | not authorized |

**Scope note:** Earlier Phase 3F notes mentioned CobraBench as a possible next phase. **This Phase 3G charter supersedes that for the current workstream:** optimization planning only; no benchmark runs until a later explicitly authorized phase.

---

## Phase 3F measured baseline (ground truth)

| Metric | Measured value |
| --- | --- |
| Provider / GPU | RunPod Community Cloud / NVIDIA A40 48 GB @ $0.44/hr |
| Python / torch | 3.12.3 / `2.6.0+cu124` |
| transformers / accelerate / bitsandbytes | 5.14.1 / 1.14.0 / 0.49.2 |
| Cold load (first process) | **74.8 s** |
| Warmish subsequent loads | **~22–25 s** |
| Peak VRAM | **~5.88–6.32 GiB** |
| Host RAM total | ~503 GiB (pod oversized vs need) |
| Approx. process RAM delta (load) | ~2–3 GiB available-RAM drop observed |
| Generation latency (short smoke) | ~1.4–9.3 s |
| Overlay disk | ~30 GB (insufficient for model+venv) |
| Model + workspace path | `/workspace` network volume required |
| Phase 3F session cost | ~$1.38 / ~3.14 h |
| Qualification | 6/6 full loads; Outcome A |

---

## Evaluation dimensions

For each opportunity below:

* **Benefit** — expected production impact  
* **Effort** — engineering time / complexity (S / M / L)  
* **Risk** — chance of breaking functional equivalence or ops reliability (Low / Med / High)  
* **Requalification** — whether a full Phase-3F-style smoke qualification (or subset) is required before accepting the change into the locked candidate

### Requalification policy (proposed)

| Change class | Requalification |
| --- | --- |
| Ops-only (scripts, SSH bootstrap, cleanup automation, docs) | None (verification checklist only) |
| Dependency pin clarification without version change | Hash/lock verification only |
| Dependency version change, torch/CUDA/template change | **Full 6-load smoke requalification** |
| Quantization / device_map / dtype / tokenizer flags | **Full requal + treat as behavior-sensitive** (out of Phase 3G unless separately approved) |
| GPU SKU change with identical software stack | Abbreviated smoke (1 load + 1 generate + 1 qual) recommended; full 3/3 if SKU &lt; 24 GB VRAM |

---

## Opportunities by theme

### 1. Faster startup time (pod → ready shell)

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| S1 | Bake `PUBLIC_KEY` + SSH readiness into pod create/update checklist; avoid stop/start cycles | Saves 5–20 min per session when SSH broken | S | Low | No |
| S2 | Prefer Network Volume or persistent workspace already containing venv + model | Cuts env create from ~7–15 min to near-zero | M | Med (stale env drift) | Lock hash verify; smoke if image/venv changed |
| S3 | Prebuilt custom RunPod template with pinned venv + CUDA libs | Fastest cold pod boot to “import torch” | L | Med–High (image drift, larger attack surface) | Full smoke on template change |
| S4 | Automate first-boot provisioning script (idempotent) | Reliable minutes-scale setup; fewer human steps | M | Low | No (if pins unchanged) |

**Baseline pain:** SSH key injection / restart, overlay-disk dead ends, and pip installs dominated wall clock before first load.

---

### 2. Lower VRAM usage

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| V1 | Keep current 4-bit NF4 path; document peak ~6 GiB as the production envelope | Enables smaller GPUs (16–24 GB) → cost | S | Low | No (docs only) |
| V2 | Disable torch inductor / compile workers if spawned on import | Small VRAM/CPU noise reduction; cleaner cold start | S | Low–Med | Abbreviated smoke |
| V3 | Switch to alternate quant (GPTQ/AWQ/GGUF) or tighter bits | Possibly −1–3 GiB VRAM | L | **High** (behavior change) | **Out of Phase 3G** unless separately authorized |
| V4 | Activation / KV-cache limits for long contexts | Helps long prompts; little effect on short smoke | M | Med | Smoke + later bench phase |

**Assessment:** Phase 3F peak VRAM is already modest (~6 GiB). The main VRAM win for “production readiness” is **SKU right-sizing**, not more aggressive quantization.

---

### 3. Lower RAM usage

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| R1 | Right-size system RAM at provision (32–64 GB vs 50–500+ GB templates) | Lower $/hr on RAM-heavy SKUs; same model path | S | Low | Abbreviated smoke on new SKU |
| R2 | Ensure `low_cpu_mem_usage=True` remains enforced in one shared loader | Prevents accidental RAM spikes | S | Low | No if already true |
| R3 | Avoid CPU offload / disk offload permanently in production loader | Prevents RAM/disk blowups | S | Low | No (already forbidden in 3F) |
| R4 | Limit dataloader / tokenizer parallelism / inductor workers | Reduces multi-GB RAM spikes during load | S–M | Low | Abbreviated smoke |

**Assessment:** Host RAM was never the bottleneck (hundreds of GiB available). Optimize **provisioning RAM**, not model compression.

---

### 4. Reduced package footprint

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| P1 | Split locks: `requirements-cloud-runtime.txt` (inference) vs `requirements-cloud-dev.txt` (pytest, etc.) | Smaller prod venv; faster pip | S | Low | Hash verify + import smoke |
| P2 | Remove unused transitive NVIDIA wheels where safe (template already has CUDA) | Potentially multi-GB disk savings | M | Med (broken CUDA imports) | Full smoke |
| P3 | Use slim base image (no Jupyter, no unused CUDA toolkits) | Faster pull; less disk; better security | M–L | Med | Full smoke |
| P4 | Vendor only needed model shards + tokenizer files (already true) | No further weight reduction without format change | — | — | N/A |

**Observed freeze:** `pip freeze` includes full `nvidia-*-cu12` wheel set + `triton` + `pytest`. Prod path does not need pytest.

---

### 5. Faster cold model loading

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| L1 | Keep model weights on local NVMe/network volume close to GPU; never `/` overlay | Avoids catastrophic I/O; already required | S | Low | No |
| L2 | Persist safetensors on volume; measure warm-cache vs cold-cache loads | Clarify 75 s vs 22 s gap; target &lt;30 s cold | S | Low | Measurement only |
| L3 | Memory-map / safetensors load tuning; ensure single-threaded vs multi-shard strategy measured | Possible 10–40% cold-load improvement | M | Med | Full smoke |
| L4 | Torch weight pre-conversion / cached 4-bit state dict on volume | Large cold-load win possible | L | **High** (new artifact class; equivalence risk) | Full requal; new inventory hash scheme |
| L5 | Avoid fresh-process loads in production serving (keep warm worker) | Amortizes 22–75 s load | M | Med (ops/process model) | Smoke for warm path; not a loader change |

**Assessment:** Best near-term win is **warm worker + volume locality**. Cached quantized weights are powerful but raise equivalence/governance cost.

---

### 6. Improved dependency reproducibility

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| D1 | Fix BOM in `dependency_lock_sha256` field on runtime candidate; canonicalize lock hashing | Clean audits | S | Low | No |
| D2 | Commit `pip freeze` + lock + `uv`/`pip` hash-mode (`--require-hashes`) | Stronger bit-for-bit installs | M | Low–Med | Full smoke after first hashed install |
| D3 | Pin torch + all nvidia-* wheels explicitly in one lock file | Eliminates “install torch separately” footgun | S | Low | Full smoke once |
| D4 | Record CUDA driver / template digest / image digest in environment manifest | Ties runtime to image identity | S | Low | No |
| D5 | SBOM generation (CycloneDX) for cloud venv | Compliance / drift detection | M | Low | No |

**Assessment:** Highest ROI reproducibility work is **D1–D4** before any package upgrades.

---

### 7. Improved cloud provisioning

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| C1 | Codify “adopt-or-create” policy with hard `max_active_gpu_instances=1` | Prevents double-spend | S | Low | No |
| C2 | Preflight gates: price, VRAM≥16, RAM≥32, disk≥ model+venv+margin, US region, on-demand | Stops bad launches earlier | S–M | Low | No |
| C3 | Prefer L4/A5000 within authorized caps when creating (not adopting) | Better $/perf alignment to auth | S | Low | Abbreviated smoke on SKU |
| C4 | One-command provisioner: create → SSH wait → sync bundle/model → verify hashes → ready | Cuts human error; faster iteration | M | Med | Checklist + smoke on first use |
| C5 | Enforce `/workspace` (or network volume) for model+venv in provisioner | Prevents overlay OOM/disk-full | S | Low | No |
| C6 | Auto-terminate + cleanup verification as mandatory exit handler | Hard cost control | S | Low | No |

**Phase 3F lessons:** SSH blocked session progress; overlay disk nearly blocked model storage; adoption of A40 worked but was accidental SKU vs preferred L4.

---

### 8. Lower operating cost

| ID | Opportunity | Benefit | Effort | Risk | Requal |
| --- | --- | --- | --- | --- | --- |
| $1 | Use smallest GPU that fits ~8 GiB peak VRAM (e.g. 16–24 GB class within auth) | Often 30–70% $/hr reduction vs 48 GB A40 | S | Low–Med | Abbreviated/full smoke by SKU |
| $2 | Stop pod between jobs; keep only network volume | Pay storage not GPU while idle | S | Low | No |
| $3 | Reduce setup time via S2/S3/C4 (less billable idle GPU) | Saves $/session even at same rate | M | Low | Per linked item |
| $4 | Spot/interruptible instances | Large $/hr cut | S | **High** (preempt) | **Not authorized** under current auth rules |
| $5 | Multi-tenant / always-on endpoint | Amortizes load | L | High + deployment | **Forbidden in 3G** |

**Rough cost model (illustrative):**  
At $0.44/hr, every 15 minutes of avoidable setup ≈ $0.11. Cutting session overhead from ~45 min setup to ~10 min saves ~$0.25/session before any SKU change. Moving to a $0.20–0.30/hr 24 GB SKU (if available/authorized) dominates long-run savings.

---

## Prioritized engineering roadmap

### Priority 0 — Approve & lock Phase 3G charter (docs only)

1. Approve this roadmap and constraints.  
2. Record Phase 3G as **runtime optimization / production readiness**, explicitly **not** CobraBench execution.  
3. Keep `phase-3f-qualified` immutable; any accepted optimization lands as a new candidate + evidence, never silently rewriting 3F.

**Deliverable:** signed-off roadmap (this document) + short ADR-0015 draft after approval.

---

### Priority 1 — Production hygiene (low risk, no model-path change)

| Order | Item | Themes | Why first |
| --- | --- | --- | --- |
| 1 | C1, C2, C5, C6 — provision/cleanup gates | Provisioning, cost | Prevents spend accidents |
| 2 | S1, S4 — SSH/bootstrap automation | Startup | Removes largest non-model delay |
| 3 | P1, D1, D3, D4 — split locks + pin torch stack + image digests | Footprint, reproducibility | Cleaner installs without behavior change |
| 4 | V1, R1, R2, R3 — document envelope; right-size RAM/GPU selection rules | VRAM, RAM, cost | Enables cheaper SKUs safely |
| 5 | L1, L2 — volume locality + cold/warm load telemetry | Cold load | Quantifies next investments |

**Expected outcome:** Repeatable bring-up on a right-sized pod in &lt;15–20 minutes with verified locks, without touching model code.

**Requalification:** mostly none; abbreviated smoke when SKU changes.

---

### Priority 2 — Cold-start & install performance (still equivalence-preserving)

| Order | Item | Themes | Notes |
| --- | --- | --- | --- |
| 6 | S2 — persisted volume with venv+weights | Startup, cost | Guard with lock/hash checks each boot |
| 7 | C3, $1 — authorized cheaper SKU matrix (L4/A5000/16–24 GB) | Cost, provisioning | Smoke per SKU |
| 8 | L5 — warm long-lived worker pattern (ops pattern, not serving deploy) | Cold load | Keep non-public; no endpoint |
| 9 | D2 — hash-checked installs | Reproducibility | One full smoke after enablement |
| 10 | P2/P3 — slim image / trim CUDA wheels | Footprint, startup | Full smoke |

**Expected outcome:** Cold pod→first-token path dominated by model load (~20–75 s), not package install or SSH recovery.

---

### Priority 3 — Deferred / requires separate authorization

| Item | Why deferred |
| --- | --- |
| V3, L4 — new quant formats or cached 4-bit artifacts | Behavior / inventory governance |
| $4 — spot instances | Outside current authorization |
| $5 / public endpoint / deployment | Explicitly forbidden |
| CobraBench v0.2-rc2 execution | Separate phase after optimization approval path |
| Any transformers/torch upgrade | Full requal + freeze discipline |

---

## Suggested Phase 3G work packages (after approval)

| WP | Name | Includes | Exit criteria |
| --- | --- | --- | --- |
| WP-A | Charter & ADR | ADR-0015 scope; update `docs/ROADMAP.md` | Approved constraints published |
| WP-B | Provisioner hardening | C1–C2, C5–C6, S1, S4 | Dry-run docs + scripted checklist; no live spend until authorized |
| WP-C | Lock & footprint | P1, D1, D3, D4 | New lock files hashed; import test locally/cloud |
| WP-D | SKU & cost playbook | V1, R1, C3, $1–$3 | Written SKU matrix with estimated $/hr and smoke plan |
| WP-E | Load telemetry | L1–L2, optional L3 spike | Cold vs warm load report under same pins |
| WP-F | Optional volume cache | S2 (+ guarded) | Boot script verifies inventory + lock before use |

**No WP implements model/benchmark/deploy changes.**

---

## Success metrics (for later implementation phases)

| Metric | Phase 3F baseline | Phase 3G target (proposal) |
| --- | --- | --- |
| Time: pod RUNNING → SSH ready | variable (blocked once) | &lt; 3 min typical |
| Time: SSH → verified env | ~7–15 min pip | &lt; 2 min (cached) or &lt; 10 min (cold pip) |
| Cold model load | 74.8 s first / ~22 s later | Documented; aim ≤30 s cold on volume |
| Peak VRAM | ~6.3 GiB | ≤ 8 GiB envelope unchanged |
| Billable setup overhead | large fraction of 3F session | ≥50% reduction on repeat sessions |
| Dependency identity | lock + freeze | lock + freeze + image digest + hash install |
| Benchmark status | prepared-not-run | **unchanged** |
| Official score | 0.840 | **unchanged** |

---

## Explicit non-goals

* Changing generation defaults, prompts, or tokenizer chat-template behavior  
* Running CobraBench or any benchmark case  
* Training, LoRA, QLoRA  
* Public inference endpoints / Jupyter exposure  
* Declaring Cobra Core  
* Silent dependency upgrades “for speed”

---

## Approval gate

**Stop here.** Do not implement WP-B through WP-F until this roadmap is approved.

Requested decision from approver:

1. Accept Phase 3G charter (optimization ≠ benchmark execution)?  
2. Approve Priority 1 items for implementation next?  
3. Authorize any cloud spend for validation pods (amount / hours / SKU caps)?  
4. Confirm cheaper SKUs within existing auth are allowed for smoke requal?

---

## References

* `docs/releases/phase-3f/` (freeze package)  
* `docs/releases/phase-3f/RELEASE_NOTES_Phase3F.md`  
* `docs/releases/phase-3f/runtime-candidate/qwen3-8b-cloud-linux-qualified.json`  
* `docs/decisions/ADR-0014-cloud-linux-runtime-qualification.md`  
* Tag: `phase-3f-qualified`
