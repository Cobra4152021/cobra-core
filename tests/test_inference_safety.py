"""Inference safety and result serialization unit tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cobra_core.inference.safety import (
    InferenceSafetyError,
    validate_request_limits,
    validate_token_budget,
)
from cobra_core.schemas.inference import ChatMessage, InferenceRequest, InferenceResult


def test_token_and_context_limits() -> None:
    validate_request_limits(
        InferenceRequest(user_prompt="hi", max_new_tokens=128),
        context_window=32768,
    )
    with pytest.raises(InferenceSafetyError):
        validate_request_limits(
            InferenceRequest(user_prompt="hi", max_new_tokens=4096),
            context_window=2048,
        )
    with pytest.raises(InferenceSafetyError):
        validate_token_budget(
            input_tokens=30000,
            max_new_tokens=5000,
            context_window=32768,
        )


def test_inference_result_serialization() -> None:
    result = InferenceResult(
        run_id="run-1",
        model_manifest_ref="model-cards/qwen/qwen3-8b.manifest.json",
        model_revision="b968826d9c46dd6066d109eabc6255188de91218",
        runtime="transformers",
        prompt_messages=[ChatMessage(role="user", content="hi")],
        rendered_chat_template="rendered",
        inference_settings={"temperature": 0.0},
        raw_generated_text="hi",
        assistant_response="hi",
        reasoning_content=None,
        input_token_count=1,
        output_token_count=1,
        total_token_count=2,
        total_latency_ms=10.0,
        tokens_per_second=100.0,
        finish_reason="completed",
        created_at=datetime.now(UTC),
        trust_remote_code=False,
    )
    data = result.model_dump(mode="json")
    assert data["trust_remote_code"] is False
    assert data["assistant_response"] == "hi"
    roundtrip = InferenceResult.model_validate(data)
    assert roundtrip.run_id == "run-1"


def test_smoke_result_parsing() -> None:
    from cobra_core.smoke.suite import SmokeSuiteResult, SmokeTestResult

    suite = SmokeSuiteResult(
        results=[
            SmokeTestResult("A", "basic", True, "ok"),
            SmokeTestResult("B", "json", False, "bad"),
        ]
    )
    payload = suite.to_dict()
    assert payload["passed_count"] == 1
    assert payload["total"] == 2
