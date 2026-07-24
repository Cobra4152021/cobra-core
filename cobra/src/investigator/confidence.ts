/**
 * Confidence Engine (KC-004B).
 * Separates finding, evidence, recommendation, investigation confidence and readiness.
 */

import type { ConfidenceLevel, FindingDraft, RecommendationDraft } from "./types.js";
import type { EvidenceQualitySummary } from "./evidenceQuality.js";
import type { HypothesisDraft } from "./hypotheses.js";
import type { MissingEvidenceReport } from "./missingEvidence.js";
import type { ConflictItem } from "./findings.js";

export type ReadinessLevel = "ready" | "review_required" | "blocked_insufficient_evidence";

export interface ConfidenceBundle {
  findingConfidence: ConfidenceLevel;
  evidenceConfidence: ConfidenceLevel;
  recommendationConfidence: ConfidenceLevel;
  investigationConfidence: ConfidenceLevel;
  overallReadiness: ReadinessLevel;
  rationale: string[];
}

function rank(c: ConfidenceLevel): number {
  switch (c) {
    case "high":
      return 3;
    case "medium":
      return 2;
    case "low":
      return 1;
    default:
      return 0;
  }
}

function fromRank(n: number): ConfidenceLevel {
  if (n >= 3) return "high";
  if (n >= 2) return "medium";
  if (n >= 1) return "low";
  return "insufficient_evidence";
}

function majority(levels: ConfidenceLevel[]): ConfidenceLevel {
  if (!levels.length) return "insufficient_evidence";
  const avg = levels.reduce((a, c) => a + rank(c), 0) / levels.length;
  return fromRank(Math.round(avg));
}

function fromMeanScore(mean: number): ConfidenceLevel {
  if (mean >= 0.75) return "high";
  if (mean >= 0.55) return "medium";
  if (mean >= 0.35) return "low";
  return "insufficient_evidence";
}

export function buildConfidenceBundle(input: {
  findings: FindingDraft[];
  recommendations: RecommendationDraft[];
  evidenceQuality: EvidenceQualitySummary;
  hypotheses: HypothesisDraft[];
  missing: MissingEvidenceReport;
  conflicts: ConflictItem[];
}): ConfidenceBundle {
  const rationale: string[] = [];

  const findingConfidence = majority(input.findings.map((f) => f.confidence));
  rationale.push(`Finding confidence aggregated from ${input.findings.length} finding(s).`);

  const evidenceConfidence = fromMeanScore(input.evidenceQuality.meanOverall);
  rationale.push(
    `Evidence quality mean=${input.evidenceQuality.meanOverall} (high=${input.evidenceQuality.highQualityCount}, low=${input.evidenceQuality.lowQualityCount}).`,
  );

  const recommendationConfidence = majority(input.recommendations.map((r) => r.confidence));
  rationale.push(`Recommendation confidence from ${input.recommendations.length} recommendation(s).`);

  const activeHyps = input.hypotheses.filter((h) => h.status === "active");
  const hypCap =
    activeHyps.some((h) => h.confidence === "high") && input.conflicts.length === 0
      ? "high"
      : activeHyps.some((h) => rank(h.confidence) >= 2)
        ? "medium"
        : "low";

  const criticalMissing = input.missing.items.filter(
    (m) => m.priority === "critical" || m.priority === "high",
  ).length;

  let investigationRank = Math.min(
    rank(findingConfidence),
    rank(evidenceConfidence),
    rank(hypCap as ConfidenceLevel),
  );
  if (criticalMissing >= 2) investigationRank = Math.min(investigationRank, 1);
  if (input.evidenceQuality.scores.length === 0) investigationRank = 0;
  if (input.conflicts.length >= 2) investigationRank = Math.min(investigationRank, 2);

  const investigationConfidence = fromRank(investigationRank);

  let overallReadiness: ReadinessLevel = "ready";
  if (
    investigationConfidence === "insufficient_evidence" ||
    input.evidenceQuality.scores.length === 0 ||
    criticalMissing >= 3
  ) {
    overallReadiness = "blocked_insufficient_evidence";
    rationale.push("Readiness blocked: insufficient evidence or critical gaps.");
  } else if (
    criticalMissing > 0 ||
    input.conflicts.length > 0 ||
    findingConfidence === "low" ||
    investigationConfidence === "low" ||
    input.findings.some((f) => f.confidence === "insufficient_evidence")
  ) {
    overallReadiness = "review_required";
    rationale.push("Readiness = Review Required due to gaps, conflicts, or weak findings.");
  } else {
    rationale.push("Readiness = ready for publication review.");
  }

  return {
    findingConfidence,
    evidenceConfidence,
    recommendationConfidence,
    investigationConfidence,
    overallReadiness,
    rationale,
  };
}
