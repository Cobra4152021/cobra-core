# Performance Baseline — v0.9.0-rc1 (offline mock)

**Mode:** `COBRA_INFERENCE_MODE=mock`  
**Host:** local pytest runner  
**Suite:** `tests/test_protocol_v1_rc1_controls.py::test_offline_soak_mock_100_requests`

## Results (software path)

| Metric | Value |
| --- | --- |
| Requests | 100 |
| Successes | 100 |
| Failures | 0 |
| Final inflight | 0 |
| Double-count check | 1 metrics success per request |
| GPU | not used |

This is an **offline software soak**, not a GPU inference benchmark.

## GPU baseline

Not executed in this certification pass. Requires separate authorization for:

- Qwen3-8B NF4 load
- sustained token throughput / latency percentiles
- optional CobraBench (must not silently replace 0.840)

## Phase 4 capability evidence (prior)

See `docs/capability-validation/CAPABILITY_VALIDATION_REPORT.md` (97.8% Pass/Pass+, prior GPU host). RC gate for a **second** validation wave remains GPU-gated.
