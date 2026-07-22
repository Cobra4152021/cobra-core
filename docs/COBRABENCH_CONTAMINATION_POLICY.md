# CobraBench Contamination Policy

This document defines how CobraBench cases are sourced, versioned, and kept valid as a measurement instrument. It applies to all frozen releases under `benchmarks/releases/` and to working copies under `benchmarks/cases/`.

## Why synthetic cases are preferred initially

Early CobraBench releases prioritize **fully synthetic, public-safe cases** because they:

- Eliminate privacy, legal, and operational risk from real investigations or customer data.
- Avoid copyright issues from reproducing substantial third-party text.
- Reduce the chance that benchmark prompts already appear in public crawl data tied to specific answers.
- Make the suite reproducible for external researchers without access agreements.

Public-source material may be added later only after transformation (below) and contamination review.

## How public-source cases are transformed

When a case draws on public material, it must be **transformed**, not copied:

1. **Abstract** — Replace names, organizations, dates, and identifiers with fictional equivalents.
2. **Restructure** — Change narrative order, document types, or section layout so the case is not reconstructible from the original.
3. **Subset** — Include only the minimum excerpt needed; never paste full articles, filings, or manuals.
4. **Re-key** — Assign new citation keys (`SRC-A`, …) and new case IDs; do not preserve original URLs as answers.
5. **Review** — Record provenance internally (not in public case JSON) and run near-duplicate detection before inclusion.

Transformed cases still require `sensitivity` classification and may not ship until reviewed.

## Why prompts must not be published prematurely

Benchmark **prompts and source bundles are part of the measurement instrument**. Publishing them widely before a release is frozen can:

- Allow models or vendors to train or tune directly on exact evaluation items.
- Invalidate comparisons between “before leak” and “after leak” runs.
- Encourage overfitting to citation keys and expected phrases checked by objective rules.

**Policy:** Do not publish full case JSON, system prompts, or user prompts outside controlled evaluation contexts until the release is explicitly marked frozen and documented. Aggregated scores and category descriptions may be published; full prompts require release versioning and contamination review.

## Case versioning

Each case carries a `version` field (e.g. `0.1.0`). Frozen releases use a directory slug (e.g. `cobrabench-v0.1`) plus `INVENTORY.json` hashes.

- **Patch-level changes** (wording clarity, typos) require new case `version` and inventory regeneration.
- **Material changes** (expected behaviors, sources, checks) require a **new release** (e.g. v0.2), not silent edits to a frozen release.
- Never rewrite hashes in `INVENTORY.json` without changing file content through a documented release process.

## Training datasets kept separate

Model training corpora, fine-tuning JSONL, and distillation pipelines must live in **separate storage paths** from benchmark releases. CI and tooling should not merge benchmark case directories into training data builders by default.

## Fine-tuning must exclude held-out benchmark cases

Any fine-tuning, RLHF, or continued pretraining on Cobra-target models **must exclude**:

- All case IDs and file contents from frozen releases the model will be scored against.
- Near-duplicates (see below) of those cases.

Training `guard` modules and dataset manifests should reference release IDs explicitly. Using benchmark text as training data invalidates future scores on that release.

## Near-duplicate detection

Before adding or publishing cases, run near-duplicate checks:

- **Exact** — SHA-256 of normalized JSON body (excluding pretty-print whitespace if normalized).
- **Textual** — Shingle or embedding similarity on `system_prompt`, `user_prompt`, and `supporting_sources[].content` against held-out releases and training sets.
- **Structural** — Same category + highly overlapping expected behaviors and checks.

Cases above the project similarity threshold are rejected or deferred to a future non-held-out split.

## Accidental leakage invalidates a benchmark version

If benchmark prompts or answers are found in:

- Public repos, forums, or vendor training disclosures, or
- A model’s training set without exclusion proof,

then that **release version is contaminated** for rigorous comparison. Response:

1. Document the leak scope and date.
2. Retire the release for primary reporting (keep for historical runs only with a contamination flag).
3. Cut a new release with new case IDs and refreshed content.
4. Do not compare scores across contaminated and clean releases without explicit adjustment.

## Related artifacts

- Frozen releases: `benchmarks/releases/cobrabench-v0.1/`
- Working copies: `benchmarks/cases/`
- Inventory tool: `scripts/build_cobrabench_inventory.py`
- Release helpers: `src/cobra_core/benchmarks/release.py`
