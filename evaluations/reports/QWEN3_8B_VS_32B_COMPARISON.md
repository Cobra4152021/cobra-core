# Qwen3-8B vs Qwen3-32B — CobraBench v0.1 Comparison

**Status:** Incomplete — no dual-model scores.  
**Date:** 2026-07-22  
**Benchmark:** CobraBench v0.1 (28 cases frozen)  
**Not Cobra Core.** Neither model is designated Cobra Core by this phase.

## Verdict

No quality comparison is available. Qwen3-32B failed local load validation; the dual-model evaluation was not started.

## Planned comparison axes (unevaluated)

| Axis | Status |
| --- | --- |
| Areas where 32B materially outperforms 8B | Unknown |
| Areas of similar performance | Unknown |
| Areas where 8B performs better | Unknown |
| Quality vs cost | 32B acquired (~65.5 GB disk) but cannot run here; 8B runs |
| Quality vs speed | Unknown for CobraBench; 32B load unstable |
| Statistically weak conclusions | N/A — zero case pairs |
| Cases needing reruns | All 28, after Gate 5 passes |
| Benchmark weaknesses discovered | Harness/heuristics prepared; not stress-tested on live outputs |

## Resource comparison (local measurements)

| Item | Qwen3-8B | Qwen3-32B |
| --- | --- | --- |
| Artifact size | ~16.4 GB | ~65.5 GB |
| Load on this machine | Success (Phase 2B) | Fail (crash `0xC0000005`) |
| CobraBench v0.1 | Not run (gate stop) | Not run |

## Recommendation

1. Do not invent a winner from weighted totals.  
2. Follow ADR-0002: stop 32B local evaluation on this host until resources improve.  
3. Optionally authorize 8B-only CobraBench v0.1 as an interim control baseline.
