/** Labor staffing compliance — reuses Government staffing/overtime metrics (KC-006). */

import {
  computeStaffingMetrics,
  computeOvertimeMetrics,
  type GovernmentMetric,
} from "../government/metrics.js";

export interface LaborStaffingContext {
  minimumStaffing?: number | null;
  mandatoryOvertimeHours?: number | null;
  reliefFactor?: number | null;
  holdovers?: number | null;
  vacancies?: number | null;
  authorized?: number | null;
  filled?: number | null;
  deployable?: number | null;
  overtimeHours?: number | null;
  overtimeCost?: number | null;
  assignmentLanguage?: string | null;
  shiftBidNotes?: string | null;
  seniorityNotes?: string | null;
  contractStaffingRules?: string[];
  period?: string | null;
  citations?: string[];
}

export interface LaborStaffingAnalysis {
  metrics: GovernmentMetric[];
  laborNotes: string[];
  gaps: string[];
  disclaimer: string;
}

export function analyzeLaborStaffing(ctx: LaborStaffingContext): LaborStaffingAnalysis {
  const citations = ctx.citations ?? [];
  const metrics = [
    ...computeStaffingMetrics({
      authorized: ctx.authorized,
      filled: ctx.filled,
      deployable: ctx.deployable,
      vacant: ctx.vacancies,
      period: ctx.period,
      citations,
    }),
    ...computeOvertimeMetrics({
      overtimeHours: ctx.overtimeHours ?? ctx.mandatoryOvertimeHours,
      overtimeCost: ctx.overtimeCost,
      filledPositions: ctx.filled,
      vacancies: ctx.vacancies,
      period: ctx.period,
      citations,
    }),
  ];

  const laborNotes: string[] = [];
  const gaps: string[] = [];

  if (ctx.minimumStaffing != null && ctx.deployable != null) {
    laborNotes.push(
      `Deployable (${ctx.deployable}) vs cited minimum staffing (${ctx.minimumStaffing}) — comparison only; not a breach finding.`,
    );
  } else if (ctx.minimumStaffing != null) {
    gaps.push("Deployable staffing field missing for minimum staffing comparison.");
  }

  if (ctx.reliefFactor != null) {
    laborNotes.push(`Relief factor supplied: ${ctx.reliefFactor} (assumption labeled as source-provided).`);
  } else {
    gaps.push("Relief factor not supplied.");
  }

  if (ctx.holdovers != null) {
    laborNotes.push(`Holdovers counted: ${ctx.holdovers}.`);
  }
  if (ctx.assignmentLanguage) laborNotes.push(`Assignment language note: ${ctx.assignmentLanguage}`);
  if (ctx.shiftBidNotes) laborNotes.push(`Shift bid notes: ${ctx.shiftBidNotes}`);
  if (ctx.seniorityNotes) laborNotes.push(`Seniority notes: ${ctx.seniorityNotes}`);
  for (const rule of ctx.contractStaffingRules ?? []) {
    laborNotes.push(`Contract staffing rule cited: ${rule}`);
  }

  return {
    metrics,
    laborNotes,
    gaps,
    disclaimer:
      "Staffing compliance support only. Reuses Government metrics. Not a contract violation determination.",
  };
}
