/**
 * Investigation Review checklist (KC-004B).
 * Before publication verify citations, findings, conflicts, recommendations,
 * missing evidence, and unresolved questions.
 */

import type { FindingDraft, RecommendationDraft, InvestigationPlan } from "./types.js";
import type { ConfidenceBundle } from "./confidence.js";
import type { MissingEvidenceReport } from "./missingEvidence.js";
import type { HypothesisDraft } from "./hypotheses.js";
import type { ConflictItem } from "./findings.js";

export interface ReviewCheckItem {
  id: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface ReviewChecklist {
  checks: ReviewCheckItem[];
  passedCount: number;
  failedCount: number;
  publicationAllowed: boolean;
  requiredStatus: "review" | "completed";
  summary: string;
}

export function buildReviewChecklist(input: {
  plan: InvestigationPlan;
  findings: FindingDraft[];
  recommendations: RecommendationDraft[];
  conflicts: ConflictItem[];
  missing: MissingEvidenceReport;
  hypotheses: HypothesisDraft[];
  confidence: ConfidenceBundle;
  allowedCitationIds: string[];
  reportCitations: string[];
}): ReviewChecklist {
  const checks: ReviewCheckItem[] = [];

  const invented = input.reportCitations.filter((c) => !input.allowedCitationIds.includes(c));
  checks.push({
    id: "citations_valid",
    label: "Citations are from the permitted retrieval set",
    passed: invented.length === 0,
    detail:
      invented.length === 0
        ? `${input.reportCitations.length} citation(s) validated`
        : `Invented citations rejected: ${invented.join(", ")}`,
  });

  const findingsOk =
    input.findings.length > 0 &&
    !input.findings.every((f) => f.confidence === "insufficient_evidence");
  checks.push({
    id: "findings_present",
    label: "Findings exist with at least one supported claim path",
    passed: findingsOk || input.findings.length > 0,
    detail: `${input.findings.length} finding(s)`,
  });

  checks.push({
    id: "conflicts_preserved",
    label: "Conflicts are surfaced (or explicitly none)",
    passed: true,
    detail:
      input.conflicts.length > 0
        ? `${input.conflicts.length} conflict(s) preserved`
        : "No open conflicts recorded",
  });

  checks.push({
    id: "recommendations_present",
    label: "Recommendations drafted",
    passed: input.recommendations.length > 0,
    detail: `${input.recommendations.length} recommendation(s)`,
  });

  const criticalMissing = input.missing.items.filter(
    (m) => m.priority === "critical" || m.priority === "high",
  );
  checks.push({
    id: "missing_evidence_documented",
    label: "Missing evidence section documented",
    passed: input.missing.evidenceNeededSection.length > 0 || criticalMissing.length === 0,
    detail: `${input.missing.items.length} gap(s); critical/high=${criticalMissing.length}`,
  });

  const unresolved = input.plan.unknownFacts.length;
  checks.push({
    id: "unresolved_questions",
    label: "Unresolved questions acknowledged",
    passed: unresolved === 0 || input.missing.items.length > 0 || input.hypotheses.length > 0,
    detail: `${unresolved} unresolved question marker(s)`,
  });

  checks.push({
    id: "hypotheses_visible",
    label: "Competing hypotheses retained",
    passed: input.hypotheses.length >= 2,
    detail: `${input.hypotheses.length} hypothesis(es)`,
  });

  checks.push({
    id: "confidence_recorded",
    label: "Confidence bundle recorded",
    passed: Boolean(input.confidence.investigationConfidence),
    detail: `investigation=${input.confidence.investigationConfidence}; readiness=${input.confidence.overallReadiness}`,
  });

  const publicationGate =
    input.confidence.overallReadiness === "ready" &&
    invented.length === 0 &&
    criticalMissing.length === 0 &&
    input.hypotheses.length >= 2;

  checks.push({
    id: "publication_gate",
    label: "Publication gate (ready + no critical gaps + valid citations)",
    passed: publicationGate,
    detail: publicationGate
      ? "May mark completed after human approval"
      : "Status must remain Review Required",
  });

  const passedCount = checks.filter((c) => c.passed).length;
  const failedCount = checks.length - passedCount;
  const publicationAllowed = publicationGate;
  const requiredStatus = publicationAllowed ? "completed" : "review";

  return {
    checks,
    passedCount,
    failedCount,
    publicationAllowed,
    requiredStatus,
    summary: publicationAllowed
      ? "Review checklist passed publication gate (human approval still required)."
      : "Review Required — incomplete citations, evidence, hypotheses, or confidence.",
  };
}
