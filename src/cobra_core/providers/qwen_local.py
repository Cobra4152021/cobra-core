"""Operational Qwen local adapter (Transformers)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from cobra_core.schemas.inference import ChatMessage, InferenceRequest, InferenceResult
from cobra_core.schemas.manifest import ModelManifest


class QwenLocalAdapter:
    """
    Qwen-specific local generation using official chat templates.

    ``trust_remote_code`` defaults to False. Qwen3 is supported by recent
    transformers without remote code.
    """

    provider_id = "qwen"
    trust_remote_code = False

    def __init__(self, *, load_in_4bit: bool = True) -> None:
        self.load_in_4bit = load_in_4bit
        self._model: Any = None
        self._tokenizer: Any = None
        self._artifact_dir: Path | None = None
        self._load_warnings: list[str] = []

    def is_configured(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._artifact_dir = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _ensure_loaded(self, artifact_dir: Path) -> None:
        if self._model is not None and self._artifact_dir == artifact_dir:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "torch/transformers required; install cobra-core[inference]"
            ) from exc

        self.unload()
        tokenizer = AutoTokenizer.from_pretrained(
            str(artifact_dir),
            trust_remote_code=self.trust_remote_code,
        )
        load_kwargs: dict[str, Any] = {
            "trust_remote_code": self.trust_remote_code,
            "device_map": "auto",
        }
        warnings: list[str] = []
        if self.load_in_4bit:
            try:
                from transformers import BitsAndBytesConfig

                load_kwargs["quantization_config"] = BitsAndBytesConfig(  # type: ignore[no-untyped-call]
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                )
            except Exception as exc:
                warnings.append(
                    f"bitsandbytes 4-bit unavailable ({exc}); "
                    "falling back to float16 with GPU/CPU offload"
                )
                load_kwargs["torch_dtype"] = torch.float16
                load_kwargs["max_memory"] = {0: "10GiB", "cpu": "24GiB"}
        else:
            load_kwargs["torch_dtype"] = (
                torch.bfloat16 if torch.cuda.is_available() else torch.float32
            )

        try:
            model = AutoModelForCausalLM.from_pretrained(str(artifact_dir), **load_kwargs)
        except Exception as exc:
            if "quantization_config" in load_kwargs:
                warnings.append(f"4-bit load failed ({exc}); retrying float16 offload")
                load_kwargs.pop("quantization_config", None)
                load_kwargs["torch_dtype"] = torch.float16
                load_kwargs["max_memory"] = {0: "10GiB", "cpu": "24GiB"}
                model = AutoModelForCausalLM.from_pretrained(str(artifact_dir), **load_kwargs)
            else:
                raise
        self._load_warnings = warnings
        eval_fn = getattr(model, "eval", None)
        if callable(eval_fn):
            eval_fn()
        self._tokenizer = tokenizer
        self._model = model
        self._artifact_dir = artifact_dir

    def generate_local(
        self,
        *,
        artifact_dir: Path,
        manifest: ModelManifest,
        manifest_ref: str,
        request: InferenceRequest,
        messages: list[ChatMessage],
        run_id: str,
        environment_reference: str | None,
    ) -> InferenceResult:
        self._ensure_loaded(artifact_dir)
        assert self._tokenizer is not None and self._model is not None
        import torch

        warnings = list(getattr(self, "_load_warnings", []))
        enable_thinking = request.enable_thinking
        chat_messages = [{"role": m.role, "content": m.content} for m in messages]

        template_kwargs: dict[str, Any] = {
            "tokenize": False,
            "add_generation_prompt": True,
        }
        # Official Qwen3 chat template supports enable_thinking when provided.
        if enable_thinking is not None:
            template_kwargs["enable_thinking"] = enable_thinking
        try:
            rendered = self._tokenizer.apply_chat_template(chat_messages, **template_kwargs)
        except TypeError:
            # Older template signature without enable_thinking
            template_kwargs.pop("enable_thinking", None)
            rendered = self._tokenizer.apply_chat_template(chat_messages, **template_kwargs)
            if enable_thinking is not None:
                warnings.append(
                    "tokenizer chat template did not accept enable_thinking; "
                    "mode may not have been applied by template API"
                )

        inputs = self._tokenizer([rendered], return_tensors="pt")
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        input_len = int(inputs["input_ids"].shape[-1])

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": request.max_new_tokens,
            "do_sample": request.temperature > 0,
        }
        if request.temperature > 0:
            gen_kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            gen_kwargs["top_p"] = request.top_p
        if request.top_k is not None:
            gen_kwargs["top_k"] = request.top_k
        if request.repetition_penalty is not None:
            gen_kwargs["repetition_penalty"] = request.repetition_penalty
        if request.seed is not None and hasattr(torch, "manual_seed"):
            torch.manual_seed(request.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(request.seed)

        started = time.perf_counter()
        ttft: float | None = None
        try:
            with torch.inference_mode():
                output = self._model.generate(**inputs, **gen_kwargs)
        except torch.cuda.OutOfMemoryError as exc:
            self.unload()
            raise RuntimeError(f"CUDA OOM during generation: {exc}") from exc
        except KeyboardInterrupt:
            self.unload()
            raise
        total_ms = (time.perf_counter() - started) * 1000.0

        generated_ids = output[0][input_len:].tolist()
        raw_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)
        reasoning, answer = _split_qwen_thinking(raw_text)
        # Only trust split when enable_thinking True; otherwise keep reasoning null
        # if thinking was explicitly disabled.
        if enable_thinking is False:
            if reasoning:
                warnings.append(
                    "thinking-like markers appeared despite enable_thinking=False; "
                    "recording full text as assistant_response"
                )
                answer = raw_text
                reasoning = None
        elif enable_thinking is None:
            # Do not invent reasoning; only keep split if markers existed.
            pass

        out_tokens = len(generated_ids)
        tps = (out_tokens / (total_ms / 1000.0)) if total_ms > 0 else None
        try:
            transformers_version = metadata.version("transformers")
        except metadata.PackageNotFoundError:
            transformers_version = None

        return InferenceResult(
            run_id=run_id,
            model_manifest_ref=manifest_ref,
            model_revision=manifest.model_revision,
            runtime="transformers",
            prompt_messages=messages,
            rendered_chat_template=rendered,
            inference_settings={
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
                "max_new_tokens": request.max_new_tokens,
                "seed": request.seed,
                "enable_thinking": enable_thinking,
                "load_in_4bit": self.load_in_4bit,
                "trust_remote_code": self.trust_remote_code,
            },
            raw_generated_text=raw_text,
            assistant_response=answer,
            reasoning_content=reasoning,
            input_token_count=input_len,
            output_token_count=out_tokens,
            total_token_count=input_len + out_tokens,
            time_to_first_token_ms=ttft,
            total_latency_ms=total_ms,
            tokens_per_second=tps,
            finish_reason="completed",
            warnings=warnings,
            error=None,
            environment_reference=environment_reference,
            created_at=datetime.now(UTC),
            tokenizer_version=None,
            transformers_version=transformers_version,
            trust_remote_code=self.trust_remote_code,
        )


def _split_qwen_thinking(text: str) -> tuple[str | None, str]:
    """Split Qwen thinking blocks only when explicit markers are present."""
    start = text.find("<think>")
    end = text.find("</think>")
    if start != -1 and end != -1 and end > start:
        reasoning = text[start + len("<think>") : end].strip()
        answer = text[end + len("</think>") :].strip()
        return reasoning or None, answer
    return None, text.strip()
