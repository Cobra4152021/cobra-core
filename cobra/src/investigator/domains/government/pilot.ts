/** Pilot metadata and scorecard (KC-005) — does not alter findings. */

export interface GovernmentPilotMeta {
  pilotCase: boolean;
  pilotOwner: string | null;
  pilotStartedAt: string | null;
  pilotCompletedAt: string | null;
  baselineManualHours: number | null;
  cobraHours: number | null;
  estimatedTimeSaved: number | null;
  reviewerRating: number | null;
  citationAccuracyRating: number | null;
  findingQualityRating: number | null;
  reportQualityRating: number | null;
  falsePositiveCount: number | null;
  falseNegativeCount: number | null;
  bugsFound: string[];
  featureRequests: string[];
  pilotNotes: string | null;
}

export interface GovernmentPilotScorecard {
  planRelevance: number;
  evidenceCompleteness: number;
  citationAccuracy: number;
  hypothesisQuality: number;
  findingUsefulness: number;
  recommendationUsefulness: number;
  reportClarity: number;
  neutrality: number;
  easeOfUse: number;
  timeSaved: number;
  reviewerConfidence: number;
  wouldUseAgain: boolean;
  wouldRecommend: boolean;
  requiresMajorRevision: boolean;
  blockingDefect: boolean;
}

export function emptyPilotMeta(owner?: string | null): GovernmentPilotMeta {
  return {
    pilotCase: true,
    pilotOwner: owner ?? null,
    pilotStartedAt: null,
    pilotCompletedAt: null,
    baselineManualHours: null,
    cobraHours: null,
    estimatedTimeSaved: null,
    reviewerRating: null,
    citationAccuracyRating: null,
    findingQualityRating: null,
    reportQualityRating: null,
    falsePositiveCount: null,
    falseNegativeCount: null,
    bugsFound: [],
    featureRequests: [],
    pilotNotes: null,
  };
}

function clampScore(n: number): number {
  if (!Number.isFinite(n)) return 1;
  return Math.min(5, Math.max(1, Math.round(n)));
}

export function scorePilot(input: Partial<GovernmentPilotScorecard>): GovernmentPilotScorecard & {
  average: number;
} {
  const card: GovernmentPilotScorecard = {
    planRelevance: clampScore(input.planRelevance ?? 3),
    evidenceCompleteness: clampScore(input.evidenceCompleteness ?? 3),
    citationAccuracy: clampScore(input.citationAccuracy ?? 3),
    hypothesisQuality: clampScore(input.hypothesisQuality ?? 3),
    findingUsefulness: clampScore(input.findingUsefulness ?? 3),
    recommendationUsefulness: clampScore(input.recommendationUsefulness ?? 3),
    reportClarity: clampScore(input.reportClarity ?? 3),
    neutrality: clampScore(input.neutrality ?? 3),
    easeOfUse: clampScore(input.easeOfUse ?? 3),
    timeSaved: clampScore(input.timeSaved ?? 3),
    reviewerConfidence: clampScore(input.reviewerConfidence ?? 3),
    wouldUseAgain: Boolean(input.wouldUseAgain),
    wouldRecommend: Boolean(input.wouldRecommend),
    requiresMajorRevision: Boolean(input.requiresMajorRevision),
    blockingDefect: Boolean(input.blockingDefect),
  };
  const dims = [
    card.planRelevance,
    card.evidenceCompleteness,
    card.citationAccuracy,
    card.hypothesisQuality,
    card.findingUsefulness,
    card.recommendationUsefulness,
    card.reportClarity,
    card.neutrality,
    card.easeOfUse,
    card.timeSaved,
  ];
  const average = dims.reduce((a, b) => a + b, 0) / dims.length;
  return { ...card, average };
}

/** Documented comparison method for estimated time saved — never invent savings. */
export function estimateTimeSaved(baselineManualHours: number | null, cobraHours: number | null): {
  hours: number | null;
  method: string;
} {
  if (baselineManualHours == null || cobraHours == null) {
    return {
      hours: null,
      method: "Not claimed — baseline_manual_hours and cobra_hours both required.",
    };
  }
  return {
    hours: Math.max(0, baselineManualHours - cobraHours),
    method: "estimated_time_saved = baseline_manual_hours - cobra_hours (reviewer-supplied).",
  };
}
