"""
Inference service boundary for Protocol V1.

Separates model runtime from HTTP. Supports mock (default) and optional local
Qwen3-8B NF4 path via existing QwenLocalAdapter (no weight/quant changes).
"""

from __future__ import annotations

import concurrent.futures
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cobra_core.protocol_v1.config import ServerConfig
from cobra_core.protocol_v1.inference import (
    InferenceCancelledError,
    InferenceFailedError,
    InferenceResult,
    mock_complete,
    run_local_qwen,
    truncate_messages,
)
from cobra_core.protocol_v1.runtime_state import RuntimeState


@dataclass
class ServiceOutcome:
    ok: bool
    result: InferenceResult | None = None
    error_code: str | None = None
    error_message: str | None = None
    # Timing boundaries (monotonic, ms):
    # queue_ms: time waiting before worker start (0 when no queue)
    # inference_ms: time inside the inference backend
    # provider_latency_ms: queue + inference (+ thin service overhead)
    # total_ms: full handler-observed span (set by handler)
    queue_ms: int = 0
    inference_ms: int = 0
    provider_latency_ms: int = 0


class InferenceService:
    def __init__(self, cfg: ServerConfig, state: RuntimeState) -> None:
        self.cfg = cfg
        self.state = state
        self._adapter: Any | None = None
        self._manifest: Any | None = None
        self._artifact_dir: Path | None = None
        self._lock = threading.Lock()

    def ready(self) -> bool:
        return self.state.inference_ready

    def ensure_runtime(self) -> None:
        """Eager/lazy load for local mode. Mock mode is always ready."""
        if self.cfg.inference_mode in {"mock", "echo", "test"}:
            self.state.mark_loaded()
            return
        with self._lock:
            if self.state.model_loaded and self._adapter is not None:
                return
            try:
                self._load_local()
                self.state.mark_loaded()
            except Exception:
                # Never leak paths/exception text into API; store safe reason only.
                self.state.mark_load_failed("model_unavailable")
                raise InferenceFailedError(
                    "model_unavailable", "Model runtime is unavailable"
                ) from None

    def _load_local(self) -> None:
        from cobra_core.providers.qwen_local import QwenLocalAdapter
        from cobra_core.schemas.manifest import ModelManifest
        from cobra_core.storage.paths import resolve_model_paths

        manifest_path = Path("model-cards/qwen/qwen3-8b.manifest.json")
        # Resolve relative to repo root.
        repo = Path(__file__).resolve().parents[3]
        path = repo / manifest_path
        manifest = ModelManifest.model_validate_json(path.read_text(encoding="utf-8"))
        paths = resolve_model_paths(
            manifest.provider,
            manifest.model_name,
            manifest.model_revision,
            model_home=None,
        )
        artifact_dir = (
            Path(manifest.local_artifact_root) if manifest.local_artifact_root else paths.artifacts
        )
        adapter = QwenLocalAdapter(load_in_4bit=True)
        adapter._ensure_loaded(artifact_dir)  # noqa: SLF001 — reuse validated load path
        self._adapter = adapter
        self._manifest = manifest
        self._artifact_dir = artifact_dir

    def complete(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        *,
        cancel_event: threading.Event | None = None,
        timeout_ms: int | None = None,
    ) -> ServiceOutcome:
        """
        Run one inference with server-side timeout.

        Cancellation limitation: mock cooperatively checks cancel_event between
        sleep slices. Local GPU generate() is not hard-interrupted; a timed-out
        worker may finish in the background but its result is discarded.
        """
        deadline_ms = self.cfg.timeout_ms if timeout_ms is None else timeout_ms
        truncated, ctx_err = truncate_messages(messages, self.cfg.max_context)
        if ctx_err == "context_limit":
            return ServiceOutcome(
                ok=False,
                error_code="context_limit",
                error_message="Context limit exceeded",
            )

        # force_fail hook for tests only
        fail = getattr(self, "_force_fail", False)

        def _work() -> InferenceResult:
            if cancel_event is not None and cancel_event.is_set():
                raise InferenceCancelledError()
            if self.cfg.inference_mode in {"mock", "echo", "test"}:
                self.state.record_generation()
                return mock_complete(
                    truncated,
                    max_tokens,
                    delay_ms=self.cfg.mock_delay_ms,
                    cancel_event=cancel_event,
                    fail=bool(fail),
                )
            self.ensure_runtime()
            assert self._adapter is not None and self._artifact_dir is not None
            self.state.record_generation()
            return run_local_qwen(
                truncated,
                max_tokens,
                adapter=self._adapter,
                artifact_dir=self._artifact_dir,
                manifest=self._manifest,
            )

        queue_ms = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_work)
            try:
                result = fut.result(timeout=max(0.001, deadline_ms / 1000.0))
            except concurrent.futures.TimeoutError:
                if cancel_event is not None:
                    cancel_event.set()
                # Do not consume late result for the HTTP response.
                return ServiceOutcome(
                    ok=False,
                    error_code="timeout",
                    error_message="Cobra Core request timed out",
                    queue_ms=queue_ms,
                    inference_ms=deadline_ms,
                    provider_latency_ms=deadline_ms,
                )
            except InferenceCancelledError:
                return ServiceOutcome(
                    ok=False,
                    error_code="cancelled",
                    error_message="Request cancelled",
                    queue_ms=queue_ms,
                )
            except InferenceFailedError as exc:
                return ServiceOutcome(
                    ok=False,
                    error_code=exc.code,
                    error_message=exc.message,
                    queue_ms=queue_ms,
                )
            except Exception:
                return ServiceOutcome(
                    ok=False,
                    error_code="provider_error",
                    error_message="Inference failed",
                    queue_ms=queue_ms,
                )

        if cancel_event is not None and cancel_event.is_set():
            return ServiceOutcome(
                ok=False,
                error_code="cancelled",
                error_message="Request cancelled",
                queue_ms=queue_ms,
            )

        return ServiceOutcome(
            ok=True,
            result=result,
            queue_ms=queue_ms,
            inference_ms=result.inference_ms,
            provider_latency_ms=queue_ms + result.inference_ms,
        )
