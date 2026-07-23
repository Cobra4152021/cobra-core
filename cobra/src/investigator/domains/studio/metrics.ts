/** Studio chart metric normalization (KC-007). */

export type StudioMetricDomain = "government" | "labor" | "shared";

export type StudioMetricSeriesId =
  | "budget_trends"
  | "overtime"
  | "vacancies"
  | "staffing"
  | "pilot_success"
  | "investigation_duration"
  | "evidence_quality"
  | "missing_evidence"
  | "confidence";

export interface StudioMetricPoint {
  x: string;
  y: number;
}

export interface StudioMetricSeries {
  id: StudioMetricSeriesId;
  label: string;
  points: StudioMetricPoint[];
  domain: StudioMetricDomain;
}

export interface RawMetricInput {
  id: StudioMetricSeriesId;
  label?: string;
  domain?: StudioMetricDomain;
  points: Array<{ x: string; y: number | null | undefined }>;
}

const SERIES_LABELS: Record<StudioMetricSeriesId, string> = {
  budget_trends: "Budget trends",
  overtime: "Overtime",
  vacancies: "Vacancies",
  staffing: "Staffing",
  pilot_success: "Pilot success",
  investigation_duration: "Investigation duration",
  evidence_quality: "Evidence quality",
  missing_evidence: "Missing evidence",
  confidence: "Confidence",
};

const SERIES_DOMAINS: Record<StudioMetricSeriesId, StudioMetricDomain> = {
  budget_trends: "government",
  overtime: "shared",
  vacancies: "government",
  staffing: "shared",
  pilot_success: "shared",
  investigation_duration: "shared",
  evidence_quality: "shared",
  missing_evidence: "shared",
  confidence: "shared",
};

export function normalizeMetricSeries(input: RawMetricInput): StudioMetricSeries {
  const points = input.points
    .filter((p) => p.y != null && Number.isFinite(p.y))
    .map((p) => ({ x: String(p.x), y: p.y as number }))
    .sort((a, b) => a.x.localeCompare(b.x));

  return {
    id: input.id,
    label: input.label ?? SERIES_LABELS[input.id],
    points,
    domain: input.domain ?? SERIES_DOMAINS[input.id],
  };
}

export function normalizeMetricSeriesBatch(inputs: RawMetricInput[]): StudioMetricSeries[] {
  return inputs.map(normalizeMetricSeries);
}
