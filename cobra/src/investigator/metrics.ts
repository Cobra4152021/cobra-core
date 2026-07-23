/**
 * Investigation metrics (KC-004B).
 */

import type { EvidenceQualitySummary } from "./evidenceQuality.js";
import type { HypothesisDraft } from "./hypotheses.js";
import type { ConfidenceBundle } from "./confidence.js";
import type { ConflictItem } from "./findings.js";
import type { FindingDraft } from "./types.js";

export interface InvestigationMetrics {
  durationMs: number;
  documentsReviewed: number;
  evidenceQualityMean: number;
  citationCoverage: number;
  hypothesesGenerated: number;
  conflictsDetected: number;
  findingsCount: number;
  confidenceTrend: {
    evidence: string;
    findings: string;
    investigation: string;
    readiness: string;
  };
  startedAt: number;
  completedAt: number;
}

export function buildInvestigationMetrics(input: {
  startedAt: number;
  completedAt: number;
  documentsReviewed: number;
  evidenceQuality: EvidenceQualitySummary;
  citationCoverage: number;
  hypotheses: HypothesisDraft[];
  conflicts: ConflictItem[];
  findings: FindingDraft[];
  confidence: ConfidenceBundle;
}): InvestigationMetrics {
  return {
    durationMs: Math.max(0, input.completedAt - input.startedAt),
    documentsReviewed: input.documentsReviewed,
    evidenceQualityMean: input.evidenceQuality.meanOverall,
    citationCoverage: input.citationCoverage,
    hypothesesGenerated: input.hypotheses.length,
    conflictsDetected: input.conflicts.length,
    findingsCount: input.findings.length,
    confidenceTrend: {
      evidence: input.confidence.evidenceConfidence,
      findings: input.confidence.findingConfidence,
      investigation: input.confidence.investigationConfidence,
      readiness: input.confidence.overallReadiness,
    },
    startedAt: input.startedAt,
    completedAt: input.completedAt,
  };
}
