"""CIAL provider adapters (Phase 2: mock + OpenAI-compatible)."""

from __future__ import annotations

from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider

__all__ = ["MockProvider", "OpenAICompatibleProvider"]
