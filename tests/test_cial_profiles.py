"""Profile-centric CIAL activation tests."""

from __future__ import annotations

import pytest

from cobra_core.cial.config import CialConfigError, load_cial_config
from cobra_core.cial.profiles import (
    PROFILE_DEFAULT,
    PROFILE_OFFLINE,
    PROFILE_RESEARCH,
    resolve_profile,
)
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


def test_resolve_builtin_profiles() -> None:
    default = resolve_profile(PROFILE_DEFAULT, openai_model="gpt-x")
    assert default.provider_id == "mock"
    assert default.model_id == DEFAULT_MODEL
    assert default.requires_live is False

    offline = resolve_profile(PROFILE_OFFLINE, openai_model="gpt-x")
    assert offline.provider_id == "mock"
    assert offline.requires_live is False

    research = resolve_profile(PROFILE_RESEARCH, openai_model="gpt-x")
    assert research.provider_id == "openai"
    assert research.model_id == "gpt-x"
    assert research.requires_live is True


def test_profile_env_preferred_over_legacy_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIAL_PROFILE", "offline")
    monkeypatch.setenv("CIAL_PROVIDER", "openai")
    cfg = load_cial_config()
    assert cfg.active_profile == "offline"
    assert cfg.default_provider == "mock"


def test_legacy_provider_maps_to_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CIAL_PROFILE", raising=False)
    monkeypatch.setenv("CIAL_PROVIDER", "openai")
    cfg = load_cial_config()
    assert cfg.active_profile == "research"
    assert cfg.default_provider == "openai"


def test_unknown_profile_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIAL_PROFILE", "marketplace")
    with pytest.raises(CialConfigError):
        load_cial_config()
