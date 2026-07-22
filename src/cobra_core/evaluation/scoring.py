"""Category-preserving score aggregation.

Overall scores are derived summaries only. Category detail is always retained.
LLM-as-judge scores are advisory and must not silently overwrite objective/rule/human scores.
"""

from __future__ import annotations

from collections import defaultdict

from cobra_core.schemas.categories import CATEGORY_WEIGHTS, BenchmarkCategory
from cobra_core.schemas.evaluation import EvaluatorKind, EvaluatorScore, ScoreBreakdown

# Prefer non-advisory evidence when aggregating a category.
_KIND_PRIORITY: dict[EvaluatorKind, int] = {
    EvaluatorKind.OBJECTIVE: 4,
    EvaluatorKind.RULE_BASED: 3,
    EvaluatorKind.HUMAN: 2,
    EvaluatorKind.LLM_AS_JUDGE: 1,
}


def aggregate_category_scores(scores: list[EvaluatorScore]) -> ScoreBreakdown:
    """
    Aggregate evaluator scores into a category breakdown.

    For each category, select the highest-priority non-conflicting evidence.
    LLM-as-judge is used only when no objective/rule/human score exists.
    """
    by_category: dict[BenchmarkCategory, list[EvaluatorScore]] = defaultdict(list)
    for score in scores:
        by_category[score.category].append(score)

    selected: dict[BenchmarkCategory, float] = {}
    notes_parts: list[str] = []

    for category, items in by_category.items():
        ranked = sorted(
            items,
            key=lambda s: (_KIND_PRIORITY[s.kind], 0 if s.is_advisory else 1, s.score),
            reverse=True,
        )
        chosen = ranked[0]
        selected[category] = chosen.score
        if chosen.kind == EvaluatorKind.LLM_AS_JUDGE:
            notes_parts.append(
                f"{category.value}: using advisory LLM-as-judge score "
                "(not ground truth; requires human review)"
            )

    return ScoreBreakdown(
        by_category=selected,
        weights_applied=dict(CATEGORY_WEIGHTS),
        notes="; ".join(notes_parts) if notes_parts else None,
    )
