"""Strict and tolerant structured-output parsers (Phase 2F)."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class ParserMode(StrEnum):
    STRICT = "strict"
    TOLERANT = "tolerant"


class StructuredParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ParserMode
    success: bool
    fields: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    extra_fields: list[str] = Field(default_factory=list)
    transformations_applied: list[str] = Field(default_factory=list)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    unrecoverable_issues: list[str] = Field(default_factory=list)
    raw_text: str = ""
    normalized_text: str = ""


_LABEL_LINE = re.compile(
    r"^\s*(?:\*\*|__)?(?P<label>FINDING|RISK|NEXT|Finding|Risk|Next)"
    r"(?:\*\*|__)?\s*[:\-–—]\s*(?P<value>.+?)\s*$",
    re.MULTILINE,
)
_BULLET_LABEL = re.compile(
    r"^\s*[-*]\s*(?:\*\*|__)?(?P<label>FINDING|RISK|NEXT|Finding|Risk|Next)"
    r"(?:\*\*|__)?\s*[:\-–—]\s*(?P<value>.+?)\s*$",
    re.MULTILINE,
)


def _canon_label(label: str) -> str:
    return label.strip().upper()


def parse_finding_risk_next(
    text: str,
    *,
    mode: ParserMode = ParserMode.STRICT,
    required_fields: list[str] | None = None,
) -> StructuredParseResult:
    """
    Parse FINDING / RISK / NEXT structured answers.

    Tolerant mode may normalize markdown bullets, bold labels, whitespace,
    capitalization, and separators. It must not invent missing field content.
    """
    required = required_fields or ["FINDING", "RISK", "NEXT"]
    transformations: list[str] = []
    raw = text
    working = text.strip()

    if mode == ParserMode.TOLERANT:
        if re.search(r"\*\*[A-Za-z]+\*\*", working):
            transformations.append("strip_bold_markers")
        if re.search(r"^\s*[-*]\s+", working, flags=re.MULTILINE):
            transformations.append("accept_markdown_bullets")
        transformations.append("normalize_label_case")
        transformations.append("normalize_separators")

    fields: dict[str, str] = {}
    patterns = [_LABEL_LINE, _BULLET_LABEL] if mode == ParserMode.TOLERANT else [_LABEL_LINE]

    if mode == ParserMode.STRICT:
        # Strict: require LABEL: value lines without leading bullets/bold-only variants.
        strict_pat = re.compile(
            r"^(?P<label>FINDING|RISK|NEXT):\s*(?P<value>.+?)\s*$",
            re.MULTILINE,
        )
        patterns = [strict_pat]

    for pat in patterns:
        for match in pat.finditer(working):
            label = _canon_label(match.group("label"))
            value = match.group("value").strip()
            value = re.sub(r"^\*+|\*+$", "", value).strip()
            if label not in fields and value:
                fields[label] = value

    missing = [f for f in required if f not in fields or not fields[f].strip()]
    extras = [k for k in fields if k not in required]
    unrecoverable: list[str] = []
    if missing:
        unrecoverable.append(f"missing_fields:{','.join(missing)}")

    # Never invent content for missing fields.
    success = len(missing) == 0
    confidence = 0.95 if success and mode == ParserMode.STRICT else (0.8 if success else 0.2)

    normalized_lines = [f"{k}: {fields[k]}" for k in required if k in fields]
    return StructuredParseResult(
        mode=mode,
        success=success,
        fields=fields,
        missing_fields=missing,
        extra_fields=extras,
        transformations_applied=transformations,
        confidence=confidence,
        unrecoverable_issues=unrecoverable,
        raw_text=raw,
        normalized_text="\n".join(normalized_lines),
    )


def parse_result_as_dict(result: StructuredParseResult) -> dict[str, Any]:
    return result.model_dump(mode="json")
