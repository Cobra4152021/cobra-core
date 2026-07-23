/** Labor pilot scorecard (KC-006). */

export interface LaborPilotScorecard {
  planRelevance: number;
  evidenceCompleteness: number;
  citationAccuracy: number;
  hypothesisQuality: number;
  findingUsefulness: number;
  reportClarity: number;
  neutrality: number;
  easeOfUse: number;
  timeSaved: number;
  wouldUseAgain: boolean;
  wouldRecommend: boolean;
  blockingDefect: boolean;
  average: number;
}

function clamp(n: number): number {
  if (!Number.isFinite(n)) return 1;
  return Math.min(5, Math.max(1, Math.round(n)));
}

export function scoreLaborPilot(input: Partial<LaborPilotScorecard>): LaborPilotScorecard {
  const dims = {
    planRelevance: clamp(input.planRelevance ?? 3),
    evidenceCompleteness: clamp(input.evidenceCompleteness ?? 3),
    citationAccuracy: clamp(input.citationAccuracy ?? 3),
    hypothesisQuality: clamp(input.hypothesisQuality ?? 3),
    findingUsefulness: clamp(input.findingUsefulness ?? 3),
    reportClarity: clamp(input.reportClarity ?? 3),
    neutrality: clamp(input.neutrality ?? 3),
    easeOfUse: clamp(input.easeOfUse ?? 3),
    timeSaved: clamp(input.timeSaved ?? 3),
  };
  const values = Object.values(dims);
  const average = values.reduce((a, b) => a + b, 0) / values.length;
  return {
    ...dims,
    wouldUseAgain: Boolean(input.wouldUseAgain),
    wouldRecommend: Boolean(input.wouldRecommend),
    blockingDefect: Boolean(input.blockingDefect),
    average,
  };
}
