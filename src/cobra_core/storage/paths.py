"""Centralized external model path resolution (weights never live in git)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_HOME_WINDOWS = Path("D:/cobra-models")
DEFAULT_MODEL_HOME_POSIX = Path.home() / "cobra-models"
ENV_MODEL_HOME = "COBRA_MODEL_HOME"

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def default_model_home() -> Path:
    """Return the default external model root for this platform."""
    if os.name == "nt":
        return DEFAULT_MODEL_HOME_WINDOWS
    return DEFAULT_MODEL_HOME_POSIX


def get_model_home(override: str | Path | None = None) -> Path:
    """Resolve COBRA_MODEL_HOME or platform default."""
    if override is not None:
        return Path(override).expanduser().resolve()
    env_value = os.environ.get(ENV_MODEL_HOME)
    if env_value:
        return Path(env_value).expanduser().resolve()
    return default_model_home().expanduser().resolve()


def _require_safe_segment(value: str, field_name: str) -> str:
    cleaned = value.strip().replace("/", "-").replace("\\", "-")
    if not _SAFE_SEGMENT.match(cleaned):
        raise ValueError(f"unsafe {field_name} for storage path: {value!r}")
    return cleaned


@dataclass(frozen=True)
class ModelStoragePaths:
    """Layout under the external model root for one pinned revision."""

    model_home: Path
    provider: str
    model_slug: str
    revision: str
    root: Path
    artifacts: Path
    provenance: Path
    hashes: Path
    quarantine: Path
    download_state: Path

    def ensure_layout(self) -> None:
        for path in (
            self.root,
            self.artifacts,
            self.provenance,
            self.hashes,
            self.quarantine,
            self.download_state,
        ):
            path.mkdir(parents=True, exist_ok=True)


def resolve_model_paths(
    provider: str,
    model_name: str,
    revision: str,
    *,
    model_home: str | Path | None = None,
) -> ModelStoragePaths:
    """
    Build the external storage layout for a provider/model/revision.

    Example:
      D:/cobra-models/qwen/qwen3-8b/<revision>/artifacts
    """
    home = get_model_home(model_home)
    provider_seg = _require_safe_segment(provider.lower(), "provider")
    slug = _require_safe_segment(model_name.lower().replace(" ", "-"), "model_name")
    rev = _require_safe_segment(revision, "revision")
    root = home / provider_seg / slug / rev
    return ModelStoragePaths(
        model_home=home,
        provider=provider_seg,
        model_slug=slug,
        revision=rev,
        root=root,
        artifacts=root / "artifacts",
        provenance=root / "provenance",
        hashes=root / "hashes",
        quarantine=root / "quarantine",
        download_state=root / "download-state",
    )


def assert_outside_repo(path: Path, repo_root: Path) -> None:
    """Raise if a model path resolves inside the git repository."""
    resolved = path.resolve()
    repo = repo_root.resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return
    raise ValueError(f"model path must not be inside the git repository: {resolved}")
