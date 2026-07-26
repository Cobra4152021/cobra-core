# Benchmark Reports

## Formats

| Format | API | Contents |
|--------|-----|----------|
| JSON | `render_json` / `*.json` | Full machine-readable run |
| Markdown | `render_markdown` / `*.md` | Human summary tables |
| HTML | `render_html` / `*.html` | Lightweight styled report |

Write all three with `write_reports(result, output_dir)`.

## Summary fields

- Overall score + pass/fail
- Skill score (mean of case scores per skill)
- Provider id (comparison label)
- Workflow id
- Latency average
- Estimated cost
- Calibration curve
- Repeatability (when `repeats > 1`)
- Recommendations

## Provider comparison

`BenchmarkRunner.compare_providers(dataset_id, ["mock", "openai"])` scores the **same** dataset/workflow with different provider **labels**. It does not change AIR routing; supply a custom `executor` to call real providers if desired.

## Audit

`BENCHMARK_AUDIT` stores isolated events (`channel=benchmark_isolated`). Secrets and prompts are redacted. Never mixed with ISF/KEF production audit.
