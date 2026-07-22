"""Blinded model comparison helpers (no winner declaration)."""

from __future__ import annotations

from typing import Any

from cobra_core.schemas.categories import CATEGORY_WEIGHTS, BenchmarkCategory

_MATERIAL_DELTA = 0.05


def blind_model_label(index: int) -> str:
    """Return a blind label for side-by-side review (Model-A, Model-B, ...)."""
    if index < 0:
        raise ValueError("index must be non-negative")
    letter = chr(ord("A") + index)
    if letter > "Z":
        raise ValueError("index exceeds supported blind label range")
    return f"Model-{letter}"


def compare_category_scores(
    a: dict[str, float],
    b: dict[str, float],
    *,
    material_threshold: float = _MATERIAL_DELTA,
) -> dict[str, Any]:
    """
    Compare two category score maps and report material deltas.

    Does not declare a winner; reports signed deltas only.
    """
    categories = sorted(set(a) | set(b))
    deltas: dict[str, float] = {}
    material: dict[str, float] = {}
    for category in categories:
        delta = round(b.get(category, 0.0) - a.get(category, 0.0), 4)
        deltas[category] = delta
        if abs(delta) >= material_threshold:
            material[category] = delta

    return {
        "deltas_b_minus_a": deltas,
        "material_deltas": material,
        "material_threshold": material_threshold,
        "categories_compared": categories,
    }


def weighted_total(scores: dict[str, float]) -> float | None:
    """
    Compute weighted overall from category scores without declaring a winner.

    Returns None when required weighted categories are missing.
    """
    total = 0.0
    weight_sum = 0.0
    for category, weight in CATEGORY_WEIGHTS.items():
        key = category.value if isinstance(category, BenchmarkCategory) else str(category)
        if key not in scores:
            return None
        total += scores[key] * weight
        weight_sum += weight
    if weight_sum <= 0:
        return None
    return round(total / weight_sum, 4)


def compare_weighted_totals(a: dict[str, float], b: dict[str, float]) -> dict[str, Any]:
    """Report weighted totals and delta without winner language."""
    total_a = weighted_total(a)
    total_b = weighted_total(b)
    delta = None
    if total_a is not None and total_b is not None:
        delta = round(total_b - total_a, 4)
    return {
        "weighted_total_a": total_a,
        "weighted_total_b": total_b,
        "delta_b_minus_a": delta,
        "note": "Totals are derived summaries; category detail remains authoritative.",
    }
