/** Studio observability chart transforms (KC-007). */

import {
  normalizeMetricSeries,
  type RawMetricInput,
  type StudioMetricSeries,
} from "./metrics.js";

export interface ObservabilityDenialEvent {
  at: string;
  kind: "error" | "rbac" | "csrf" | "idor";
  count: number;
}

export interface ObservabilityUsageEvent {
  at: string;
  pilotId?: string;
  templateId?: string;
  durationMs: number;
}

export interface ObservabilityAggregateInput {
  denials?: ObservabilityDenialEvent[];
  pilotUsage?: ObservabilityUsageEvent[];
  templateUsage?: ObservabilityUsageEvent[];
}

export interface ObservabilityChartBundle {
  denialSeries: StudioMetricSeries[];
  pilotUsageSeries: StudioMetricSeries[];
  templateUsageSeries: StudioMetricSeries[];
  durationSeries: StudioMetricSeries[];
}

function sumByKey<T extends { at: string }>(
  events: T[],
  keyFn: (e: T) => string,
  valueFn: (e: T) => number,
): RawMetricInput["points"] {
  const totals = new Map<string, number>();
  for (const event of events) {
    const key = keyFn(event);
    totals.set(key, (totals.get(key) ?? 0) + valueFn(event));
  }
  return [...totals.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([x, y]) => ({ x, y }));
}

export function aggregateObservabilityCharts(
  input: ObservabilityAggregateInput,
): ObservabilityChartBundle {
  const denials = input.denials ?? [];
  const pilotUsage = input.pilotUsage ?? [];
  const templateUsage = input.templateUsage ?? [];

  const denialSeries: StudioMetricSeries[] = (["error", "rbac", "csrf", "idor"] as const).map(
    (kind) =>
      normalizeMetricSeries({
        id: "confidence",
        label: `${kind.toUpperCase()} denials`,
        domain: "shared",
        points: sumByKey(
          denials.filter((d) => d.kind === kind),
          (d) => d.at,
          (d) => d.count,
        ),
      }),
  );

  const pilotUsageSeries = [
    normalizeMetricSeries({
      id: "pilot_success",
      label: "Pilot usage events",
      domain: "shared",
      points: sumByKey(pilotUsage, (e) => e.at, () => 1),
    }),
  ];

  const templateUsageSeries = [
    normalizeMetricSeries({
      id: "evidence_quality",
      label: "Template usage events",
      domain: "shared",
      points: sumByKey(templateUsage, (e) => e.at, () => 1),
    }),
  ];

  const durationEvents = [...pilotUsage, ...templateUsage];
  const durationSeries = [
    normalizeMetricSeries({
      id: "investigation_duration",
      label: "Average duration (ms)",
      domain: "shared",
      points: aggregateAverageDuration(durationEvents),
    }),
  ];

  return {
    denialSeries,
    pilotUsageSeries,
    templateUsageSeries,
    durationSeries,
  };
}

function aggregateAverageDuration(events: ObservabilityUsageEvent[]): RawMetricInput["points"] {
  const buckets = new Map<string, { total: number; count: number }>();
  for (const event of events) {
    const bucket = buckets.get(event.at) ?? { total: 0, count: 0 };
    bucket.total += event.durationMs;
    bucket.count += 1;
    buckets.set(event.at, bucket);
  }
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([x, { total, count }]) => ({ x, y: count > 0 ? total / count : 0 }));
}
