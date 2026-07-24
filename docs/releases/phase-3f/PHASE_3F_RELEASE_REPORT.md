# Phase 3F Release Report

## Verdict

**Qualified.** Tag `phase-3f-qualified` freezes evidence commit `0a2af49ee86451c374a600579d3644c811cd12c0` (Outcome A).

## Freeze contents

Package root: `docs/releases/phase-3f/`

Includes runtime qualification report, environment versions, dependency lockfiles, runtime candidate JSON, quality suite results, attempt evidence, cloud cost/cleanup records, release notes, and this report.

## Integrity

* CobraBench v0.2-rc2 protocol: `prepared-not-run`
* Official CobraBench v0.1 score: **0.840** (unchanged)
* Quality suite at freeze: **passed** (`229 passed, 1 skipped, 6 deselected in 3.50s`)
* Benchmark executed during Phase 3F: **false**

## Operations summary

* Adopted RunPod pod `txw75nv9hn96hu` (A40, $0.44/hr); no second instance
* 6/6 full-load qualification sequence passed
* Estimated spend ~$1.38; pod terminated; remaining billable resources: none

## Next step

Phase 3G is the next authorized phase. It is **not** started by this freeze.
