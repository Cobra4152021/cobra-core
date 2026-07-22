"""Tests for blind label generation."""

from __future__ import annotations

import pytest

from cobra_core.evaluation.comparison import blind_model_label


def test_blind_labels_sequence() -> None:
    assert blind_model_label(0) == "Model-A"
    assert blind_model_label(1) == "Model-B"
    assert blind_model_label(2) == "Model-C"


def test_blind_label_rejects_negative_index() -> None:
    with pytest.raises(ValueError):
        blind_model_label(-1)
