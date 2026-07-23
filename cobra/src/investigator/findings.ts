import type { ConfidenceLevel, FindingDraft } from "./types.js";

export type EvidenceItem = {
  id?: string;
  kind: string;
  label: string;
  excerpt?: string;
  citationId?: string | null;
};

export type ConflictItem = {
  summary: string;
  status?: string;
};

/**
 * Build findings from collected evidence + conflicts. No LLM.
 * Every finding carries citation IDs only from the provided allowlist.
 */
export function buildFindings(input: {
  questions: string[];
  evidence: EvidenceItem[];
  conflicts: ConflictItem[];
  allowedCitationIds: string[];
}): FindingDraft[] {
  const allowed = new Set(input.allowedCitationIds);
  const findings: FindingDraft[] = [];

  if (input.evidence.length === 0) {
    findings.push({
      title: "Insufficient evidence collected",
      summary:
        "The investigation did not retrieve accessible evidence for the stated questions. No factual conclusion is warranted.",
      confidence: "insufficient_evidence",
      citations: [],
      evidence: [],
      entityIds: [],
      timelineRefs: [],
    });
    return findings;
  }

  // Group evidence by kind for structured findings
  const byKind = new Map<string, EvidenceItem[]>();
  for (const e of input.evidence) {
    const list = byKind.get(e.kind) ?? [];
    list.push(e);
    byKind.set(e.kind, list);
  }

  for (const [kind, items] of byKind) {
    const cites = items
      .map((i) => i.citationId)
      .filter((c): c is string => Boolean(c && allowed.has(c)));
    const excerpts = items.map((i) => i.excerpt || i.label).slice(0, 8);
    findings.push({
      title: `Evidence cluster: ${kind}`,
      summary: `Collected ${items.length} item(s) of kind "${kind}". Key material: ${excerpts
        .slice(0, 3)
        .join(" | ")}`,
      confidence: confidenceFromSupport(items.length, cites.length, input.conflicts.length),
      citations: cites,
      evidence: items.map((i) => i.id || i.label),
      entityIds: [],
      timelineRefs: items.filter((i) => i.kind === "timeline").map((i) => i.id || i.label),
    });
  }

  for (const q of input.questions.slice(0, 5)) {
    const related = input.evidence.filter((e) =>
      `${e.label} ${e.excerpt ?? ""}`.toLowerCase().includes(tokenFromQuestion(q)),
    );
    const cites = related
      .map((i) => i.citationId)
      .filter((c): c is string => Boolean(c && allowed.has(c)));
    findings.push({
      title: `Question: ${q.slice(0, 120)}`,
      summary:
        related.length > 0
          ? `Partial support from ${related.length} evidence item(s).`
          : "No directly matching evidence was found for this question.",
      confidence:
        related.length === 0
          ? "insufficient_evidence"
          : confidenceFromSupport(related.length, cites.length, 0),
      citations: cites,
      evidence: related.map((i) => i.id || i.label),
      entityIds: [],
      timelineRefs: [],
    });
  }

  if (input.conflicts.length) {
    findings.push({
      title: "Open conflicts preserved",
      summary: input.conflicts
        .slice(0, 5)
        .map((c) => c.summary)
        .join("; "),
      confidence: "low",
      citations: [],
      evidence: input.conflicts.map((c) => c.summary),
      entityIds: [],
      timelineRefs: [],
    });
  }

  return findings;
}

function tokenFromQuestion(q: string): string {
  const words = q
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 4);
  return words[0] ?? q.slice(0, 8).toLowerCase();
}

function confidenceFromSupport(
  evidenceCount: number,
  citationCount: number,
  conflictCount: number,
): ConfidenceLevel {
  if (evidenceCount === 0) return "insufficient_evidence";
  if (conflictCount > 0 && citationCount === 0) return "low";
  if (citationCount >= 2 && evidenceCount >= 3 && conflictCount === 0) return "high";
  if (citationCount >= 1 || evidenceCount >= 2) return "medium";
  return "low";
}
