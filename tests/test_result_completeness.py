"""Tests for CobraBench run artifact completeness and helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from cobra_core.evaluation.cobrabench_run import (
    REQUIRED_RUN_ARTIFACTS,
    REQUIRED_RUN_DIRS,
    detect_missing_human_review,
    generate_run_id,
    run_cobrabench,
    validate_score_in_range,
)
from cobra_core.schemas.benchmark import BenchmarkCase


def test_generate_run_id_format() -> None:
    run_id = generate_run_id()
    assert re.match(r"^\d{8}T\d{6}Z-[a-f0-9]{8}$", run_id)


def test_validate_score_in_range() -> None:
    validate_score_in_range(0.0)
    validate_score_in_range(1.0)
    with pytest.raises(ValueError):
        validate_score_in_range(1.1)


def test_detect_missing_human_review() -> None:
    assert detect_missing_human_review({"status": "pending", "scores": []}) is True
    assert detect_missing_human_review({"status": "complete", "scores": [{"score": 0.5}]}) is False


def test_dry_run_creates_required_files(
    repo_root: Path,
    primary_qwen_manifest_path: Path,
    tmp_path: Path,
) -> None:
    with patch("cobra_core.evaluation.cobrabench_run._results_root", return_value=tmp_path):
        run_dir = run_cobrabench(
            manifest_path=primary_qwen_manifest_path,
            model_slug="qwen3-32b-test",
            run_id="20260722T120000Z-deadbeef",
            case_ids=["cb-015-citation-key-discipline"],
            dry_run=True,
        )

    for name in REQUIRED_RUN_ARTIFACTS:
        assert (run_dir / name).is_file(), f"missing artifact {name}"
    for dirname in REQUIRED_RUN_DIRS:
        assert (run_dir / dirname).is_dir(), f"missing directory {dirname}"

    prompts = list((run_dir / "prompts").glob("*.json"))
    assert len(prompts) == 1
    human = json.loads((run_dir / "human-scores.json").read_text(encoding="utf-8"))
    assert human["status"] == "pending"
    assert detect_missing_human_review(human) is True


def test_failed_run_preserves_errors_json(
    repo_root: Path,
    primary_qwen_manifest_path: Path,
    tmp_path: Path,
) -> None:
    case = BenchmarkCase.model_validate_json(
        (
            repo_root
            / "benchmarks"
            / "releases"
            / "cobrabench-v0.1"
            / "cases"
            / "cb-015-citation-key-discipline.json"
        ).read_text(encoding="utf-8")
    )

    class _FailingEngine:
        def run(self, **_kwargs: object) -> None:
            raise RuntimeError("simulated inference failure")

    class _DummyAdapter:
        def __init__(self, **kwargs: object) -> None:
            _ = kwargs

        def unload(self) -> None:
            return None

    with (
        patch("cobra_core.evaluation.cobrabench_run._results_root", return_value=tmp_path),
        patch("cobra_core.evaluation.cobrabench_run.load_release_cases", return_value=[case]),
        patch("cobra_core.evaluation.cobrabench_run.ModelManifest") as manifest_cls,
        patch("cobra_core.providers.qwen_local.QwenLocalAdapter", _DummyAdapter),
        patch("cobra_core.inference.engine.LocalInferenceEngine", lambda adapter: _FailingEngine()),
    ):
        manifest_cls.model_validate_json.return_value = type(
            "M",
            (),
            {
                "model_name": "qwen3-32b",
                "model_revision": "rev",
                "provider": "qwen",
            },
        )()
        run_dir = run_cobrabench(
            manifest_path=primary_qwen_manifest_path,
            model_slug="qwen3-32b-test",
            run_id="20260722T120001Z-cafebabe",
            dry_run=False,
        )

    errors_doc = json.loads((run_dir / "errors.json").read_text(encoding="utf-8"))
    assert len(errors_doc["errors"]) == 1
    assert errors_doc["errors"][0]["case_id"] == case.case_id
    run_doc = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert run_doc["cases"][0]["status"] == "error"
