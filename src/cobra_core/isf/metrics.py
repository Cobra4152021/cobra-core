"""ISF observability (bounded labels only)."""

from __future__ import annotations

import threading
from collections import Counter
from typing import Any

_ALLOWED_SKILLS = frozenset(
    {
        "vehicle_damage_assessment",
        "policy_compliance_review",
        "contract_analysis",
        "budget_analysis",
        "evidence_summary",
        "timeline_construction",
        "pattern_detection",
        "open_source_research",
        "interview_summary",
        "document_comparison",
        "unknown",
    }
)
_ALLOWED_STATUS = frozenset(
    {
        "completed",
        "needs_human_review",
        "missing_required_evidence",
        "failed",
        "structured_output_invalid",
        "skill_not_found",
        "skill_version_unsupported",
        "routing_failed",
        "other",
    }
)
_ALLOWED_PROVIDERS = frozenset({"mock", "openai", "unknown", "none"})
_ALLOWED_SCHEMA_RESULT = frozenset({"valid", "invalid", "repaired", "skipped", "unknown"})


def _bound(value: str, allowed: frozenset[str], default: str) -> str:
    key = (value or default).strip().lower()
    return key if key in allowed else default


class IsfMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.execution_total = 0
        self.execution_success = 0
        self.execution_failure = 0
        self.missing_evidence = 0
        self.schema_validation_failure = 0
        self.schema_repair = 0
        self.schema_repair_failure = 0
        self.low_confidence = 0
        self.human_review_required = 0
        self.latency_ms_sum = 0
        self.latency_ms_count = 0
        self.skill_selections: Counter[str] = Counter()
        self.status_counts: Counter[str] = Counter()
        self.provider_counts: Counter[str] = Counter()
        self.schema_results: Counter[str] = Counter()

    def record(
        self,
        *,
        skill_id: str,
        status: str,
        provider_id: str | None,
        schema_result: str,
        success: bool,
        missing_evidence: bool = False,
        schema_failure: bool = False,
        repair_attempted: bool = False,
        repair_failed: bool = False,
        low_confidence: bool = False,
        human_review: bool = False,
        latency_ms: int = 0,
    ) -> None:
        with self._lock:
            self.execution_total += 1
            if success:
                self.execution_success += 1
            else:
                self.execution_failure += 1
            if missing_evidence:
                self.missing_evidence += 1
            if schema_failure:
                self.schema_validation_failure += 1
            if repair_attempted:
                self.schema_repair += 1
            if repair_failed:
                self.schema_repair_failure += 1
            if low_confidence:
                self.low_confidence += 1
            if human_review:
                self.human_review_required += 1
            self.latency_ms_sum += max(0, int(latency_ms))
            self.latency_ms_count += 1
            self.skill_selections[_bound(skill_id, _ALLOWED_SKILLS, "unknown")] += 1
            self.status_counts[_bound(status, _ALLOWED_STATUS, "other")] += 1
            self.provider_counts[_bound(provider_id or "none", _ALLOWED_PROVIDERS, "unknown")] += 1
            self.schema_results[_bound(schema_result, _ALLOWED_SCHEMA_RESULT, "unknown")] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = self.latency_ms_sum / self.latency_ms_count if self.latency_ms_count else 0.0
            return {
                "execution_total": self.execution_total,
                "execution_success": self.execution_success,
                "execution_failure": self.execution_failure,
                "missing_evidence": self.missing_evidence,
                "schema_validation_failure": self.schema_validation_failure,
                "schema_repair": self.schema_repair,
                "schema_repair_failure": self.schema_repair_failure,
                "low_confidence": self.low_confidence,
                "human_review_required": self.human_review_required,
                "latency_ms_avg": round(avg, 3),
                "skill_selections": dict(self.skill_selections),
                "status_counts": dict(self.status_counts),
                "provider_counts": dict(self.provider_counts),
                "schema_results": dict(self.schema_results),
            }

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP isf_execution_total ISF executions attempted",
                "# TYPE isf_execution_total counter",
                f"isf_execution_total {self.execution_total}",
                "# HELP isf_execution_success_total Successful ISF executions",
                "# TYPE isf_execution_success_total counter",
                f"isf_execution_success_total {self.execution_success}",
                "# HELP isf_execution_failure_total Failed ISF executions",
                "# TYPE isf_execution_failure_total counter",
                f"isf_execution_failure_total {self.execution_failure}",
                "# HELP isf_missing_evidence_total Missing-evidence failures",
                "# TYPE isf_missing_evidence_total counter",
                f"isf_missing_evidence_total {self.missing_evidence}",
                "# HELP isf_schema_validation_failure_total Schema validation failures",
                "# TYPE isf_schema_validation_failure_total counter",
                f"isf_schema_validation_failure_total {self.schema_validation_failure}",
                "# HELP isf_schema_repair_total Schema repair attempts",
                "# TYPE isf_schema_repair_total counter",
                f"isf_schema_repair_total {self.schema_repair}",
                "# HELP isf_schema_repair_failure_total Schema repair failures",
                "# TYPE isf_schema_repair_failure_total counter",
                f"isf_schema_repair_failure_total {self.schema_repair_failure}",
                "# HELP isf_low_confidence_total Results below confidence threshold",
                "# TYPE isf_low_confidence_total counter",
                f"isf_low_confidence_total {self.low_confidence}",
                "# HELP isf_human_review_required_total Human-review dispositions",
                "# TYPE isf_human_review_required_total counter",
                f"isf_human_review_required_total {self.human_review_required}",
                "# HELP isf_execution_latency_ms ISF execution latency",
                "# TYPE isf_execution_latency_ms summary",
                f"isf_execution_latency_ms_sum {self.latency_ms_sum}",
                f"isf_execution_latency_ms_count {self.latency_ms_count}",
                "# HELP isf_skill_selection_total Selections by bounded skill_id",
                "# TYPE isf_skill_selection_total counter",
            ]
            for skill, n in sorted(self.skill_selections.items()):
                lines.append(f'isf_skill_selection_total{{skill_id="{skill}"}} {n}')
            return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self.execution_total = 0
            self.execution_success = 0
            self.execution_failure = 0
            self.missing_evidence = 0
            self.schema_validation_failure = 0
            self.schema_repair = 0
            self.schema_repair_failure = 0
            self.low_confidence = 0
            self.human_review_required = 0
            self.latency_ms_sum = 0
            self.latency_ms_count = 0
            self.skill_selections.clear()
            self.status_counts.clear()
            self.provider_counts.clear()
            self.schema_results.clear()


ISF_METRICS = IsfMetrics()
