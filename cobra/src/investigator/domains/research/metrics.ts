/** Research domain metrics (KC-009). */

export interface ResearchMetricCounts {
  evidenceCount: number;
  citedSourceCount: number;
  totalSourceCount: number;
  hypothesisCount: number;
  highConfidenceHypothesisCount: number;
  requiredCategoryCount: number;
  coveredCategoryCount: number;
  uniqueSourceKinds: number;
  totalSourceKinds: number;
  supportingRelations: number;
  contradictingRelations: number;
}

export interface ResearchMetric {
  id: string;
  name: string;
  value: number;
  unit: "ratio" | "count";
  description: string;
}

function clamp01(n: number): number {
  if (Number.isNaN(n) || !Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

export function computeResearchMetrics(counts: ResearchMetricCounts): ResearchMetric[] {
  const evidenceDensity =
    counts.totalSourceCount > 0 ? counts.evidenceCount / counts.totalSourceCount : 0;
  const citationCoverage =
    counts.totalSourceCount > 0 ? counts.citedSourceCount / counts.totalSourceCount : 0;
  const hypothesisConfidence =
    counts.hypothesisCount > 0
      ? counts.highConfidenceHypothesisCount / counts.hypothesisCount
      : 0;
  const researchCompleteness =
    counts.requiredCategoryCount > 0
      ? counts.coveredCategoryCount / counts.requiredCategoryCount
      : 0;
  const sourceDiversity =
    counts.totalSourceKinds > 0 ? counts.uniqueSourceKinds / counts.totalSourceKinds : 0;
  const relationTotal = counts.supportingRelations + counts.contradictingRelations;
  const evidenceConflicts =
    relationTotal > 0 ? counts.contradictingRelations / relationTotal : 0;

  return [
    {
      id: "evidence_density",
      name: "Evidence density",
      value: clamp01(evidenceDensity),
      unit: "ratio",
      description: "Ratio of evidence items to total sources.",
    },
    {
      id: "citation_coverage",
      name: "Citation coverage",
      value: clamp01(citationCoverage),
      unit: "ratio",
      description: "Share of sources with resolved citations.",
    },
    {
      id: "hypothesis_confidence",
      name: "Hypothesis confidence",
      value: clamp01(hypothesisConfidence),
      unit: "ratio",
      description: "Share of hypotheses rated high confidence.",
    },
    {
      id: "research_completeness",
      name: "Research completeness",
      value: clamp01(researchCompleteness),
      unit: "ratio",
      description: "Coverage of required evidence categories.",
    },
    {
      id: "source_diversity",
      name: "Source diversity",
      value: clamp01(sourceDiversity),
      unit: "ratio",
      description: "Variety of source kinds represented.",
    },
    {
      id: "evidence_conflicts",
      name: "Evidence conflicts",
      value: clamp01(evidenceConflicts),
      unit: "ratio",
      description: "Share of substantive relations that contradict.",
    },
  ];
}
