import type { FindingDraft, RecommendationDraft } from "./types.js";

/**
 * Deterministic recommendations from findings. No LLM.
 */
export function buildRecommendations(findings: FindingDraft[]): RecommendationDraft[] {
  const recs: RecommendationDraft[] = [];

  const insufficient = findings.filter((f) => f.confidence === "insufficient_evidence");
  if (insufficient.length) {
    recs.push({
      title: "Collect missing evidence before concluding",
      body: "Multiple questions lack supporting evidence. Prioritize vault documents, staffing/budget records, and decision memos that address the open questions.",
      priority: "high",
      reason: "Findings marked insufficient evidence",
      findingIndexes: findings
        .map((f, i) => (f.confidence === "insufficient_evidence" ? i : -1))
        .filter((i) => i >= 0),
      evidence: insufficient.flatMap((f) => f.evidence).slice(0, 10),
      expectedImpact: "Enables citation-backed conclusions and reduces unsupported claims.",
      confidence: "medium",
    });
  }

  const conflicts = findings.filter((f) => /conflict/i.test(f.title));
  if (conflicts.length) {
    recs.push({
      title: "Resolve or document open conflicts",
      body: "Preserve both sides of conflicting evidence. Assign a reviewer to adjudicate with primary sources; do not overwrite earlier facts.",
      priority: "high",
      reason: "Conflict findings present",
      findingIndexes: findings.map((f, i) => (/conflict/i.test(f.title) ? i : -1)).filter((i) => i >= 0),
      evidence: conflicts.flatMap((f) => f.evidence).slice(0, 10),
      expectedImpact: "Prevents silent resolution and improves auditability.",
      confidence: "medium",
    });
  }

  const supported = findings.filter(
    (f) => f.confidence === "high" || f.confidence === "medium",
  );
  if (supported.length) {
    recs.push({
      title: "Publish supported findings with citations",
      body: "Promote medium/high confidence findings into the formal report appendix with their citation IDs unchanged.",
      priority: "medium",
      reason: "Supported findings available",
      findingIndexes: findings
        .map((f, i) => (f.confidence === "high" || f.confidence === "medium" ? i : -1))
        .filter((i) => i >= 0),
      evidence: supported.flatMap((f) => f.citations).slice(0, 20),
      expectedImpact: "Delivers a traceable investigation product for stakeholders.",
      confidence: "medium",
    });
  }

  if (recs.length === 0) {
    recs.push({
      title: "Re-scope the investigation",
      body: "Current materials do not yet support actionable recommendations. Narrow the question set or expand evidence collection.",
      priority: "medium",
      reason: "No actionable finding cluster",
      findingIndexes: [],
      evidence: [],
      expectedImpact: "Focuses effort where evidence can be obtained.",
      confidence: "low",
    });
  }

  return recs;
}
