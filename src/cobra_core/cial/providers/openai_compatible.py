"""
OpenAI-compatible CIAL provider (KC-020).

Reference adapter for future providers. Uses chat completions over an
OpenAI-compatible HTTP API. No streaming, tools, or vision.
Credentials never leave the Core process and are never logged.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urljoin

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState
from cobra_core.cial.providers.http_transport import (
    HttpResponse,
    HttpTransport,
    UrllibTransport,
    encode_json,
)
from cobra_core.cial.types import (
    GenerateRequest,
    InferenceResult,
    LatencyTier,
    ModelRecord,
    QualityTier,
)

PROVIDER_ID = "openai"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2

# Retryable HTTP statuses (no auth/client errors).
_RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


def _join_url(base: str, path: str) -> str:
    base_n = base if base.endswith("/") else base + "/"
    return urljoin(base_n, path.lstrip("/"))


def map_http_status_to_cial(status: int) -> CialErrorCode:
    """Map provider HTTP status codes into the CIAL taxonomy."""
    if status in {401, 403}:
        return CialErrorCode.AUTHENTICATION_FAILED
    if status == 404:
        return CialErrorCode.MODEL_NOT_FOUND
    if status in {408}:
        return CialErrorCode.TIMEOUT
    if status == 429:
        return CialErrorCode.RATE_LIMITED
    if status in {500, 502, 503, 504}:
        return CialErrorCode.PROVIDER_UNAVAILABLE
    if 400 <= status < 500:
        return CialErrorCode.INFERENCE_FAILED
    return CialErrorCode.PROVIDER_UNAVAILABLE


def _uses_max_completion_tokens(model_id: str) -> bool:
    """Newer OpenAI chat models require max_completion_tokens instead of max_tokens."""
    mid = (model_id or "").strip().lower()
    return mid.startswith(("gpt-5", "o1", "o3", "o4"))


def _safe_error_message(status: int, body: bytes | None = None) -> str:
    """Non-leaking operator message (no prompts, keys, or raw bodies)."""
    base = f"openai-compatible provider HTTP {status}"
    if not body:
        return base
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return base
    if not isinstance(data, dict):
        return base
    err = data.get("error")
    if not isinstance(err, dict):
        return base
    # Allowlist short machine codes only (never message text — may echo prompts).
    code = err.get("code")
    err_type = err.get("type")
    bits: list[str] = []
    if isinstance(code, str) and code.isascii() and len(code) <= 64:
        bits.append(f"code={code}")
    if isinstance(err_type, str) and err_type.isascii() and len(err_type) <= 64:
        bits.append(f"type={err_type}")
    return f"{base} ({', '.join(bits)})" if bits else base


class OpenAICompatibleProvider:
    """CIAL adapter for OpenAI-compatible `/chat/completions` endpoints."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        model_id: str = DEFAULT_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: HttpTransport | None = None,
        enabled: bool = True,
        revision: str = "openai-compatible-v1",
    ) -> None:
        self._provider_id = PROVIDER_ID
        self._api_key = (api_key or "").strip()
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._model_id = (model_id or DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self._timeout_seconds = float(timeout_seconds)
        self._max_retries = max(0, int(max_retries))
        self._transport: HttpTransport = transport or UrllibTransport()
        self._enabled = enabled and bool(self._api_key)
        self._health = HealthState.UNKNOWN if self._enabled else HealthState.DISABLED
        self._model = ModelRecord(
            provider_id=PROVIDER_ID,
            model_id=self._model_id,
            display_name=f"OpenAI-compatible ({self._model_id})",
            enabled=self._enabled,
            capabilities=frozenset({Capability.TEXT, Capability.JSON}),
            context_window=128_000,
            max_output_tokens=16_384,
            supports_json=True,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=False,
            quality_tier=QualityTier.HIGH,
            latency_tier=LatencyTier.STANDARD,
            estimated_input_cost=None,
            estimated_output_cost=None,
            revision=revision,
            metadata={"api": "openai-compatible", "chat_completions": True},
            health=self._health,
        )

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def list_models(self) -> list[ModelRecord]:
        return [self._sync_model_record()]

    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.TEXT, Capability.JSON})

    def health(self) -> HealthState:
        return self._health

    def set_health(self, health: HealthState) -> None:
        self._health = health
        self._sync_model_record()

    def readiness_check(self) -> bool:
        return self.probe_health() in {
            HealthState.HEALTHY,
            HealthState.DEGRADED,
            HealthState.UNKNOWN,
        }

    def probe_health(self) -> HealthState:
        """
        Active health probe against GET /models.

        - no key → disabled
        - 200 → healthy
        - 429 / slow success path markers → degraded
        - auth failure / connection / 5xx → unavailable
        """
        if not self._api_key:
            self._health = HealthState.DISABLED
            self._sync_model_record()
            return self._health

        try:
            resp = self._transport.request(
                method="GET",
                url=_join_url(self._base_url, "models"),
                headers=self._headers(),
                body=None,
                timeout_seconds=min(self._timeout_seconds, 15.0),
            )
        except TimeoutError:
            self._health = HealthState.UNAVAILABLE
            self._sync_model_record()
            return self._health
        except OSError:
            # Connection refused / DNS / TLS — typed state only (no host leakage).
            self._health = HealthState.UNAVAILABLE
            self._sync_model_record()
            return self._health

        if resp.status == 200:
            self._health = HealthState.HEALTHY
        elif resp.status == 429:
            self._health = HealthState.DEGRADED
        elif resp.status in {401, 403} or resp.status >= 500:
            self._health = HealthState.UNAVAILABLE
        elif resp.status == 404:
            # Some gateways omit /models; treat as degraded (generate may still work).
            self._health = HealthState.DEGRADED
        else:
            self._health = HealthState.DEGRADED

        self._sync_model_record()
        return self._health

    def generate(self, request: GenerateRequest) -> InferenceResult:
        if not self._api_key:
            raise CialError(
                CialErrorCode.AUTHENTICATION_FAILED,
                "openai-compatible provider is not configured",
            )
        if request.model_id != self._model_id:
            raise CialError(
                CialErrorCode.MODEL_NOT_FOUND,
                "openai-compatible model not found",
            )
        if not self._enabled or self._health == HealthState.DISABLED:
            raise CialError(
                CialErrorCode.MODEL_DISABLED,
                "openai-compatible model is disabled",
            )
        if self._health == HealthState.UNAVAILABLE:
            raise CialError(
                CialErrorCode.PROVIDER_UNAVAILABLE,
                "openai-compatible provider is unavailable",
            )
        if request.cancel_event is not None and request.cancel_event.is_set():
            from cobra_core.protocol_v1.inference import InferenceCancelledError

            raise InferenceCancelledError()

        payload = self._build_payload(request)
        t0 = time.perf_counter()
        data = self._post_chat_completions(payload)
        elapsed = max(0, int(round((time.perf_counter() - t0) * 1000)))
        content, prompt_tokens, completion_tokens = self._parse_completion(data)

        return InferenceResult(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            inference_ms=elapsed,
            cial_provider_id=PROVIDER_ID,
            cial_model_id=request.model_id,
            cial_latency_ms=elapsed,
            cial_health_state=self._health.value,
        )

    def _build_payload(self, request: GenerateRequest) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        for msg in request.messages:
            role = str(msg.get("role") or "user")
            content = str(msg.get("content") or "")
            messages.append({"role": role, "content": content})

        payload: dict[str, Any] = {
            "model": request.model_id,
            "messages": messages,
            "stream": False,
        }
        # GPT-5 / o-series reject legacy max_tokens (HTTP 400); use max_completion_tokens.
        token_limit = int(request.max_tokens)
        if _uses_max_completion_tokens(request.model_id):
            payload["max_completion_tokens"] = token_limit
        else:
            payload["max_tokens"] = token_limit

        meta = request.metadata or {}
        if meta.get("json_mode") is True or meta.get("response_format") == "json_object":
            payload["response_format"] = {"type": "json_object"}
        elif isinstance(meta.get("response_format"), dict):
            # Pass-through only the OpenAI json_object shape; ignore unknown schemas.
            rf = meta["response_format"]
            if rf.get("type") == "json_object":
                payload["response_format"] = {"type": "json_object"}

        return payload

    def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = _join_url(self._base_url, "chat/completions")
        body = encode_json(payload)
        attempts = self._max_retries + 1
        last_error: CialError | None = None

        for attempt in range(attempts):
            try:
                resp = self._transport.request(
                    method="POST",
                    url=url,
                    headers=self._headers(),
                    body=body,
                    timeout_seconds=self._timeout_seconds,
                )
            except TimeoutError:
                last_error = CialError(CialErrorCode.TIMEOUT, "openai-compatible request timed out")
                if attempt + 1 >= attempts:
                    break
                self._backoff(attempt)
                continue
            except OSError:
                last_error = CialError(
                    CialErrorCode.PROVIDER_UNAVAILABLE,
                    "openai-compatible connection failure",
                )
                if attempt + 1 >= attempts:
                    break
                self._backoff(attempt)
                continue

            if resp.status == 200:
                return self._decode_json_object(resp)

            code = map_http_status_to_cial(resp.status)
            last_error = CialError(code, _safe_error_message(resp.status, resp.body))
            if resp.status in _RETRYABLE_STATUSES and attempt + 1 < attempts:
                self._backoff(attempt)
                continue
            raise last_error

        assert last_error is not None
        raise last_error

    def _decode_json_object(self, resp: HttpResponse) -> dict[str, Any]:
        try:
            data = json.loads(resp.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response is not valid JSON",
            ) from exc
        if not isinstance(data, dict):
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response schema is invalid",
            )
        return data

    def _parse_completion(self, data: dict[str, Any]) -> tuple[str, int, int]:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response schema is invalid",
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response schema is invalid",
            )
        message = first.get("message")
        if not isinstance(message, dict):
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response schema is invalid",
            )
        content = message.get("content")
        if content is None:
            raise CialError(
                CialErrorCode.INVALID_RESPONSE,
                "openai-compatible response schema is invalid",
            )
        text = content if isinstance(content, str) else json.dumps(content)

        usage_raw = data.get("usage")
        usage: dict[str, Any] = usage_raw if isinstance(usage_raw, dict) else {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        return text, prompt_tokens, completion_tokens

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _backoff(self, attempt: int) -> None:
        # Small deterministic backoff (tests may use max_retries=0 to skip).
        time.sleep(min(0.05 * (2**attempt), 0.4))

    def _sync_model_record(self) -> ModelRecord:
        self._model = ModelRecord(
            provider_id=self._model.provider_id,
            model_id=self._model.model_id,
            display_name=self._model.display_name,
            enabled=self._enabled,
            capabilities=self._model.capabilities,
            context_window=self._model.context_window,
            max_output_tokens=self._model.max_output_tokens,
            supports_json=self._model.supports_json,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=False,
            quality_tier=self._model.quality_tier,
            latency_tier=self._model.latency_tier,
            estimated_input_cost=self._model.estimated_input_cost,
            estimated_output_cost=self._model.estimated_output_cost,
            revision=self._model.revision,
            metadata=dict(self._model.metadata),
            health=self._health,
        )
        return self._model

    def __repr__(self) -> str:
        return (
            f"OpenAICompatibleProvider(model_id={self._model_id!r}, "
            f"base_url={self._base_url!r}, configured={self.configured}, "
            f"health={self._health.value!r})"
        )
