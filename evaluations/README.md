# Evaluations

| Path | Purpose |
| --- | --- |
| `results/` | Raw evaluation artifacts (gitignored) |
| `reports/` | Human-readable reports (mostly gitignored; templates committed) |

Every evaluation must preserve exact prompt, model revision, inference parameters, raw output location, evaluator version, and scoring rationale.

Generate an empty report template:

```bash
python scripts/report_template.py
```
