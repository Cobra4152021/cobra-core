/** Deterministic government data normalization (KC-005). */

export type ParseConfidence = "confirmed" | "inferred" | "ambiguous" | "unparseable";

export interface NormalizedFiscalYear {
  original: string;
  startYear: number | null;
  endYear: number | null;
  label: string | null;
  confidence: ParseConfidence;
}

export interface NormalizedMoney {
  original: string;
  amount: number | null;
  currency: string;
  accountingSign: 1 | -1 | null;
  confidence: ParseConfidence;
}

export interface NormalizedStaffingCounts {
  original: Record<string, string | number | null | undefined>;
  authorized: number | null;
  budgeted: number | null;
  filled: number | null;
  active: number | null;
  deployable: number | null;
  vacant: number | null;
  confidence: ParseConfidence;
  assumptions: string[];
}

export interface NormalizedHours {
  original: Record<string, string | number | null | undefined>;
  regularHours: number | null;
  overtimeHours: number | null;
  compensatoryHours: number | null;
  leaveHours: number | null;
  trainingHours: number | null;
  confidence: ParseConfidence;
}

function num(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const cleaned = v.replace(/[$,\s]/g, "").replace(/^\((.*)\)$/, "-$1");
    if (!cleaned || cleaned === "-") return null;
    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/** Normalize fiscal year strings while preserving original text. */
export function normalizeFiscalYear(raw: string): NormalizedFiscalYear {
  const original = String(raw ?? "").trim();
  if (!original) {
    return { original, startYear: null, endYear: null, label: null, confidence: "unparseable" };
  }

  let m = original.match(/^FY\s*(\d{4})$/i);
  if (m) {
    const y = Number(m[1]);
    return { original, startYear: y - 1, endYear: y, label: `FY${y}`, confidence: "confirmed" };
  }

  m = original.match(/^Fiscal\s+Year\s+(\d{4})$/i);
  if (m) {
    const y = Number(m[1]);
    return { original, startYear: y - 1, endYear: y, label: `FY${y}`, confidence: "confirmed" };
  }

  m = original.match(/^(\d{4})\s*[-/]\s*(\d{2}|\d{4})$/);
  if (m) {
    const start = Number(m[1]);
    let end = Number(m[2]);
    if (end < 100) end = Math.floor(start / 100) * 100 + end;
    if (end === start + 1 || end === start) {
      return {
        original,
        startYear: start,
        endYear: end === start ? start + 1 : end,
        label: `FY${end === start ? start + 1 : end}`,
        confidence: "confirmed",
      };
    }
    return {
      original,
      startYear: start,
      endYear: end,
      label: null,
      confidence: "ambiguous",
    };
  }

  m = original.match(/^(\d{4})$/);
  if (m) {
    const y = Number(m[1]);
    return {
      original,
      startYear: y - 1,
      endYear: y,
      label: `FY${y}`,
      confidence: "inferred",
    };
  }

  return { original, startYear: null, endYear: null, label: null, confidence: "unparseable" };
}

export function normalizeMoney(raw: string, currency = "USD"): NormalizedMoney {
  const original = String(raw ?? "").trim();
  if (!original) {
    return { original, amount: null, currency, accountingSign: null, confidence: "unparseable" };
  }
  const paren = /^\(.*\)$/.test(original.replace(/\s/g, ""));
  const amount = num(original);
  if (amount === null) {
    return { original, amount: null, currency, accountingSign: null, confidence: "unparseable" };
  }
  const sign: 1 | -1 = amount < 0 || paren ? -1 : 1;
  return {
    original,
    amount: Math.abs(amount) * (sign === -1 ? -1 : 1),
    currency,
    accountingSign: sign,
    confidence: /[a-zA-Z]/.test(original.replace(/USD|CAD|EUR/gi, "")) ? "ambiguous" : "confirmed",
  };
}

export function normalizeStaffingCounts(
  input: Record<string, string | number | null | undefined>,
): NormalizedStaffingCounts {
  const authorized = num(input.authorized ?? input.authorized_positions);
  const budgeted = num(input.budgeted ?? input.budgeted_positions);
  const filled = num(input.filled ?? input.filled_positions);
  const active = num(input.active ?? input.active_staffing);
  const deployable = num(input.deployable ?? input.deployable_staffing);
  let vacant = num(input.vacant ?? input.vacancies);
  const assumptions: string[] = [];
  let confidence: ParseConfidence = "confirmed";

  if (vacant === null && authorized !== null && filled !== null) {
    vacant = Math.max(0, authorized - filled);
    assumptions.push("vacant inferred as authorized - filled");
    confidence = "inferred";
  }

  const present = [authorized, budgeted, filled, active, deployable, vacant].filter((x) => x !== null);
  if (present.length === 0) confidence = "unparseable";
  else if (assumptions.length) confidence = "inferred";

  return {
    original: { ...input },
    authorized,
    budgeted,
    filled,
    active,
    deployable,
    vacant,
    confidence,
    assumptions,
  };
}

export function normalizeHours(
  input: Record<string, string | number | null | undefined>,
): NormalizedHours {
  const regularHours = num(input.regularHours ?? input.regular_hours);
  const overtimeHours = num(input.overtimeHours ?? input.overtime_hours ?? input.ot_hours);
  const compensatoryHours = num(input.compensatoryHours ?? input.comp_time);
  const leaveHours = num(input.leaveHours ?? input.leave_hours);
  const trainingHours = num(input.trainingHours ?? input.training_hours);
  const present = [regularHours, overtimeHours, compensatoryHours, leaveHours, trainingHours].some(
    (x) => x !== null,
  );
  return {
    original: { ...input },
    regularHours,
    overtimeHours,
    compensatoryHours,
    leaveHours,
    trainingHours,
    confidence: present ? "confirmed" : "unparseable",
  };
}
