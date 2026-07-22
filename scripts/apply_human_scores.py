#!/usr/bin/env python3
"""Merge human review scores into a CobraBench run directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.cobrabench_run import validate_score_in_range  # noqa: E402


def _load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records
    payload = json.loads(text)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "scores" in payload:
        scores = payload["scores"]
        if isinstance(scores, list):
            return scores
    raise ValueError("Expected JSON list, JSONL lines, or object with scores[]")


def _validate_record(record: dict[str, Any], index: int) -> None:
    score = record.get("score")
    if score is None:
        raise ValueError(f"record[{index}] missing score")
    validate_score_in_range(float(score), field_name=f"record[{index}].score")
    rationale = record.get("rationale")
    if not rationale or not str(rationale).strip():
        raise ValueError(f"record[{index}] missing non-empty rationale")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="CobraBench run directory containing human-scores.json",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Human scores JSON or JSONL file",
    )
    args = parser.parse_args(argv)

    run_dir = args.run_dir.resolve()
    target = run_dir / "human-scores.json"
    if not target.is_file():
        print(f"ERROR: missing {target}", file=sys.stderr)
        return 2

    records = _load_records(args.input)
    for index, record in enumerate(records):
        _validate_record(record, index)

    existing = json.loads(target.read_text(encoding="utf-8"))
    merged = {
        "status": "complete",
        "scores": records,
        "merged_from": str(args.input),
        "previous_status": existing.get("status"),
    }
    target.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"Merged {len(records)} human score(s) into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
