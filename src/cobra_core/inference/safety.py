"""Resource-safety controls for local inference."""

from __future__ import annotations

from pathlib import Path

from cobra_core.acquisition.quarantine import assert_not_quarantined
from cobra_core.schemas.inference import InferenceRequest
from cobra_core.storage.paths import ModelStoragePaths


class InferenceSafetyError(ValueError):
    """Raised when a request violates safety limits."""


DEFAULT_MAX_INPUT_TOKENS = 4096
DEFAULT_MAX_NEW_TOKENS = 256
HARD_MAX_NEW_TOKENS = 4096


def validate_request_limits(
    request: InferenceRequest,
    *,
    context_window: int,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> None:
    if request.max_new_tokens < 1:
        raise InferenceSafetyError("max_new_tokens must be >= 1")
    if request.max_new_tokens > HARD_MAX_NEW_TOKENS:
        raise InferenceSafetyError(f"max_new_tokens exceeds hard cap {HARD_MAX_NEW_TOKENS}")
    if request.max_new_tokens > context_window:
        raise InferenceSafetyError("max_new_tokens exceeds model context_window")
    # Conservative: leave room for prompt + generation inside context window.
    if request.max_new_tokens > max_input_tokens:
        # not an error by itself; prompt length checked separately when tokenized
        pass


def validate_token_budget(
    *,
    input_tokens: int,
    max_new_tokens: int,
    context_window: int,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> None:
    if input_tokens > max_input_tokens:
        raise InferenceSafetyError(
            f"input_tokens {input_tokens} exceeds max_input_tokens {max_input_tokens}"
        )
    if input_tokens + max_new_tokens > context_window:
        raise InferenceSafetyError(
            f"context overflow: input ({input_tokens}) + max_new_tokens "
            f"({max_new_tokens}) > context_window ({context_window})"
        )


def validate_model_loadable(paths: ModelStoragePaths, manifest_status: str) -> None:
    assert_not_quarantined(paths)
    if manifest_status != "acquired":
        raise InferenceSafetyError(
            f"refusing to load model with acquisition_status={manifest_status!r}; "
            "require acquired/verified manifests"
        )
    if not paths.artifacts.is_dir() or not any(paths.artifacts.iterdir()):
        raise InferenceSafetyError(f"artifact path missing or empty: {paths.artifacts}")
    marker = paths.root / "QUARANTINED.json"
    if marker.exists():
        raise InferenceSafetyError("quarantine marker present")


def ensure_path_exists(path: Path) -> None:
    if not path.exists():
        raise InferenceSafetyError(f"invalid model path: {path}")
