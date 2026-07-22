# Qwen3-8B Weakness Matrix (Phase 2E)

**Baseline:** `20260722T200000Z-8bba5e01` (locked)  
**Diagnostics:** planned `20260722T220000Z-2ediag01` — **blocked before generation** (`0xC0000005`; not a model-quality test failure).  
**Rank order:** investigation risk → frequency → reproducibility → harm potential.

## Material weaknesses

### W01 — Unsupported-claim heuristic

| Field | Value |
| --- | --- |
| Cause | Scoring / evaluator (**S**) |
| Sampled precision | ≈ **0%** (0/50 true unsupported) |
| False-positive rate | ≈ **100%** on the labeled sample |
| Training target? | **No** |
| Next action | Version heuristic; ignore aggregate 172 for model judgment |

### W02 — Citation-key behavior

| Field | Value |
| --- | --- |
| Cause | Prompt / interface (**P**), with scoring sensitivity |
| Cases | cb-023, cb-024 (P# / [S#] vs SRC-A) |
| Prompt-fixable? | **Likely yes** |
| Training target? | **Not yet** |
| Next action | Clarified cite-SRC instructions; v0.2 secondary-label policy |

### W03 — Metric contradiction depth

| Field | Value |
| --- | --- |
| Cause | Suspected model capability (**M**) |
| Cases | cb-019 (human ≈ 0.55) |
| Requires | Controlled thinking + prompt diagnostics |
| Adaptation-eligible? | **No — not yet** |
| Next action | Complete deferred Cohort B/C before any Class 4 discussion |

### W04 — Exact output formatting

| Field | Value |
| --- | --- |
| Cause | Prompt / parser (**P**+**S**) |
| Cases | cb-027 |
| Content | Semantic FINDING/RISK/NEXT substantially correct; markdown bullets |
| Scoring | Dual semantic + exact-format scores |
| Training target? | **No** |

### W05 — Output-token budgeting

| Field | Value |
| --- | --- |
| Cause | Runtime / configuration (**L**+**P**) |
| Cases | Verbose investigation (e.g. cb-001/002/004 at 512 tokens) |
| Long-doc baseline? | **Not** established as cause of cb-023/024 (finished ~128 tokens) |
| Training target? | **No** |
| Next action | Token budgeting / higher caps (deferred Cohort A) |

### W06 — Early long-document completion

| Field | Value |
| --- | --- |
| Cause | Suspected model behavior or prompt effect (**M**/**P**), not simple truncation |
| Evidence | finish_reason=completed at ≈127–128 tokens under 512 cap |
| Requires | Controlled output-length and prompt diagnostics |
| Adaptation-eligible? | **No — not yet** |

### W07 — Keyword-based false failures

| Field | Value |
| --- | --- |
| Cause | Scoring / parser (**S**) |
| Nature | Benchmark framework issue (behavior keywords vs strong human scores) |
| Training target? | **No** |
| Next action | Evaluator / v0.2 keyword-checker review |

### W08 — Quantization impact

| Field | Value |
| --- | --- |
| Cause | **Unknown** (**U**/**R**) |
| Evidence | No BF16 or 8-bit comparison exists |
| Rule | Do **not** attribute weaknesses to 4-bit without evidence |

### W09 — GPU contention

| Field | Value |
| --- | --- |
| Cause | Runtime environment (**R**) |
| Effect | Blocked Phase 2E live diagnostic generations |
| Model-quality weakness? | **No** |
| Next action | Follow diagnostics runbook; new run ID |

## Summary table

| ID | Likely cause | Training-addressable now? |
| --- | --- | --- |
| W01 | S | No |
| W02 | P (+S) | No |
| W03 | M (suspected) | No — await controls |
| W04 | P+S | No |
| W05 | L/runtime | No |
| W06 | M/P (suspected) | No — await controls |
| W07 | S | No |
| W08 | U | Unknown / not attributed |
| W09 | R (environment) | N/A |

## Ranking for investigation risk

1. **W03** — numeric contradiction depth  
2. **W06 / W02** — long-doc completeness and citation habit  
3. **W01 / W07** — scoring noise distorting decisions  
4. **W05 / W04** — operational and format risks  
5. **W08** — uncertainty, not a proven defect  
6. **W09** — process blocker only
