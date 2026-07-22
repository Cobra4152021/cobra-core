"""CobraBench evaluation helpers."""

from cobra_core.evaluation.citations import citation_metrics, extract_citation_keys
from cobra_core.evaluation.cobrabench_run import (
    EVALUATOR_VERSION,
    REQUIRED_RUN_ARTIFACTS,
    REQUIRED_RUN_DIRS,
    build_user_prompt,
    detect_missing_human_review,
    generate_run_id,
    run_cobrabench,
    validate_score_in_range,
)
from cobra_core.evaluation.comparison import (
    blind_model_label,
    compare_category_scores,
    compare_weighted_totals,
    weighted_total,
)
from cobra_core.evaluation.contradiction import contradiction_metrics
from cobra_core.evaluation.hallucination import (
    HallucinationSeverity,
    classify_hallucination_severity,
)
from cobra_core.evaluation.refusal import refusal_metrics
from cobra_core.evaluation.report_template import write_empty_report_template
from cobra_core.evaluation.rule_checks import (
    run_objective_checks,
    run_rule_based_behavior_checks,
    score_from_checks,
)
from cobra_core.evaluation.scoring import aggregate_category_scores

__all__ = [
    "EVALUATOR_VERSION",
    "HallucinationSeverity",
    "REQUIRED_RUN_ARTIFACTS",
    "REQUIRED_RUN_DIRS",
    "aggregate_category_scores",
    "blind_model_label",
    "build_user_prompt",
    "citation_metrics",
    "classify_hallucination_severity",
    "compare_category_scores",
    "compare_weighted_totals",
    "contradiction_metrics",
    "detect_missing_human_review",
    "extract_citation_keys",
    "generate_run_id",
    "refusal_metrics",
    "run_cobrabench",
    "run_objective_checks",
    "run_rule_based_behavior_checks",
    "score_from_checks",
    "validate_score_in_range",
    "weighted_total",
    "write_empty_report_template",
]
