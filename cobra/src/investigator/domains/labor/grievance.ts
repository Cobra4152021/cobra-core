/** Grievance builder (KC-006) — draft only; human review required. */

export interface GrievanceDraft {
  issue: string;
  timeline: string[];
  facts: string[];
  evidenceIds: string[];
  witnesses: string[];
  contractArticles: string[];
  policies: string[];
  pastPracticeClaims: string[];
  missingEvidence: string[];
  competingExplanations: string[];
  draftText: string;
  reviewRequired: true;
  disclaimer: string;
}

export function buildGrievanceDraft(input: {
  issue: string;
  timeline?: string[];
  facts?: string[];
  evidenceIds?: string[];
  witnesses?: string[];
  contractArticles?: string[];
  policies?: string[];
  pastPracticeClaims?: string[];
  missingEvidence?: string[];
  competingExplanations?: string[];
}): GrievanceDraft {
  const issue = input.issue.trim();
  const timeline = input.timeline ?? [];
  const facts = input.facts ?? [];
  const contractArticles = input.contractArticles ?? [];
  const missingEvidence = input.missingEvidence ?? [];
  const competingExplanations = input.competingExplanations ?? [
    "Records support the stated issue for further review.",
    "Alternate operational explanation exists.",
    "Evidence is insufficient for a firm position.",
  ];

  const draftText = [
    "DRAFT GRIEVANCE — HUMAN REVIEW REQUIRED",
    "",
    `Issue: ${issue}`,
    "",
    "Timeline:",
    ...(timeline.length ? timeline.map((t) => `- ${t}`) : ["- (none provided)"]),
    "",
    "Facts (as provided):",
    ...(facts.length ? facts.map((f) => `- ${f}`) : ["- (none provided)"]),
    "",
    "Contract articles cited:",
    ...(contractArticles.length ? contractArticles.map((a) => `- ${a}`) : ["- (none cited)"]),
    "",
    "Competing explanations:",
    ...competingExplanations.map((c) => `- ${c}`),
    "",
    "Missing evidence:",
    ...(missingEvidence.length ? missingEvidence.map((m) => `- ${m}`) : ["- (none listed)"]),
    "",
    "This draft does not determine contract violation, ULP, or liability.",
  ].join("\n");

  return {
    issue,
    timeline,
    facts,
    evidenceIds: input.evidenceIds ?? [],
    witnesses: input.witnesses ?? [],
    contractArticles,
    policies: input.policies ?? [],
    pastPracticeClaims: input.pastPracticeClaims ?? [],
    missingEvidence,
    competingExplanations,
    draftText,
    reviewRequired: true,
    disclaimer:
      "Draft only. Not a filing. Not legal advice. Not a determination of violation or liability.",
  };
}
