"""Typed evaluator versioning metadata (Phase 2F)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class EvaluatorMetadata(BaseModel):
    """Immutable identity for an evaluator implementation version."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evaluator_name: Annotated[str, Field(min_length=1)]
    evaluator_version: Annotated[str, Field(min_length=1)]
    implementation_version: Annotated[str, Field(min_length=1)]
    rule_set_version: Annotated[str, Field(min_length=1)]
    parser_version: Annotated[str, Field(min_length=1)]
    scoring_version: Annotated[str, Field(min_length=1)]
    configuration_hash: Annotated[str, Field(min_length=1)]
    creation_date: date
    compatibility_notes: str
    deprecated: bool = False
    replaces: str | None = None
    used_by_official_cobrabench_v01: bool = False
