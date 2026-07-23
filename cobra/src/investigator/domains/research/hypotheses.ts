/** Competing hypotheses workspace (KC-009). */

export type HypothesisConfidence = "low" | "medium" | "high" | "insufficient";

export interface HypothesisEntry {
  id: string;
  statement: string;
  support: string[];
  contradictions: string[];
  unknowns: string[];
  missing: string[];
  confidence: HypothesisConfidence;
}

export interface HypothesisWorkspace {
  issue: string;
  hypotheses: HypothesisEntry[];
  reviewRequired: boolean;
}

function defaultHypothesesForIssue(issue: string): HypothesisEntry[] {
  return [
    {
      id: "hyp_primary",
      statement: `Primary explanation accounts for available evidence regarding: ${issue}`,
      support: [],
      contradictions: [],
      unknowns: ["Corroboration across independent sources pending"],
      missing: [],
      confidence: "insufficient",
    },
    {
      id: "hyp_alternate",
      statement: `Alternate explanation remains plausible for: ${issue}`,
      support: [],
      contradictions: [],
      unknowns: ["Competing mechanism not fully tested"],
      missing: [],
      confidence: "insufficient",
    },
    {
      id: "hyp_insufficient",
      statement: `Evidence is insufficient to prefer any single explanation for: ${issue}`,
      support: [],
      contradictions: [],
      unknowns: ["Key sources not yet evaluated"],
      missing: ["Additional primary sources recommended"],
      confidence: "high",
    },
  ];
}

export function buildHypothesisWorkspace(input: {
  issue: string;
  hypotheses?: Array<Partial<HypothesisEntry> & Pick<HypothesisEntry, "id" | "statement">>;
}): HypothesisWorkspace {
  const issue = input.issue.trim() || "Unspecified issue";
  const source = input.hypotheses?.length ? input.hypotheses : defaultHypothesesForIssue(issue);

  const hypotheses: HypothesisEntry[] = source.map((h) => ({
    id: h.id,
    statement: h.statement,
    support: [...(h.support ?? [])],
    contradictions: [...(h.contradictions ?? [])],
    unknowns: [...(h.unknowns ?? [])],
    missing: [...(h.missing ?? [])],
    confidence: h.confidence ?? "insufficient",
  }));

  return {
    issue,
    hypotheses,
    reviewRequired: true,
  };
}
