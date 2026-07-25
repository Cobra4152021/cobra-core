"""
Parse provider responses into skill schemas.

Never accepts free-form text as a successful structured result.
Allows one controlled schema-repair attempt (caller-audited).
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.schemas import SCHEMA_BY_SKILL_ID, validate_skill_output

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_candidate(raw: str) -> str | None:
    """Pull JSON object/array from raw text or markdown fences."""
    text = (raw or "").strip()
    if not text:
        return None
    # Refusal heuristics (not treated as JSON success).
    low = text.lower()
    if low.startswith("i can't") or low.startswith("i cannot") or "as an ai" in low[:80]:
        return None
    m = _FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()
    # First object/array slice
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            return text[start : end + 1]
    return text if text[:1] in "{[" else None


def parse_provider_json(raw: str) -> dict[str, Any]:
    """Parse provider content into a dict; raise structured_output_invalid on failure."""
    candidate = extract_json_candidate(raw)
    if candidate is None:
        raise IsfError(
            IsfErrorCode.STRUCTURED_OUTPUT_INVALID,
            "provider response is empty, refused, or non-JSON",
        )
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise IsfError(
            IsfErrorCode.STRUCTURED_OUTPUT_INVALID,
            "provider response JSON is truncated or malformed",
        ) from exc
    if not isinstance(data, dict):
        raise IsfError(
            IsfErrorCode.STRUCTURED_OUTPUT_INVALID,
            "structured skill result must be a JSON object",
        )
    return data


def validate_or_raise(skill_schema_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return validate_skill_output(skill_schema_id, payload)
    except ValidationError as exc:
        raise IsfError(
            IsfErrorCode.STRUCTURED_OUTPUT_INVALID,
            "structured output failed schema validation",
        ) from exc
    except ValueError as exc:
        raise IsfError(IsfErrorCode.STRUCTURED_OUTPUT_INVALID, str(exc)[:160]) from exc


def schema_json_prompt(skill_schema_id: str) -> str:
    """Instruction fragment telling the provider to return schema-shaped JSON only."""
    model = SCHEMA_BY_SKILL_ID.get(skill_schema_id)
    if model is None:
        return "Return a single JSON object only."
    # Use JSON schema for fields; keep compact.
    schema = model.model_json_schema()
    return (
        "Return ONLY a single JSON object matching this JSON Schema. "
        "No markdown, no commentary.\n"
        f"{json.dumps(schema, separators=(',', ':'))}"
    )


def build_repair_prompt(skill_schema_id: str, *, prior_error: str) -> str:
    """One-shot repair instruction — same schema, no new facts."""
    return (
        f"{schema_json_prompt(skill_schema_id)}\n"
        "Repair the previous response to satisfy the schema. "
        "Do not invent missing facts; use empty lists/unknown where needed. "
        f"Prior validation issue (safe): {prior_error[:120]}"
    )
