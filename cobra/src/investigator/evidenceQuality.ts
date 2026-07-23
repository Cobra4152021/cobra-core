/**
 * Evidence Quality Score (KC-004B).
 * Scores authority, reliability, freshness, completeness, corroboration, relevance, version confidence.
 */

import type { EvidenceItem } from "./findings.js";

export type EvidenceDimension =
  | "authority"
  | "reliability"
  | "freshness"
  | "completeness"
  | "corroboration"
  | "relevance"
  | "versionConfidence";

export interface EvidenceQualityScore {
  evidenceId: string;
  kind: string;
  label: string;
  dimensions: Record<EvidenceDimension, number>;
  overall: number;
  notes: string[];
}

export interface EvidenceQualitySummary {
  scores: EvidenceQualityScore[];
  meanOverall: number;
  medianOverall: number;
  highQualityCount: number;
  lowQualityCount: number;
}

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

function kindAuthority(kind: string): number {
  const k = kind.toLowerCase();
  if (/(policy|statute|contract|agreement|decision|approval)/.test(k)) return 0.9;
  if (/(budget|payroll|official|vault|document)/.test(k)) return 0.8;
  if (/(memory|fact|timeline)/.test(k)) return 0.65;
  if (/(search|snippet|web)/.test(k)) return 0.45;
  return 0.55;
}

function scoreOne(
  item: EvidenceItem,
  all: EvidenceItem[],
  queryTokens: string[],
): EvidenceQualityScore {
  const text = `${item.label} ${item.excerpt ?? ""}`.toLowerCase();
  const notes: string[] = [];

  const authority = kindAuthority(item.kind);
  const reliability = item.citationId ? 0.85 : text.length > 40 ? 0.55 : 0.35;
  if (!item.citationId) notes.push("No validated citation attached");

  const completeness = clamp01((item.excerpt?.length ?? item.label.length) / 180);
  if (completeness < 0.35) notes.push("Thin excerpt");

  // Freshness: heuristic — prefer items mentioning recent years; else neutral
  const yearMatch = text.match(/20(1[5-9]|2[0-9])/);
  const freshness = yearMatch ? 0.75 : 0.5;

  const tokenHits = queryTokens.filter((t) => t.length > 3 && text.includes(t)).length;
  const relevance = queryTokens.length
    ? clamp01(tokenHits / Math.min(6, queryTokens.length))
    : 0.5;

  const corroborating = all.filter(
    (o) =>
      o !== item &&
      o.kind === item.kind &&
      (o.label.slice(0, 24).toLowerCase() === item.label.slice(0, 24).toLowerCase() ||
        (item.excerpt && o.excerpt && o.excerpt.slice(0, 40) === item.excerpt.slice(0, 40))),
  ).length;
  const corroboration = clamp01(0.4 + corroborating * 0.2);

  const versionConfidence = /draft|unofficial|estimated|approx/i.test(text)
    ? 0.35
    : /final|approved|signed|official/i.test(text)
      ? 0.9
      : 0.6;

  const dimensions: Record<EvidenceDimension, number> = {
    authority,
    reliability,
    freshness,
    completeness,
    corroboration,
    relevance,
    versionConfidence,
  };

  const weights: Record<EvidenceDimension, number> = {
    authority: 0.18,
    reliability: 0.18,
    freshness: 0.1,
    completeness: 0.12,
    corroboration: 0.14,
    relevance: 0.18,
    versionConfidence: 0.1,
  };

  let overall = 0;
  for (const d of Object.keys(dimensions) as EvidenceDimension[]) {
    overall += dimensions[d] * weights[d];
  }
  overall = Math.round(overall * 1000) / 1000;

  return {
    evidenceId: item.id || item.label,
    kind: item.kind,
    label: item.label,
    dimensions,
    overall,
    notes,
  };
}

export function scoreEvidenceQuality(input: {
  evidence: EvidenceItem[];
  queryText?: string;
}): EvidenceQualitySummary {
  const queryTokens = (input.queryText ?? "")
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
  const scores = input.evidence.map((e) => scoreOne(e, input.evidence, queryTokens));
  const overalls = scores.map((s) => s.overall).sort((a, b) => a - b);
  const meanOverall = overalls.length
    ? Math.round((overalls.reduce((a, b) => a + b, 0) / overalls.length) * 1000) / 1000
    : 0;
  const mid = Math.floor(overalls.length / 2);
  const medianOverall = overalls.length
    ? overalls.length % 2
      ? overalls[mid]
      : Math.round(((overalls[mid - 1] + overalls[mid]) / 2) * 1000) / 1000
    : 0;

  return {
    scores,
    meanOverall,
    medianOverall,
    highQualityCount: scores.filter((s) => s.overall >= 0.7).length,
    lowQualityCount: scores.filter((s) => s.overall < 0.45).length,
  };
}
