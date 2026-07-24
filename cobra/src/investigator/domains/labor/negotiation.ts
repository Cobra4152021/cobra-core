/** Negotiation workspace helpers (KC-006). */

export type ProposalSide = "union" | "management" | "joint" | "unknown";
export type ProposalStatus =
  | "current"
  | "union_proposal"
  | "management_proposal"
  | "counter_proposal"
  | "tentative_agreement"
  | "final_agreement";

export interface NegotiationProposal {
  id: string;
  side: ProposalSide;
  status: ProposalStatus;
  articleRefs: string[];
  summary: string;
  openIssues: string[];
}

export interface NegotiationSummary {
  proposals: NegotiationProposal[];
  changeSummary: string[];
  impactSummary: string[];
  articleDifferences: string[];
  openIssues: string[];
  disclaimer: string;
}

export function summarizeNegotiation(proposals: NegotiationProposal[]): NegotiationSummary {
  const openIssues = [...new Set(proposals.flatMap((p) => p.openIssues))];
  const articleDifferences = [
    ...new Set(proposals.flatMap((p) => p.articleRefs.map((a) => `${p.status}: ${a}`))),
  ];
  const changeSummary = proposals.map((p) => `[${p.status}/${p.side}] ${p.summary}`);
  const impactSummary = [
    "Impact assessment requires cost/staffing evidence — not generated without source fields.",
    ...proposals
      .filter((p) => p.status === "tentative_agreement" || p.status === "final_agreement")
      .map((p) => `Documented agreement state: ${p.status} — ${p.summary}`),
  ];

  return {
    proposals,
    changeSummary,
    impactSummary,
    articleDifferences,
    openIssues,
    disclaimer:
      "Negotiation workspace support only. Not a bargaining mandate, cost guarantee, or executed agreement.",
  };
}
