# Benchmark Scoring

## Overall score

Weighted mean (defaults):

| Component | Weight |
|-----------|--------|
| Finding accuracy (F1) | 0.30 |
| Citation accuracy | 0.25 |
| Schema validity | 0.15 |
| Completeness | 0.15 |
| Confidence calibration | 0.15 |

Optional: if `human_agreement` is supplied on an execution, overall = `0.9 * score + 0.1 * human_agreement`.

Pass threshold default: **0.70** (`BENCHMARK_PASS_THRESHOLD`).

## Finding accuracy

Normalized string F1 between extracted findings and gold findings. Also reports false positive / false negative rates.

## Citation scoring

| Signal | Meaning |
|--------|---------|
| supported | Actual citation in gold set |
| incorrect / unsupported | Actual citation not in gold |
| missing | Gold citation absent |
| duplicate | Repeated citation labels |

Accuracy ≈ supported / |gold|, with a small duplicate penalty.

## Schema validity

Output validated via ISF `validate_skill_output`. Score 1.0 if valid when gold expects validity.

## Completeness

Checks `summary_contains`, structured field matches, and expected `missing_information` hits.

## Confidence calibration

- Confidence must fall in gold `[min, max]`
- High confidence (≥0.7) should correspond to correct findings
- Low confidence (≤0.4) is preferred when findings are wrong

Calibration curve bins: `high` / `medium` / `low`.

## Missing-evidence cases

When gold `expect_missing_evidence=true`, credit detecting `missing_required_evidence` (or populated `missing_information`).

## Latency & cost

Taken from execution metadata. Cost uses optional `$ / 1k tokens` config (reporting only).
