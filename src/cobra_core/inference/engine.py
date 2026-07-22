"""Provider-neutral local inference engine."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cobra_core.inference.safety import (
    DEFAULT_MAX_NEW_TOKENS,
    validate_model_loadable,
    validate_request_limits,
    validate_token_budget,
)
from cobra_core.schemas.inference import ChatMessage, InferenceRequest, InferenceResult
from cobra_core.schemas.manifest import AcquisitionStatus, ModelManifest
from cobra_core.storage.paths import resolve_model_paths
from cobra_core.util.redact import redact_secrets


class LocalInferenceEngine:
    """
    Provider-neutral facade over a configured local adapter.

    Adapters implement ``generate_local``.
    """

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def run(
        self,
        *,
        manifest: ModelManifest,
        manifest_ref: str,
        request: InferenceRequest,
        environment_reference: str | None = None,
        results_dir: Path | None = None,
        persist: bool = True,
    ) -> InferenceResult:
        if manifest.acquisition_status not in {
            AcquisitionStatus.ACQUIRED,
            AcquisitionStatus.VERIFIED,
        }:
            raise RuntimeError("manifest is not in acquired or verified state")
        paths = resolve_model_paths(
            manifest.provider,
            manifest.model_name,
            manifest.model_revision,
            model_home=None,
        )
        # Prefer explicit local_artifact_root from manifest when present.
        artifact_dir = (
            Path(manifest.local_artifact_root) if manifest.local_artifact_root else paths.artifacts
        )
        validate_model_loadable(paths, manifest.acquisition_status.value)
        if not artifact_dir.exists():
            raise RuntimeError(f"local artifact root missing: {artifact_dir}")

        req = request
        if req.max_new_tokens > DEFAULT_MAX_NEW_TOKENS and req.max_new_tokens > 256:
            # keep explicit user value but still enforce hard caps in safety
            pass
        validate_request_limits(req, context_window=manifest.context_window)

        messages = _normalize_messages(req)
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]

        result_obj = self.adapter.generate_local(
            artifact_dir=artifact_dir,
            manifest=manifest,
            manifest_ref=manifest_ref,
            request=req,
            messages=messages,
            run_id=run_id,
            environment_reference=environment_reference,
        )
        if not isinstance(result_obj, InferenceResult):
            raise TypeError("adapter.generate_local must return InferenceResult")
        result = result_obj
        if result.input_token_count is not None:
            validate_token_budget(
                input_tokens=result.input_token_count,
                max_new_tokens=req.max_new_tokens,
                context_window=manifest.context_window,
            )

        if persist and results_dir is not None:
            _persist_run(results_dir / run_id, result, messages)
        return result


def _normalize_messages(request: InferenceRequest) -> list[ChatMessage]:
    if request.messages:
        return list(request.messages)
    messages: list[ChatMessage] = []
    if request.system_prompt:
        messages.append(ChatMessage(role="system", content=request.system_prompt))
    if not request.user_prompt:
        raise ValueError("user_prompt or messages is required")
    messages.append(ChatMessage(role="user", content=request.user_prompt))
    return messages


def _persist_run(run_dir: Path, result: InferenceResult, messages: list[ChatMessage]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps(redact_secrets(result.model_dump(mode="json")), indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "prompt.json").write_text(
        json.dumps(
            redact_secrets({"messages": [m.model_dump() for m in messages]}),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "response.txt").write_text(result.assistant_response, encoding="utf-8")
    metrics = {
        "input_token_count": result.input_token_count,
        "output_token_count": result.output_token_count,
        "total_token_count": result.total_token_count,
        "total_latency_ms": result.total_latency_ms,
        "tokens_per_second": result.tokens_per_second,
        "time_to_first_token_ms": result.time_to_first_token_ms,
        "finish_reason": result.finish_reason,
    }
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "environment-reference.json").write_text(
        json.dumps({"environment_reference": result.environment_reference}, indent=2) + "\n",
        encoding="utf-8",
    )
