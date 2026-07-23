/** Investigation comparison transforms (KC-007). */

export interface InvestigationComparisonItem {
  id: string;
  label: string;
}

export interface InvestigationComparisonSnapshot {
  id: string;
  title: string;
  findings: InvestigationComparisonItem[];
  evidence: InvestigationComparisonItem[];
  metrics: InvestigationComparisonItem[];
  recommendations: InvestigationComparisonItem[];
  confidence: number | null;
  missingEvidence: InvestigationComparisonItem[];
}

export interface InvestigationComparisonHighlight {
  field:
    | "findings"
    | "evidence"
    | "metrics"
    | "recommendations"
    | "confidence"
    | "missingEvidence";
  onlyInA: InvestigationComparisonItem[];
  onlyInB: InvestigationComparisonItem[];
  shared: InvestigationComparisonItem[];
}

export interface InvestigationComparisonResult {
  a: InvestigationComparisonSnapshot;
  b: InvestigationComparisonSnapshot;
  highlights: InvestigationComparisonHighlight[];
  confidenceDelta: number | null;
  disclaimer: string;
}

function byId(items: InvestigationComparisonItem[]): Map<string, InvestigationComparisonItem> {
  return new Map(items.map((i) => [i.id, i]));
}

function compareItems(
  field: InvestigationComparisonHighlight["field"],
  aItems: InvestigationComparisonItem[],
  bItems: InvestigationComparisonItem[],
): InvestigationComparisonHighlight {
  const mapA = byId(aItems);
  const mapB = byId(bItems);
  const onlyInA: InvestigationComparisonItem[] = [];
  const onlyInB: InvestigationComparisonItem[] = [];
  const shared: InvestigationComparisonItem[] = [];

  for (const item of aItems) {
    if (mapB.has(item.id)) shared.push(item);
    else onlyInA.push(item);
  }
  for (const item of bItems) {
    if (!mapA.has(item.id)) onlyInB.push(item);
  }

  return { field, onlyInA, onlyInB, shared };
}

export function compareInvestigations(
  a: InvestigationComparisonSnapshot,
  b: InvestigationComparisonSnapshot,
): InvestigationComparisonResult {
  const highlights: InvestigationComparisonHighlight[] = [
    compareItems("findings", a.findings, b.findings),
    compareItems("evidence", a.evidence, b.evidence),
    compareItems("metrics", a.metrics, b.metrics),
    compareItems("recommendations", a.recommendations, b.recommendations),
    compareItems("missingEvidence", a.missingEvidence, b.missingEvidence),
  ];

  const confidenceDelta =
    a.confidence != null && b.confidence != null
      ? Math.round((b.confidence - a.confidence) * 10000) / 10000
      : null;

  highlights.push({
    field: "confidence",
    onlyInA: [],
    onlyInB: [],
    shared: [],
  });

  return {
    a,
    b,
    highlights,
    confidenceDelta,
    disclaimer:
      "Side-by-side comparison for review only. Not a merged finding, legal conclusion, or audit opinion.",
  };
}
