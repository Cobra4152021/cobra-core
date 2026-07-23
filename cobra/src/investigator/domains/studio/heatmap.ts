/** Studio heatmap transforms (KC-007). */

export type StudioHeatmapCategory =
  | "overtime"
  | "staffing"
  | "budget_variance"
  | "grievances"
  | "policy"
  | "missing_evidence"
  | "timeline_density";

export interface StudioHeatmapCellInput {
  row: string;
  column: string;
  value: number | null | undefined;
  label?: string;
}

export interface StudioHeatmapCell {
  row: string;
  column: string;
  value: number;
  intensity: number;
  category: StudioHeatmapCategory;
  label: string;
}

export interface StudioHeatmap {
  category: StudioHeatmapCategory;
  cells: StudioHeatmapCell[];
  maxValue: number;
}

function clampIntensity(value: number, max: number): number {
  if (max <= 0 || !Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value / max));
}

export function buildHeatmapCells(
  category: StudioHeatmapCategory,
  inputs: StudioHeatmapCellInput[],
): StudioHeatmap {
  const valid = inputs.filter((c) => c.value != null && Number.isFinite(c.value));
  const maxValue = valid.length ? Math.max(...valid.map((c) => c.value as number)) : 0;

  const cells: StudioHeatmapCell[] = valid.map((c) => {
    const value = c.value as number;
    return {
      row: c.row,
      column: c.column,
      value,
      intensity: clampIntensity(value, maxValue),
      category,
      label: c.label ?? `${c.row} / ${c.column}`,
    };
  });

  return { category, cells, maxValue };
}
