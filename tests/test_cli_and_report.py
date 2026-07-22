"""CLI and report template tests."""

from __future__ import annotations

from pathlib import Path

from cobra_core.cli import report_template_main, validate_cases_main, validate_manifests_main
from cobra_core.evaluation.report_template import write_empty_report_template


def test_validate_cases_cli_ok() -> None:
    assert validate_cases_main([]) == 0


def test_validate_manifests_cli_ok() -> None:
    assert validate_manifests_main([]) == 0


def test_report_template_written(tmp_path: Path) -> None:
    out = tmp_path / "TEMPLATE.md"
    path = write_empty_report_template(out)
    text = path.read_text(encoding="utf-8")
    assert "EMPTY TEMPLATE" in text
    assert "LLM-as-judge" in text
    assert "Investigation reasoning" in text
    assert report_template_main(["--output", str(out)]) == 0
