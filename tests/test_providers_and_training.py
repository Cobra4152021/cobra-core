"""Provider placeholders and training guards."""

from __future__ import annotations

import pytest

from cobra_core.inference.runner import InferenceNotAvailableError, InferenceRunner
from cobra_core.providers import (
    GenerationRequest,
    ProviderNotConfiguredError,
    get_provider,
    list_providers,
)
from cobra_core.training import TrainingNotEnabledError, assert_training_disabled


def test_providers_registered() -> None:
    assert list_providers() == ["gemma", "mistral", "qwen"]


def test_providers_not_configured() -> None:
    for provider_id in list_providers():
        provider = get_provider(provider_id)
        assert provider.is_configured() is False
        with pytest.raises(ProviderNotConfiguredError):
            provider.generate(
                GenerationRequest(system_prompt="s", user_prompt="u"),
            )


def test_inference_runner_blocked() -> None:
    runner = InferenceRunner(get_provider("qwen"))
    with pytest.raises(InferenceNotAvailableError):
        runner.run(GenerationRequest(system_prompt="s", user_prompt="u"))


def test_training_disabled() -> None:
    with pytest.raises(TrainingNotEnabledError):
        assert_training_disabled()
