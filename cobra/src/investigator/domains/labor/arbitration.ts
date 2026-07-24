/** Arbitration preparation packet (KC-006). */

export interface ArbitrationPrep {
  issue: string;
  evidenceIds: string[];
  witnesses: string[];
  timeline: string[];
  exhibits: Array<{ id: string; label: string; citationId: string | null }>;
  questions: string[];
  supportingEvidence: string[];
  contraryEvidence: string[];
  unresolvedQuestions: string[];
  exhibitIndexMarkdown: string;
  disclaimer: string;
}

export function buildArbitrationPrep(input: {
  issue: string;
  evidenceIds?: string[];
  witnesses?: string[];
  timeline?: string[];
  exhibits?: Array<{ id: string; label: string; citationId?: string | null }>;
  questions?: string[];
  supportingEvidence?: string[];
  contraryEvidence?: string[];
  unresolvedQuestions?: string[];
}): ArbitrationPrep {
  const exhibits = (input.exhibits ?? []).map((e, i) => ({
    id: e.id || `ex_${i + 1}`,
    label: e.label,
    citationId: e.citationId ?? null,
  }));
  const exhibitIndexMarkdown = [
    "# Citation-backed Exhibit Index",
    "",
    ...exhibits.map(
      (e, i) =>
        `${i + 1}. ${e.label} (id: ${e.id}${e.citationId ? `; citation: ${e.citationId}` : "; citation: pending"})`,
    ),
    "",
    "_Index is organizational only. Does not predict arbitral outcomes._",
  ].join("\n");

  return {
    issue: input.issue.trim(),
    evidenceIds: input.evidenceIds ?? [],
    witnesses: input.witnesses ?? [],
    timeline: input.timeline ?? [],
    exhibits,
    questions: input.questions ?? [
      "What is the framed issue?",
      "What remedy is sought?",
      "What contrary evidence must be addressed?",
    ],
    supportingEvidence: input.supportingEvidence ?? [],
    contraryEvidence: input.contraryEvidence ?? [],
    unresolvedQuestions: input.unresolvedQuestions ?? [],
    exhibitIndexMarkdown,
    disclaimer:
      "Arbitration preparation support only. Not legal advice. Does not determine liability or predict awards.",
  };
}
