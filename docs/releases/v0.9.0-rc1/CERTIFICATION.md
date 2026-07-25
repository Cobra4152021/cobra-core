# Cobra Core RC1 Certification Record

**Version:** `0.9.0rc1`  
**Intended tag:** `v0.9.0-rc1`  
**Date:** 2026-07-25  
**Branch:** `kc-rc1-certification`

## Decision

**READY FOR RC1** (software / Protocol V1 package scope).

Not a production internet deployment designation. Not a CobraBench score change.

## Quality evidence

| Gate | Result |
| --- | --- |
| `scripts/run_quality.py` | PASS (270 passed, 1 skipped) |
| `ruff check` / `ruff format --check` | PASS |
| `mypy src/cobra_core` | PASS |
| `cobra-protocol-conformance` | PASS |
| schemaHash | `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3` |
| fixtureHash | `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7` |
| `python -m build` | PASS → `cobra_core-0.9.0rc1` sdist + wheel |
| Official score | `0.840` unchanged |
| CobraBench | `prepared-not-run` |

## RC1 engineering delivered

- Kill switch, concurrency, daily quota admission
- Metrics + authenticated `/metrics`
- CI workflow
- Changelog, release notes, config/deploy/rollback/troubleshoot docs
- Offline mock soak (100 requests)
- Security review delta + dependency review

## Remaining (explicitly out of software-RC cut / human-GPU)

1. Second live Phase 4 capability validation wave on GPU
2. Live GPU inference soak / latency percentiles
3. Optional authorized CobraBench re-run (must not silently replace 0.840)

## Tag command

```bash
git tag -a v0.9.0-rc1 -m "Cobra Core 0.9.0rc1 — Protocol V1 software release candidate"
```
