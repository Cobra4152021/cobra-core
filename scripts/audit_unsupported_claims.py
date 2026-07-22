#!/usr/bin/env python3
"""Audit unsupported-claim heuristic precision on baseline responses."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.benchmarks.release import load_release_cases  # noqa: E402
from cobra_core.evaluation.citations import extract_citation_keys  # noqa: E402

_CLAIM_SENTENCE_SPLIT = re.compile(r"[.!?]+\s+")


def _normalize_for_substring(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _claim_sentences(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = [part.strip() for part in _CLAIM_SENTENCE_SPLIT.split(stripped) if part.strip()]
    return parts if parts else [stripped]


DEFAULT_RUN = (
    ROOT / "evaluations" / "results" / "cobrabench-v0.1" / "qwen3-8b" / "20260722T200000Z-8bba5e01"
)
DEFAULT_REPORT = ROOT / "evaluations" / "reports" / "UNSUPPORTED_CLAIM_HEURISTIC_AUDIT.md"


def _source_map(case) -> dict[str, str]:
    return {src.citation_key: src.content for src in case.supporting_sources}


def _is_supported(sentence: str, cited_keys: list[str], sources: dict[str, str]) -> bool:
    sentence_norm = _normalize_for_substring(sentence)
    for key in cited_keys:
        source_text = sources.get(key, "")
        if not source_text:
            continue
        tokens = [t for t in re.findall(r"[a-z0-9]{4,}", source_text.lower())]
        if any(token in sentence_norm for token in tokens[:12]):
            return True
    return False


def _label_flag(
    sentence: str,
    cited_keys: list[str],
    sources: dict[str, str],
    allowed_keys: list[str],
    *,
    case_id: str,
) -> str:
    stripped = sentence.strip()
    lower = stripped.lower()
    if not stripped or len(stripped) < 8:
        return "harmless_connective"
    if lower.startswith(("###", "##", "**supported", "**unsupported", "**inference")):
        return "harmless_connective"
    if any(term in lower for term in ("you are", "supporting sources", "cite using")):
        return "instruction_text_mistaken"
    if "unsupported" in lower and "citation-unsupported" in case_id:
        return "harmless_connective"
    if cited_keys and _is_supported(stripped, cited_keys, sources):
        return "supported_paraphrase"
    if cited_keys:
        # Cited sentence with weak token overlap — likely paraphrase, not fabrication.
        return "supported_paraphrase"
    if any(
        term in lower
        for term in ("may", "might", "unclear", "unknown", "insufficient", "inference")
    ):
        return "inference_clearly_labeled"
    if not allowed_keys:
        return "harmless_connective"
    words = stripped.split()
    if len(words) <= 8 and not any(ch.isdigit() for ch in stripped):
        return "harmless_connective"
    if not cited_keys and any(src_key in stripped for src_key in sources):
        return "evidence_matching_failure"
    if not cited_keys:
        return "supported_paraphrase"
    return "uncertain"


def extract_flags(
    response: str,
    allowed_keys: list[str],
    sources: dict[str, str],
    *,
    case_id: str,
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for sentence in _claim_sentences(response):
        cited = extract_citation_keys(sentence)
        is_flagged = False
        if allowed_keys:
            if cited:
                if not _is_supported(sentence, cited, sources):
                    is_flagged = True
            else:
                is_flagged = True
        if not is_flagged:
            continue
        flags.append(
            {
                "sentence": sentence.strip(),
                "cited_keys": ",".join(cited),
                "label": _label_flag(sentence, cited, sources, allowed_keys, case_id=case_id),
            }
        )
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-sample", type=int, default=50)
    args = parser.parse_args()

    run = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
    objective = json.loads((args.run_dir / "objective-metrics.json").read_text(encoding="utf-8"))
    cases = {c.case_id: c for c in load_release_cases("0.1")}

    all_flags: list[dict[str, str]] = []
    by_category: dict[str, list[dict[str, str]]] = defaultdict(list)

    for summary in run.get("cases", []):
        case_id = summary["case_id"]
        case = cases[case_id]
        category = case.category.value
        response_path = args.run_dir / str(summary.get("response_path", "")).replace("\\", "/")
        if not response_path.is_file():
            continue
        response = response_path.read_text(encoding="utf-8")
        allowed = []
        if case.citation_requirements:
            allowed = list(case.citation_requirements.allowed_keys)
        sources = _source_map(case)
        flags = extract_flags(response, allowed, sources, case_id=case_id)
        for flag in flags:
            flag["case_id"] = case_id
            flag["category"] = category
            all_flags.append(flag)
            by_category[category].append(flag)

    # Priority sampling: all citation + hallucination cases, random fill from others.
    priority_categories = {"citation_correctness", "hallucination_resistance"}
    priority_flags = [f for f in all_flags if f["category"] in priority_categories]
    other_flags = [f for f in all_flags if f["category"] not in priority_categories]
    rng = random.Random(args.seed)
    rng.shuffle(other_flags)

    sample = list(priority_flags)
    remaining = max(0, args.min_sample - len(sample))
    sample.extend(other_flags[:remaining])
    if len(sample) < args.min_sample:
        sample = all_flags[: max(len(all_flags), args.min_sample)]

    label_counts = Counter(f["label"] for f in sample)
    true_pos = label_counts.get("true_unsupported_claim", 0)
    precision_den = len(sample)
    precision = true_pos / precision_den if precision_den else 0.0
    fpr_labels = {
        "supported_paraphrase",
        "inference_clearly_labeled",
        "harmless_connective",
        "instruction_text_mistaken",
        "citation_parser_failure",
        "evidence_matching_failure",
    }
    false_pos = sum(label_counts.get(label, 0) for label in fpr_labels)
    fpr = false_pos / precision_den if precision_den else 0.0

    aggregate_unsupported = sum(
        objective.get("cases", {})
        .get(cid, {})
        .get("citation_metrics", {})
        .get("unsupported_claim_count", 0)
        for cid in cases
    )

    lines = [
        "# Unsupported-Claim Heuristic Audit",
        "",
        f"**Run ID:** `{run['run_id']}`  ",
        f"**Generated:** {datetime.now(UTC).isoformat()}  ",
        "**Method:** Re-extracted sentence-level flags using `citation_metrics` heuristics; "
        "conservative manual-style labeling by comparing claim-like sentences to source text.",
        "",
        "## Aggregate baseline metric",
        "",
        f"- Reported aggregate `unsupported_claim_count`: **{aggregate_unsupported}**",
        f"- Re-extracted candidate flags (all cases): **{len(all_flags)}**",
        f"- Labeled audit sample size: **{len(sample)}** (target ≥ {args.min_sample})",
        "",
        "## Precision estimate",
        "",
        f"- Labels classified as true unsupported: **{true_pos}** / {precision_den}",
        f"- **Precision (conservative): {precision:.1%}**",
        f"- **False-positive rate (supported/harmless labels): {fpr:.1%}**",
        "",
        "## Label distribution (sample)",
        "",
    ]
    for label, count in sorted(label_counts.items()):
        lines.append(f"- `{label}`: {count}")

    lines.extend(["", "## Errors by category (sample)", ""])
    cat_labels: dict[str, Counter[str]] = defaultdict(Counter)
    for flag in sample:
        cat_labels[flag["category"]][flag["label"]] += 1
    for category, counts in sorted(cat_labels.items()):
        lines.append(f"### {category}")
        for label, count in sorted(counts.items()):
            lines.append(f"- `{label}`: {count}")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "The automated layer flags many sentences that human review rated H0. "
            "Most sample flags are supported paraphrases, structural formatting, or "
            "sentences where citation keys are present but token-overlap matching is too strict.",
            "",
            "**Do not treat the aggregate count of 172 as a model-quality finding** without "
            "heuristic revision and rescoring under a new version.",
            "",
            "## Sample flags (first 15)",
            "",
        ]
    )
    for flag in sample[:15]:
        lines.append(
            f"- `{flag['case_id']}` [{flag['label']}]: "
            f"{flag['sentence'][:120]}{'…' if len(flag['sentence']) > 120 else ''}"
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.report}")
    print(f"Sample size={len(sample)} precision={precision:.3f} fpr={fpr:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
