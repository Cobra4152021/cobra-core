"""Integration tests requiring an acquired local model.

These are excluded from the default quality suite:

    pytest -m \"not integration and not model_required\"
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cobra_core.schemas.manifest import AcquisitionStatus, ModelManifest

pytestmark = [pytest.mark.integration, pytest.mark.model_required, pytest.mark.gpu_optional]


def test_acquired_qwen3_8b_manifest_points_to_existing_artifacts(repo_root: Path) -> None:
    path = repo_root / "model-cards" / "qwen" / "qwen3-8b.manifest.json"
    manifest = ModelManifest.model_validate_json(path.read_text(encoding="utf-8"))
    if manifest.acquisition_status != AcquisitionStatus.ACQUIRED:
        pytest.skip("Qwen3-8B not acquired on this machine")
    assert manifest.local_artifact_root is not None
    root = Path(manifest.local_artifact_root)
    assert root.is_dir()
    assert (root / "LICENSE").is_file()
    assert any(root.glob("model-*.safetensors"))
