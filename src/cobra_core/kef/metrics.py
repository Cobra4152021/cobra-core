"""KEF metrics — bounded labels only."""

from __future__ import annotations

import threading
from collections import Counter
from typing import Any

_ALLOWED_CONNECTORS = frozenset({"memory", "mock", "evidence_vault", "unknown", "none", "multi"})
_ALLOWED_MODES = frozenset({"exact", "metadata", "semantic", "hybrid", "registry", "unknown"})
_ALLOWED_RESULT = frozenset({"success", "missing_required", "permission_denied", "error", "other"})
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


def _bound(value: str, allowed: frozenset[str], default: str) -> str:
    key = (value or default).strip().lower()
    return key if key in allowed else default


class KefMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.retrieval_total = 0
        self.lookup_total = 0
        self.connector_total = 0
        self.permission_denied_total = 0
        self.duplicate_removed_total = 0
        self.citations_generated_total = 0
        self.missing_required_evidence_total = 0
        self.latency_ms_sum = 0
        self.latency_ms_count = 0
        self._by_connector: Counter[str] = Counter()
        self._by_mode: Counter[str] = Counter()
        self._by_result: Counter[str] = Counter()
        self._by_skill: Counter[str] = Counter()

    def clear(self) -> None:
        with self._lock:
            self.retrieval_total = 0
            self.lookup_total = 0
            self.connector_total = 0
            self.permission_denied_total = 0
            self.duplicate_removed_total = 0
            self.citations_generated_total = 0
            self.missing_required_evidence_total = 0
            self.latency_ms_sum = 0
            self.latency_ms_count = 0
            self._by_connector.clear()
            self._by_mode.clear()
            self._by_result.clear()
            self._by_skill.clear()

    def record_retrieval(
        self,
        *,
        skill_id: str,
        connector: str,
        mode: str,
        result: str,
        returned_count: int,
        duplicates_removed: int,
        permission_denials: int,
        citations: int,
        missing_required: bool,
        latency_ms: int,
        is_lookup: bool = False,
    ) -> None:
        c = _bound(connector, _ALLOWED_CONNECTORS, "unknown")
        m = _bound(mode, _ALLOWED_MODES, "unknown")
        r = _bound(result, _ALLOWED_RESULT, "other")
        s = _bound(skill_id, _ALLOWED_SKILLS, "unknown")
        with self._lock:
            self.retrieval_total += 1
            if is_lookup:
                self.lookup_total += 1
            self.connector_total += 1
            self.permission_denied_total += max(0, permission_denials)
            self.duplicate_removed_total += max(0, duplicates_removed)
            self.citations_generated_total += max(0, citations)
            if missing_required:
                self.missing_required_evidence_total += 1
            self.latency_ms_sum += max(0, latency_ms)
            self.latency_ms_count += 1
            self._by_connector[c] += 1
            self._by_mode[m] += 1
            self._by_result[r] += 1
            self._by_skill[s] += 1
            _ = returned_count  # available for future histograms; not labeled

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = self.latency_ms_sum / self.latency_ms_count if self.latency_ms_count else 0.0
            return {
                "retrieval_total": self.retrieval_total,
                "lookup_total": self.lookup_total,
                "connector_total": self.connector_total,
                "permission_denied_total": self.permission_denied_total,
                "duplicate_removed_total": self.duplicate_removed_total,
                "citations_generated_total": self.citations_generated_total,
                "missing_required_evidence_total": self.missing_required_evidence_total,
                "average_retrieval_ms": round(avg, 3),
                "by_connector": dict(self._by_connector),
                "by_mode": dict(self._by_mode),
                "by_result": dict(self._by_result),
                "by_skill": dict(self._by_skill),
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# HELP kef_retrieval_total KEF retrieval requests",
            "# TYPE kef_retrieval_total counter",
            f"kef_retrieval_total {s['retrieval_total']}",
            "# HELP kef_lookup_total KEF exact lookups",
            "# TYPE kef_lookup_total counter",
            f"kef_lookup_total {s['lookup_total']}",
            "# HELP kef_connector_total KEF connector invocations",
            "# TYPE kef_connector_total counter",
            f"kef_connector_total {s['connector_total']}",
            "# HELP kef_permission_denied_total KEF permission denials",
            "# TYPE kef_permission_denied_total counter",
            f"kef_permission_denied_total {s['permission_denied_total']}",
            "# HELP kef_duplicate_removed_total Duplicate evidence collapsed",
            "# TYPE kef_duplicate_removed_total counter",
            f"kef_duplicate_removed_total {s['duplicate_removed_total']}",
            "# HELP kef_citations_generated_total Citations generated",
            "# TYPE kef_citations_generated_total counter",
            f"kef_citations_generated_total {s['citations_generated_total']}",
            "# HELP kef_missing_required_evidence_total Missing required evidence",
            "# TYPE kef_missing_required_evidence_total counter",
            f"kef_missing_required_evidence_total {s['missing_required_evidence_total']}",
            "# HELP kef_average_retrieval_ms Average KEF retrieval latency",
            "# TYPE kef_average_retrieval_ms gauge",
            f"kef_average_retrieval_ms {s['average_retrieval_ms']}",
        ]
        for connector, n in sorted(s["by_connector"].items()):
            lines.append(f'kef_retrieval_total{{connector_id="{connector}"}} {n}')
        for mode, n in sorted(s["by_mode"].items()):
            lines.append(f'kef_retrieval_total{{query_type="{mode}"}} {n}')
        for result, n in sorted(s["by_result"].items()):
            lines.append(f'kef_retrieval_total{{result="{result}"}} {n}')
        for skill, n in sorted(s["by_skill"].items()):
            lines.append(f'kef_retrieval_total{{skill_id="{skill}"}} {n}')
        return "\n".join(lines) + "\n"


KEF_METRICS = KefMetrics()
