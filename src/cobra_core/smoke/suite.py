"""Six technical smoke tests for acquired development models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cobra_core.inference.engine import LocalInferenceEngine
from cobra_core.schemas.inference import InferenceRequest
from cobra_core.schemas.manifest import ModelManifest


@dataclass
class SmokeTestResult:
    test_id: str
    name: str
    passed: bool
    detail: str
    unsupported: bool = False
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class SmokeSuiteResult:
    results: list[SmokeTestResult]
    run_ids: list[str] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for item in self.results if item.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed_count": self.passed_count,
            "total": len(self.results),
            "results": [item.__dict__ for item in self.results],
            "run_ids": self.run_ids,
        }


def run_smoke_suite(
    engine: LocalInferenceEngine,
    *,
    manifest: ModelManifest,
    manifest_ref: str,
    results_dir: Path,
    environment_reference: str | None,
) -> SmokeSuiteResult:
    results: list[SmokeTestResult] = []
    run_ids: list[str] = []

    def _run(test_id: str, name: str, request: InferenceRequest, checker: Any) -> None:
        try:
            result = engine.run(
                manifest=manifest,
                manifest_ref=manifest_ref,
                request=request,
                environment_reference=environment_reference,
                results_dir=results_dir,
                persist=True,
            )
            run_ids.append(result.run_id)
            ok, detail = checker(result)
            results.append(
                SmokeTestResult(
                    test_id=test_id,
                    name=name,
                    passed=ok,
                    detail=detail,
                    metrics={
                        "latency_ms": result.total_latency_ms,
                        "output_tokens": result.output_token_count,
                        "tps": result.tokens_per_second,
                    },
                )
            )
        except Exception as exc:
            results.append(
                SmokeTestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    detail=f"error: {exc}",
                )
            )

    # A — basic response
    _run(
        "A",
        "basic_response",
        InferenceRequest(
            system_prompt="Follow instructions exactly.",
            user_prompt="Reply with exactly: COBRA_MODEL_OK",
            max_new_tokens=32,
            temperature=0.0,
            seed=42,
            enable_thinking=False,
        ),
        lambda r: (
            "COBRA_MODEL_OK" in r.assistant_response,
            f"response={r.assistant_response!r}",
        ),
    )

    # B — structured JSON
    def _check_json(r: Any) -> tuple[bool, str]:
        text = r.assistant_response.strip()
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                return False, f"no JSON object found: {text!r}"
            obj = json.loads(text[start : end + 1])
            ok = obj.get("status") == "ok" and obj.get("code") == 1
            return ok, f"parsed={obj!r}"
        except Exception as exc:
            return False, f"json parse failed: {exc}; text={text!r}"

    _run(
        "B",
        "structured_json",
        InferenceRequest(
            system_prompt="Return JSON only.",
            user_prompt=(
                'Return a JSON object with keys "status" and "code" where '
                'status is "ok" and code is 1. No other text.'
            ),
            max_new_tokens=64,
            temperature=0.0,
            seed=42,
            enable_thinking=False,
        ),
        _check_json,
    )

    # C — context grounding
    passage = "SYNTHETIC PASSAGE: The warehouse crate label is SK-42 and it is stored on Shelf B."
    _run(
        "C",
        "context_grounding",
        InferenceRequest(
            system_prompt="Answer using only the provided passage.",
            user_prompt=(
                f"{passage}\n\nQuestion: What is the crate label? Answer with the label only."
            ),
            max_new_tokens=32,
            temperature=0.0,
            seed=42,
            enable_thinking=False,
        ),
        lambda r: (
            "SK-42" in r.assistant_response,
            f"response={r.assistant_response!r}",
        ),
    )

    # D — unsupported claim control
    _run(
        "D",
        "unsupported_claim_control",
        InferenceRequest(
            system_prompt="If the passage lacks the answer, say INSUFFICIENT_INFORMATION.",
            user_prompt=(
                "PASSAGE: The door is blue.\n\n"
                "Question: What is the night watchman's middle name?\n"
                "If unknown from the passage, reply exactly: INSUFFICIENT_INFORMATION"
            ),
            max_new_tokens=32,
            temperature=0.0,
            seed=42,
            enable_thinking=False,
        ),
        lambda r: (
            "INSUFFICIENT_INFORMATION" in r.assistant_response.upper()
            or "insufficient" in r.assistant_response.lower()
            or "not provided" in r.assistant_response.lower()
            or "cannot" in r.assistant_response.lower(),
            f"response={r.assistant_response!r}",
        ),
    )

    # E — determinism
    try:
        req = InferenceRequest(
            system_prompt="Be brief.",
            user_prompt="Say the word ALPHA once.",
            max_new_tokens=16,
            temperature=0.0,
            seed=123,
            enable_thinking=False,
        )
        r1 = engine.run(
            manifest=manifest,
            manifest_ref=manifest_ref,
            request=req,
            environment_reference=environment_reference,
            results_dir=results_dir,
            persist=True,
        )
        r2 = engine.run(
            manifest=manifest,
            manifest_ref=manifest_ref,
            request=req,
            environment_reference=environment_reference,
            results_dir=results_dir,
            persist=True,
        )
        run_ids.extend([r1.run_id, r2.run_id])
        same = r1.assistant_response == r2.assistant_response
        results.append(
            SmokeTestResult(
                test_id="E",
                name="determinism",
                passed=same,
                detail=(
                    f"match={same}; r1={r1.assistant_response!r}; r2={r2.assistant_response!r}. "
                    "Determinism is best-effort under Transformers/GPU kernels."
                ),
                metrics={"latency_ms_1": r1.total_latency_ms, "latency_ms_2": r2.total_latency_ms},
            )
        )
    except Exception as exc:
        results.append(
            SmokeTestResult(
                test_id="E",
                name="determinism",
                passed=False,
                detail=f"error: {exc}",
            )
        )

    # F — thinking mode
    try:
        off = engine.run(
            manifest=manifest,
            manifest_ref=manifest_ref,
            request=InferenceRequest(
                user_prompt="What is 2+2? Reply with the number only.",
                max_new_tokens=64,
                temperature=0.0,
                seed=7,
                enable_thinking=False,
            ),
            environment_reference=environment_reference,
            results_dir=results_dir,
            persist=True,
        )
        on = engine.run(
            manifest=manifest,
            manifest_ref=manifest_ref,
            request=InferenceRequest(
                user_prompt="What is 2+2? Reply with the number only.",
                max_new_tokens=128,
                temperature=0.6,
                seed=7,
                enable_thinking=True,
            ),
            environment_reference=environment_reference,
            results_dir=results_dir,
            persist=True,
        )
        run_ids.extend([off.run_id, on.run_id])
        mode_applied = (
            off.inference_settings.get("enable_thinking") is False
            and on.inference_settings.get("enable_thinking") is True
        )
        detail = (
            f"mode_flags_recorded={mode_applied}; "
            f"off_reasoning={off.reasoning_content!r}; on_reasoning_present="
            f"{on.reasoning_content is not None}; "
            "Quality of reasoning is not scored in smoke tests."
        )
        results.append(
            SmokeTestResult(
                test_id="F",
                name="thinking_mode",
                passed=mode_applied,
                detail=detail,
                unsupported=not mode_applied,
            )
        )
    except Exception as exc:
        results.append(
            SmokeTestResult(
                test_id="F",
                name="thinking_mode",
                passed=False,
                detail=f"error: {exc}",
                unsupported=True,
            )
        )

    return SmokeSuiteResult(results=results, run_ids=run_ids)
