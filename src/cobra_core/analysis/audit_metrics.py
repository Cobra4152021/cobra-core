"""Metrics helpers for heuristic and human-consistency audits."""

from __future__ import annotations

from collections.abc import Iterable

FORMAT_FAILURE_CLASSES = frozenset(
    {
        "semantic_failure",
        "syntactic_failure",
        "parser_failure",
        "ambiguous_requirement",
        "harmless_variation",
        "true_instruction_following_failure",
    }
)


def precision(true_positives: int, predicted_positives: int) -> float:
    if predicted_positives <= 0:
        return 0.0
    return true_positives / predicted_positives


def false_positive_rate(false_positives: int, labeled_negatives: int) -> float:
    """FPR among labeled non-true-unsupported items."""
    if labeled_negatives <= 0:
        return 0.0
    return false_positives / labeled_negatives


def mean_absolute_difference(pairs: Iterable[tuple[float, float]]) -> float:
    values = [abs(a - b) for a, b in pairs]
    if not values:
        return 0.0
    return sum(values) / len(values)


def validate_format_failure_class(label: str) -> bool:
    return label in FORMAT_FAILURE_CLASSES
