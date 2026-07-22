"""Typed inference request/result schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Annotated[str, Field(min_length=1)]
    content: Annotated[str, Field(min_length=0)]


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_prompt: str | None = None
    user_prompt: str | None = None
    messages: list[ChatMessage] | None = None
    temperature: float = 0.0
    top_p: float | None = 1.0
    top_k: int | None = None
    repetition_penalty: float | None = None
    max_new_tokens: Annotated[int, Field(ge=1, le=4096)] = 128
    seed: int | None = None
    enable_thinking: bool | None = None
    device: str | None = None
    runtime: str | None = None


class InferenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    model_manifest_ref: str
    model_revision: str
    runtime: str
    prompt_messages: list[ChatMessage]
    rendered_chat_template: str | None = None
    inference_settings: dict[str, Any]
    raw_generated_text: str
    assistant_response: str
    reasoning_content: str | None = None
    input_token_count: int | None = None
    output_token_count: int | None = None
    total_token_count: int | None = None
    time_to_first_token_ms: float | None = None
    total_latency_ms: float | None = None
    tokens_per_second: float | None = None
    finish_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    environment_reference: str | None = None
    created_at: datetime
    tokenizer_version: str | None = None
    transformers_version: str | None = None
    trust_remote_code: bool = False
