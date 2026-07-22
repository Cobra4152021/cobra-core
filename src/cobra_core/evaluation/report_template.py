"""Empty evaluation report template generator."""

from __future__ import annotations

from pathlib import Path

TEMPLATE = """# CobraBench Evaluation Report (Template)

> Status: EMPTY TEMPLATE — no model was evaluated.
> LLM-as-judge scores are advisory only and are never ground truth.

## Run metadata

| Field | Value |
| --- | --- |
| run_id | _TBD_ |
| timestamp | _TBD_ |
| model_manifest_ref | _TBD_ |
| model_revision | _TBD_ |
| benchmark_version | _TBD_ |
| evaluator_version | _TBD_ |
| deterministic_seed | _TBD_ |

## Inference settings

| Parameter | Value |
| --- | --- |
| temperature | _TBD_ |
| top_p | _TBD_ |
| max_tokens | _TBD_ |
| seed | _TBD_ |

## Hardware / runtime

| Field | Value |
| --- | --- |
| device | _TBD_ |
| accelerator | _TBD_ |
| runtime | _TBD_ |
| os_name | _TBD_ |

## Preserved artifacts

- Exact system prompt: _path TBD_
- Exact user prompt: _path TBD_
- Raw model output: _path TBD_
- Model manifest: _path TBD_

## Category scores

Scores must retain category-level detail. Do not report only a single unexplained number.

| Category | Weight | Objective | Rule-based | Human | LLM-as-judge (advisory) | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Investigation reasoning | 20% | | | | | |
| Evidence grounding | 15% | | | | | |
| Hallucination resistance | 15% | | | | | |
| Citation correctness | 15% | | | | | |
| Contradiction detection | 10% | | | | | |
| Coding | 10% | | | | | |
| Long-document analysis | 5% | | | | | |
| Refusal quality | 5% | | | | | |
| Instruction following | 5% | | | | | |

## Overall score (derived)

- Weighted overall: _TBD (derive only from complete category breakdown)_
- Interpretation: overall is a summary; category cells above are authoritative detail.

## Scoring rationale

_Per-category rationale goes here. Preserve evaluator kind and version for each score._

## Evidence separation checklist

- [ ] Objective measurements recorded separately
- [ ] Rule-based checks recorded separately
- [ ] Human judgments recorded separately
- [ ] LLM-as-judge results marked advisory
- [ ] No private evidence committed to git

## Notes / weaknesses for Phase 3

_TBD_
"""


def write_empty_report_template(output: Path) -> Path:
    """Write the empty evaluation report template to ``output``."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(TEMPLATE, encoding="utf-8")
    return output
