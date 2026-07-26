"""Benchmark reports — JSON, Markdown, HTML."""

from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from cobra_core.benchmark.schemas import BenchmarkRunResult, CaseScore


def result_to_dict(result: BenchmarkRunResult) -> dict[str, Any]:
    def _case(s: CaseScore) -> dict[str, Any]:
        d = asdict(s)
        return d

    return {
        "run_id": result.run_id,
        "dataset_id": result.dataset_id,
        "dataset_version": result.dataset_version,
        "provider_id": result.provider_id,
        "workflow_id": result.workflow_id,
        "overall_score": result.overall_score,
        "passed": result.passed,
        "latency_avg_ms": result.latency_avg_ms,
        "cost_total_usd": result.cost_total_usd,
        "skill_scores": _skill_scores(result),
        "case_scores": [_case(s) for s in result.case_scores],
        "calibration_curve": [asdict(b) for b in result.calibration_curve],
        "repeatability": [asdict(r) for r in result.repeatability],
        "recommendations": list(result.recommendations),
    }


def _skill_scores(result: BenchmarkRunResult) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for s in result.case_scores:
        buckets.setdefault(s.skill_id, []).append(s.overall)
    return {k: round(sum(v) / len(v), 4) for k, v in sorted(buckets.items())}


def render_json(result: BenchmarkRunResult, *, indent: int = 2) -> str:
    return json.dumps(result_to_dict(result), indent=indent) + "\n"


def render_markdown(result: BenchmarkRunResult) -> str:
    d = result_to_dict(result)
    lines = [
        f"# Benchmark Report — `{result.dataset_id}@{result.dataset_version}`",
        "",
        f"- **Run ID:** `{result.run_id}`",
        f"- **Provider:** `{result.provider_id}`",
        f"- **Workflow:** `{result.workflow_id}`",
        f"- **Overall score:** {result.overall_score:.4f}",
        f"- **Passed:** {'yes' if result.passed else 'no'}",
        f"- **Latency avg (ms):** {result.latency_avg_ms}",
        f"- **Estimated cost (USD):** {result.cost_total_usd}",
        "",
        "## Skill scores",
        "",
    ]
    for skill, score in d["skill_scores"].items():
        lines.append(f"- `{skill}`: {score:.4f}")
    lines.extend(["", "## Case scores", ""])
    lines.append("| Case | Overall | Findings | Citations | Schema | Calib | Pass |")
    lines.append("|------|---------|----------|-----------|--------|-------|------|")
    for s in result.case_scores:
        lines.append(
            f"| `{s.case_id}` | {s.overall:.3f} | {s.finding_accuracy:.3f} | "
            f"{s.citation_accuracy:.3f} | {s.schema_validity:.3f} | "
            f"{s.confidence_calibration:.3f} | {'Y' if s.passed else 'N'} |"
        )
    lines.extend(["", "## Calibration curve", ""])
    for b in result.calibration_curve:
        lines.append(
            f"- **{b.label}**: n={b.count}, correct={b.correct}, accuracy={b.accuracy:.3f}"
        )
    if result.repeatability:
        lines.extend(["", "## Repeatability", ""])
        for r in result.repeatability:
            lines.append(
                f"- `{r.case_id}`: identical={r.identical_output_rate:.3f}, "
                f"score_var={r.score_variance}, conf_var={r.confidence_variance}, "
                f"cite_var={r.citation_variance}"
            )
    lines.extend(["", "## Recommendations", ""])
    for tip in result.recommendations:
        lines.append(f"- {tip}")
    lines.append("")
    return "\n".join(lines)


def render_html(result: BenchmarkRunResult) -> str:
    d = result_to_dict(result)
    rows = []
    for s in result.case_scores:
        rows.append(
            "<tr>"
            f"<td>{html.escape(s.case_id)}</td>"
            f"<td>{s.overall:.3f}</td>"
            f"<td>{s.finding_accuracy:.3f}</td>"
            f"<td>{s.citation_accuracy:.3f}</td>"
            f"<td>{s.schema_validity:.3f}</td>"
            f"<td>{s.confidence_calibration:.3f}</td>"
            f"<td>{'Y' if s.passed else 'N'}</td>"
            "</tr>"
        )
    skill_lis = "".join(
        f"<li><code>{html.escape(k)}</code>: {v:.4f}</li>" for k, v in d["skill_scores"].items()
    )
    calib = "".join(
        f"<li><strong>{html.escape(b.label)}</strong>: n={b.count}, "
        f"accuracy={b.accuracy:.3f}</li>"
        for b in result.calibration_curve
    )
    tips = "".join(f"<li>{html.escape(t)}</li>" for t in result.recommendations)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Benchmark {html.escape(result.dataset_id)}</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem; color: #1a1a1a; background: #f7f5f1; }}
    h1,h2 {{ font-family: "Segoe UI", sans-serif; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
    th {{ background: #ece8e1; }}
    .meta {{ margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>Benchmark Report</h1>
  <div class="meta">
    <div><strong>Dataset:</strong> {html.escape(result.dataset_id)}@{html.escape(result.dataset_version)}</div>
    <div><strong>Provider:</strong> {html.escape(result.provider_id)}</div>
    <div><strong>Workflow:</strong> {html.escape(result.workflow_id)}</div>
    <div><strong>Overall:</strong> {result.overall_score:.4f}
      ({'PASS' if result.passed else 'FAIL'})</div>
    <div><strong>Latency avg:</strong> {result.latency_avg_ms} ms</div>
    <div><strong>Cost:</strong> ${result.cost_total_usd}</div>
  </div>
  <h2>Skill scores</h2>
  <ul>{skill_lis}</ul>
  <h2>Case scores</h2>
  <table>
    <thead><tr><th>Case</th><th>Overall</th><th>Findings</th><th>Citations</th>
    <th>Schema</th><th>Calib</th><th>Pass</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <h2>Calibration</h2>
  <ul>{calib}</ul>
  <h2>Recommendations</h2>
  <ul>{tips}</ul>
</body>
</html>
"""


def write_reports(
    result: BenchmarkRunResult,
    output_dir: str | Path,
    *,
    stem: str | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = stem or f"{result.dataset_id}_{result.run_id}"
    paths = {
        "json": out / f"{name}.json",
        "markdown": out / f"{name}.md",
        "html": out / f"{name}.html",
    }
    paths["json"].write_text(render_json(result), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(result), encoding="utf-8")
    paths["html"].write_text(render_html(result), encoding="utf-8")
    return paths
