"""Tests for citation extraction and metrics."""

from __future__ import annotations

from cobra_core.evaluation.citations import citation_metrics, extract_citation_keys


def test_extract_citation_keys_order_and_unique() -> None:
    text = "Finding one [SRC-A]. Later SRC-B and SRC-A again."
    assert extract_citation_keys(text) == ["SRC-A", "SRC-B"]


def test_citation_metrics_precision_and_fabrication() -> None:
    response = "Claim A SRC-A. Claim B SRC-Z."
    metrics = citation_metrics(response, ["SRC-A", "SRC-B"], {"SRC-A": "alpha content"})
    assert metrics["citation_precision"] == 0.5
    assert metrics["fabricated_citation_count"] == 1
    assert metrics["fabricated_citation_keys"] == ["SRC-Z"]


def test_citation_coverage() -> None:
    response = "Only cites SRC-A."
    metrics = citation_metrics(response, ["SRC-A", "SRC-B"], {"SRC-A": "alpha", "SRC-B": "beta"})
    assert metrics["citation_coverage"] == 0.5


def test_overstatement_zero_when_sources_unknown() -> None:
    response = "This is definitely true without citation."
    metrics = citation_metrics(response, ["SRC-A"], supporting_source_texts=None)
    assert metrics["overstatement_count"] == 0
