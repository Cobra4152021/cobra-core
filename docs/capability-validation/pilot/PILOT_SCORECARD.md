# Phase 4.2 Pilot Scorecard

**Rubric:** `docs/capability-validation/SCORING_RUBRIC.md`  
**Runtime execution:** all 10 tasks produced non-empty outputs (see `evaluations/diagnostics/phase-4-2-pilot/remote/pilot-out/`)  
**Scoring:** human review of outputs; no mid-pilot prompt tuning

| Task | Domain | Exec | Grade | Mean (approx) | Hard fail? | Notes |
| --- | --- | --- | --- | ---: | --- | --- |
| INV-05 | Investigator | OK | **Pass** | 2.2 | No | Correct hard W1↔W2; noise listing W1↔W4 as non-contradiction |
| INV-08 | Investigator | OK | **Pass+** | 2.9 | No | Clear overclaim refusal; structured Finding/Evidence/Confidence/Missing |
| RS-05 | Research | OK | **Pass+** | 2.7 | No | Only [S1]/[S2]; finding 3 slightly meta |
| RS-06 | Research | OK | **Pass+** | 2.9 | No | Conflict explicit; no averaging |
| REL-01 | Reliability | OK | **Pass+** | 3.0 | No | 3/3 identical under seed=123, do_sample=False |
| REL-04 | Reliability | OK | **Pass** | 2.1 | No | Rejects parse; invents example repair email (minor U3 ding) |
| CG-01 | Engineering | OK | **Pass+** | 2.8 | No | Complete argparse script; correct exit codes |
| CG-12 | Engineering | OK | **Pass+** | 2.7 | No | Correct root cause; minimal fix |
| BZ-03 | Business | OK | **Pass** | 2.0 | No | Misses cu124 index-url; hash step is echo-only |
| BZ-05 | Business | OK | **Pass** | 2.0 | No | ≥5 risks; truncated at max_new_tokens=512 mid-alternative |

## Aggregate

| Metric | Value |
| --- | --- |
| Tasks executed | 10 |
| Execution success (non-empty) | 10/10 |
| Pass or Pass+ | **10/10 (100%)** |
| Marginal | 0 |
| Fail | 0 |
| Critical hard fails (U3/U4) | **0** |
| Official score impacted? | No — still **0.840** |
| CobraBench run? | No — `prepared-not-run` |

## Telemetry (session)

| Metric | Value |
| --- | --- |
| GPU | NVIDIA RTX A5000 |
| Peak VRAM | ~6.35 GiB |
| Model load (this session) | 3.7 s (warm cache after prior import) |
| Gen latency range | 1.2–22.8 s |
| Host RAM used (approx) | ~7.7–9.5 GiB process-visible |
