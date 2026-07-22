"""Unit tests for storage, hashing, quarantine, and revision pinning."""

from __future__ import annotations

from pathlib import Path

import pytest

from cobra_core.acquisition.acquire import estimate_storage_gate, parse_hf_repo_id
from cobra_core.acquisition.hashing import format_sha256, sha256_file, write_sha256sums
from cobra_core.acquisition.inventory import build_inventory
from cobra_core.acquisition.quarantine import (
    QuarantinedModelError,
    assert_not_quarantined,
    is_quarantined,
    quarantine_acquisition,
)
from cobra_core.acquisition.revisions import UnpinnedRevisionError, assert_pinned_revision
from cobra_core.storage.paths import assert_outside_repo, get_model_home, resolve_model_paths
from cobra_core.util.redact import redact_secrets


def test_resolve_model_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_MODEL_HOME", str(tmp_path / "models"))
    paths = resolve_model_paths("qwen", "Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218")
    assert paths.model_slug == "qwen3-8b"
    assert paths.artifacts.name == "artifacts"
    assert get_model_home() == (tmp_path / "models").resolve()


def test_assert_outside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "models"
    outside.mkdir()
    assert_outside_repo(outside, repo)
    with pytest.raises(ValueError):
        assert_outside_repo(repo / "weights", repo)


def test_pinned_revision_enforcement() -> None:
    assert (
        assert_pinned_revision("b968826d9c46dd6066d109eabc6255188de91218")
        == "b968826d9c46dd6066d109eabc6255188de91218"
    )
    for bad in ("main", "latest", "HEAD", "master"):
        with pytest.raises(UnpinnedRevisionError):
            assert_pinned_revision(bad)


def test_sha256_and_inventory_ordering(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    (root / "b.txt").write_text("b", encoding="utf-8")
    (root / "a.txt").write_text("a", encoding="utf-8")
    digest_a = sha256_file(root / "a.txt")
    assert format_sha256(digest_a) == digest_a
    inv = build_inventory(
        root,
        model_name="demo",
        revision="abc1234",
        expected_paths=["a.txt", "b.txt", "missing.txt"],
    )
    assert [item.relative_path for item in inv.items] == ["a.txt", "b.txt"]
    assert inv.missing_expected == ["missing.txt"]
    assert inv.complete is False
    out = tmp_path / "SHA256SUMS"
    write_sha256sums([(item.relative_path, item.sha256 or "") for item in inv.items], out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].endswith("  a.txt")


def test_quarantine_blocks_inference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_MODEL_HOME", str(tmp_path))
    paths = resolve_model_paths("qwen", "Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218")
    paths.ensure_layout()
    (paths.artifacts / "LICENSE").write_text("Apache", encoding="utf-8")
    quarantine_acquisition(paths, reason="test_failure", details={"k": "v"})
    assert is_quarantined(paths)
    with pytest.raises(QuarantinedModelError):
        assert_not_quarantined(paths)


def test_storage_gate() -> None:
    ok = estimate_storage_gate(available_free_bytes=200 * 1024**3)
    assert ok["passed"] is True
    bad = estimate_storage_gate(available_free_bytes=1_000)
    assert bad["passed"] is False


def test_parse_hf_repo_and_redaction() -> None:
    assert parse_hf_repo_id("https://huggingface.co/Qwen/Qwen3-8B") == "Qwen/Qwen3-8B"
    payload = {
        "hf_token": "hf_secretvalue123456",
        "ok": "x",
        "nested": {"Authorization": "Bearer abc"},
    }
    red = redact_secrets(payload)
    assert red["hf_token"] == "[REDACTED]"
    assert red["nested"]["Authorization"] == "[REDACTED]"
    assert "hf_[REDACTED]" in redact_secrets("token=hf_abcdefghij")
