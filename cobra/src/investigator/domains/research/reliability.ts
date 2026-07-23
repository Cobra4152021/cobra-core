/** Source reliability engine (KC-009) — heuristic scoring only. */

import type { ResearchEvidenceCategoryId } from "./taxonomy.js";

export type ReliabilityDimension = "authority" | "bias" | "recency" | "reproducibility" | "confidence";
export type ReliabilityLevel = "low" | "medium" | "high" | "insufficient";

export const RELIABILITY_DISCLAIMER =
  "Reliability scores are heuristic indicators only. Human review and source verification required.";

export type SourceKind = ResearchEvidenceCategoryId;

export interface SourceReliabilityInput {
  kind: SourceKind;
  year?: number | null;
  peerReviewed?: boolean;
  currentYear?: number;
}

export interface SourceReliabilityScore {
  kind: SourceKind;
  dimensions: Record<ReliabilityDimension, ReliabilityLevel>;
  overall: ReliabilityLevel;
  disclaimer: string;
}

const BASE_SCORES: Record<
  SourceKind,
  Record<ReliabilityDimension, ReliabilityLevel>
> = {
  peer_reviewed_paper: {
    authority: "high",
    bias: "medium",
    recency: "medium",
    reproducibility: "high",
    confidence: "high",
  },
  government_report: {
    authority: "high",
    bias: "medium",
    recency: "medium",
    reproducibility: "medium",
    confidence: "high",
  },
  primary_source: {
    authority: "high",
    bias: "low",
    recency: "medium",
    reproducibility: "medium",
    confidence: "high",
  },
  secondary_source: {
    authority: "medium",
    bias: "medium",
    recency: "medium",
    reproducibility: "low",
    confidence: "medium",
  },
  expert_testimony: {
    authority: "medium",
    bias: "medium",
    recency: "medium",
    reproducibility: "insufficient",
    confidence: "medium",
  },
  field_observation: {
    authority: "medium",
    bias: "medium",
    recency: "high",
    reproducibility: "low",
    confidence: "medium",
  },
  anonymous_source: {
    authority: "low",
    bias: "high",
    recency: "medium",
    reproducibility: "insufficient",
    confidence: "low",
  },
  internet_article: {
    authority: "low",
    bias: "medium",
    recency: "medium",
    reproducibility: "low",
    confidence: "low",
  },
  book: {
    authority: "medium",
    bias: "medium",
    recency: "low",
    reproducibility: "medium",
    confidence: "medium",
  },
  newspaper: {
    authority: "medium",
    bias: "medium",
    recency: "high",
    reproducibility: "low",
    confidence: "medium",
  },
  audio: {
    authority: "medium",
    bias: "medium",
    recency: "high",
    reproducibility: "medium",
    confidence: "medium",
  },
  geographic: {
    authority: "medium",
    bias: "low",
    recency: "high",
    reproducibility: "high",
    confidence: "medium",
  },
  environmental: {
    authority: "medium",
    bias: "low",
    recency: "high",
    reproducibility: "high",
    confidence: "medium",
  },
  other: {
    authority: "insufficient",
    bias: "insufficient",
    recency: "insufficient",
    reproducibility: "insufficient",
    confidence: "insufficient",
  },
};

function levelRank(level: ReliabilityLevel): number {
  switch (level) {
    case "high":
      return 3;
    case "medium":
      return 2;
    case "low":
      return 1;
    default:
      return 0;
  }
}

function rankToLevel(rank: number): ReliabilityLevel {
  if (rank >= 3) return "high";
  if (rank >= 2) return "medium";
  if (rank >= 1) return "low";
  return "insufficient";
}

function adjustRecency(
  recency: ReliabilityLevel,
  year: number | null | undefined,
  currentYear: number,
  kind: SourceKind,
): ReliabilityLevel {
  if (!year || recency === "insufficient") return recency;
  if (kind === "anonymous_source" || kind === "internet_article") return recency;
  const age = currentYear - year;
  if (age <= 2) return rankToLevel(Math.min(3, levelRank(recency) + 1));
  if (age >= 15) return rankToLevel(Math.max(0, levelRank(recency) - 1));
  return recency;
}

function adjustPeerReview(
  dimensions: Record<ReliabilityDimension, ReliabilityLevel>,
  peerReviewed: boolean | undefined,
): Record<ReliabilityDimension, ReliabilityLevel> {
  if (!peerReviewed) return dimensions;
  return {
    ...dimensions,
    authority: rankToLevel(Math.min(3, levelRank(dimensions.authority) + 1)),
    reproducibility: rankToLevel(Math.min(3, levelRank(dimensions.reproducibility) + 1)),
    confidence: rankToLevel(Math.min(3, levelRank(dimensions.confidence) + 1)),
  };
}

function computeOverall(dimensions: Record<ReliabilityDimension, ReliabilityLevel>): ReliabilityLevel {
  const ranks = Object.values(dimensions).map(levelRank);
  const avg = ranks.reduce((a, b) => a + b, 0) / ranks.length;
  if (avg >= 2.5) return "high";
  if (avg >= 1.5) return "medium";
  if (avg >= 0.5) return "low";
  return "insufficient";
}

/** Deterministic heuristic assessment from source kind and optional metadata. */
export function assessSourceReliability(input: SourceReliabilityInput): SourceReliabilityScore {
  const base = BASE_SCORES[input.kind] ?? BASE_SCORES.other;
  const currentYear = input.currentYear ?? new Date().getFullYear();
  let dimensions = { ...base };
  dimensions.recency = adjustRecency(dimensions.recency, input.year ?? null, currentYear, input.kind);
  dimensions = adjustPeerReview(dimensions, input.peerReviewed);

  return {
    kind: input.kind,
    dimensions,
    overall: computeOverall(dimensions),
    disclaimer: RELIABILITY_DISCLAIMER,
  };
}

export const SourceReliabilityEngine = {
  assessSourceReliability,
  RELIABILITY_DISCLAIMER,
} as const;
