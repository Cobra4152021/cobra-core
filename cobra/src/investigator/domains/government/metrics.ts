/** Government metrics engine — calculate only when source fields exist (KC-005). */

export type MetricConfidence = "high" | "medium" | "low" | "insufficient";

export interface GovernmentMetric {
  id: string;
  name: string;
  category: "budget" | "staffing" | "overtime" | "equipment" | "training";
  value: number | null;
  formula: string;
  sourceFields: string[];
  period: string | null;
  units: string;
  assumptions: string[];
  confidence: MetricConfidence;
  citations: string[];
  missingFields: string[];
}

function pct(n: number, d: number): number {
  return d === 0 ? NaN : (n / d) * 100;
}

function metric(
  partial: Omit<GovernmentMetric, "confidence" | "missingFields"> & {
    required: Array<number | null | undefined>;
    requiredNames: string[];
  },
): GovernmentMetric {
  const missing = partial.requiredNames.filter((_, i) => {
    const v = partial.required[i];
    return v === null || v === undefined || (typeof v === "number" && !Number.isFinite(v));
  });
  let confidence: MetricConfidence = "high";
  let value = partial.value;
  if (missing.length) {
    value = null;
    confidence = "insufficient";
  } else if (partial.assumptions.length) {
    confidence = "medium";
  } else if (value !== null && !Number.isFinite(value)) {
    value = null;
    confidence = "insufficient";
  }
  return {
    id: partial.id,
    name: partial.name,
    category: partial.category,
    value: value !== null && Number.isFinite(value) ? value : null,
    formula: partial.formula,
    sourceFields: partial.sourceFields,
    period: partial.period,
    units: partial.units,
    assumptions: partial.assumptions,
    confidence,
    citations: partial.citations,
    missingFields: missing,
  };
}

export function computeBudgetMetrics(input: {
  adopted?: number | null;
  revised?: number | null;
  actual?: number | null;
  priorActual?: number | null;
  categoryAmount?: number | null;
  totalAmount?: number | null;
  recurring?: number | null;
  period?: string | null;
  citations?: string[];
}): GovernmentMetric[] {
  const cites = input.citations ?? [];
  const period = input.period ?? null;
  return [
    metric({
      id: "adopted_variance",
      name: "Adopted-to-actual variance",
      category: "budget",
      value:
        input.adopted != null && input.actual != null ? input.actual - input.adopted : null,
      formula: "actual - adopted",
      sourceFields: ["actual", "adopted"],
      period,
      units: "currency",
      assumptions: [],
      citations: cites,
      required: [input.adopted, input.actual],
      requiredNames: ["adopted", "actual"],
    }),
    metric({
      id: "revised_variance",
      name: "Revised-to-actual variance",
      category: "budget",
      value:
        input.revised != null && input.actual != null ? input.actual - input.revised : null,
      formula: "actual - revised",
      sourceFields: ["actual", "revised"],
      period,
      units: "currency",
      assumptions: [],
      citations: cites,
      required: [input.revised, input.actual],
      requiredNames: ["revised", "actual"],
    }),
    metric({
      id: "yoy_change",
      name: "Year-over-year actual change",
      category: "budget",
      value:
        input.actual != null && input.priorActual != null
          ? input.actual - input.priorActual
          : null,
      formula: "actual - priorActual",
      sourceFields: ["actual", "priorActual"],
      period,
      units: "currency",
      assumptions: [],
      citations: cites,
      required: [input.actual, input.priorActual],
      requiredNames: ["actual", "priorActual"],
    }),
    metric({
      id: "category_share",
      name: "Category share of total",
      category: "budget",
      value:
        input.categoryAmount != null && input.totalAmount != null
          ? pct(input.categoryAmount, input.totalAmount)
          : null,
      formula: "(categoryAmount / totalAmount) * 100",
      sourceFields: ["categoryAmount", "totalAmount"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.categoryAmount, input.totalAmount],
      requiredNames: ["categoryAmount", "totalAmount"],
    }),
    metric({
      id: "recurring_cost_share",
      name: "Recurring-cost share",
      category: "budget",
      value:
        input.recurring != null && input.actual != null ? pct(input.recurring, input.actual) : null,
      formula: "(recurring / actual) * 100",
      sourceFields: ["recurring", "actual"],
      period,
      units: "percent",
      assumptions: ["Recurring classification supplied by source"],
      citations: cites,
      required: [input.recurring, input.actual],
      requiredNames: ["recurring", "actual"],
    }),
  ];
}

export function computeStaffingMetrics(input: {
  authorized?: number | null;
  filled?: number | null;
  deployable?: number | null;
  vacant?: number | null;
  attrition?: number | null;
  averageStaff?: number | null;
  hiringLagDays?: number | null;
  period?: string | null;
  citations?: string[];
}): GovernmentMetric[] {
  const cites = input.citations ?? [];
  const period = input.period ?? null;
  const vacant =
    input.vacant ??
    (input.authorized != null && input.filled != null
      ? Math.max(0, input.authorized - input.filled)
      : null);
  const vacantAssumptions =
    input.vacant == null && vacant != null ? ["vacant inferred as authorized - filled"] : [];

  return [
    metric({
      id: "vacancy_rate",
      name: "Vacancy rate",
      category: "staffing",
      value:
        vacant != null && input.authorized != null ? pct(vacant, input.authorized) : null,
      formula: "(vacant / authorized) * 100",
      sourceFields: ["vacant", "authorized"],
      period,
      units: "percent",
      assumptions: vacantAssumptions,
      citations: cites,
      required: [vacant, input.authorized],
      requiredNames: ["vacant", "authorized"],
    }),
    metric({
      id: "filled_rate",
      name: "Filled rate",
      category: "staffing",
      value:
        input.filled != null && input.authorized != null
          ? pct(input.filled, input.authorized)
          : null,
      formula: "(filled / authorized) * 100",
      sourceFields: ["filled", "authorized"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.filled, input.authorized],
      requiredNames: ["filled", "authorized"],
    }),
    metric({
      id: "deployable_rate",
      name: "Deployable rate",
      category: "staffing",
      value:
        input.deployable != null && input.authorized != null
          ? pct(input.deployable, input.authorized)
          : null,
      formula: "(deployable / authorized) * 100",
      sourceFields: ["deployable", "authorized"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.deployable, input.authorized],
      requiredNames: ["deployable", "authorized"],
    }),
    metric({
      id: "attrition_rate",
      name: "Attrition rate",
      category: "staffing",
      value:
        input.attrition != null && input.averageStaff != null
          ? pct(input.attrition, input.averageStaff)
          : null,
      formula: "(attrition / averageStaff) * 100",
      sourceFields: ["attrition", "averageStaff"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.attrition, input.averageStaff],
      requiredNames: ["attrition", "averageStaff"],
    }),
    metric({
      id: "hiring_lag",
      name: "Hiring lag",
      category: "staffing",
      value: input.hiringLagDays ?? null,
      formula: "hiringLagDays (source)",
      sourceFields: ["hiringLagDays"],
      period,
      units: "days",
      assumptions: [],
      citations: cites,
      required: [input.hiringLagDays],
      requiredNames: ["hiringLagDays"],
    }),
  ];
}

export function computeOvertimeMetrics(input: {
  overtimeHours?: number | null;
  overtimeCost?: number | null;
  filledPositions?: number | null;
  vacancies?: number | null;
  payrollCost?: number | null;
  period?: string | null;
  citations?: string[];
}): GovernmentMetric[] {
  const cites = input.citations ?? [];
  const period = input.period ?? null;
  const avgRate =
    input.overtimeCost != null && input.overtimeHours != null && input.overtimeHours !== 0
      ? input.overtimeCost / input.overtimeHours
      : null;

  return [
    metric({
      id: "overtime_hours",
      name: "Overtime hours",
      category: "overtime",
      value: input.overtimeHours ?? null,
      formula: "overtimeHours (source)",
      sourceFields: ["overtimeHours"],
      period,
      units: "hours",
      assumptions: [],
      citations: cites,
      required: [input.overtimeHours],
      requiredNames: ["overtimeHours"],
    }),
    metric({
      id: "overtime_cost",
      name: "Overtime cost",
      category: "overtime",
      value: input.overtimeCost ?? null,
      formula: "overtimeCost (source)",
      sourceFields: ["overtimeCost"],
      period,
      units: "currency",
      assumptions: [],
      citations: cites,
      required: [input.overtimeCost],
      requiredNames: ["overtimeCost"],
    }),
    metric({
      id: "average_overtime_rate",
      name: "Average overtime rate",
      category: "overtime",
      value: avgRate,
      formula: "overtimeCost / overtimeHours",
      sourceFields: ["overtimeCost", "overtimeHours"],
      period,
      units: "currency_per_hour",
      assumptions: [],
      citations: cites,
      required: [input.overtimeCost, input.overtimeHours],
      requiredNames: ["overtimeCost", "overtimeHours"],
    }),
    metric({
      id: "overtime_per_employee",
      name: "Overtime per filled position",
      category: "overtime",
      value:
        input.overtimeHours != null && input.filledPositions != null && input.filledPositions !== 0
          ? input.overtimeHours / input.filledPositions
          : null,
      formula: "overtimeHours / filledPositions",
      sourceFields: ["overtimeHours", "filledPositions"],
      period,
      units: "hours_per_position",
      assumptions: [],
      citations: cites,
      required: [input.overtimeHours, input.filledPositions],
      requiredNames: ["overtimeHours", "filledPositions"],
    }),
    metric({
      id: "overtime_per_vacancy",
      name: "Overtime per vacancy",
      category: "overtime",
      value:
        input.overtimeHours != null && input.vacancies != null && input.vacancies !== 0
          ? input.overtimeHours / input.vacancies
          : null,
      formula: "overtimeHours / vacancies",
      sourceFields: ["overtimeHours", "vacancies"],
      period,
      units: "hours_per_vacancy",
      assumptions: ["Does not prove vacancies caused overtime"],
      citations: cites,
      required: [input.overtimeHours, input.vacancies],
      requiredNames: ["overtimeHours", "vacancies"],
    }),
    metric({
      id: "overtime_share_of_payroll",
      name: "Overtime share of payroll",
      category: "overtime",
      value:
        input.overtimeCost != null && input.payrollCost != null
          ? pct(input.overtimeCost, input.payrollCost)
          : null,
      formula: "(overtimeCost / payrollCost) * 100",
      sourceFields: ["overtimeCost", "payrollCost"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.overtimeCost, input.payrollCost],
      requiredNames: ["overtimeCost", "payrollCost"],
    }),
  ];
}

export function computeEquipmentMetrics(input: {
  ageYears?: number | null;
  expectedLifeYears?: number | null;
  maintenanceCost?: number | null;
  acquisitionCost?: number | null;
  downtimeHours?: number | null;
  availableHours?: number | null;
  period?: string | null;
  citations?: string[];
}): GovernmentMetric[] {
  const cites = input.citations ?? [];
  const period = input.period ?? null;
  return [
    metric({
      id: "lifecycle_age",
      name: "Lifecycle age",
      category: "equipment",
      value: input.ageYears ?? null,
      formula: "ageYears (source)",
      sourceFields: ["ageYears"],
      period,
      units: "years",
      assumptions: [],
      citations: cites,
      required: [input.ageYears],
      requiredNames: ["ageYears"],
    }),
    metric({
      id: "maintenance_to_value_ratio",
      name: "Maintenance-to-value ratio",
      category: "equipment",
      value:
        input.maintenanceCost != null &&
        input.acquisitionCost != null &&
        input.acquisitionCost !== 0
          ? input.maintenanceCost / input.acquisitionCost
          : null,
      formula: "maintenanceCost / acquisitionCost",
      sourceFields: ["maintenanceCost", "acquisitionCost"],
      period,
      units: "ratio",
      assumptions: [],
      citations: cites,
      required: [input.maintenanceCost, input.acquisitionCost],
      requiredNames: ["maintenanceCost", "acquisitionCost"],
    }),
    metric({
      id: "downtime_rate",
      name: "Downtime rate",
      category: "equipment",
      value:
        input.downtimeHours != null && input.availableHours != null
          ? pct(input.downtimeHours, input.availableHours)
          : null,
      formula: "(downtimeHours / availableHours) * 100",
      sourceFields: ["downtimeHours", "availableHours"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.downtimeHours, input.availableHours],
      requiredNames: ["downtimeHours", "availableHours"],
    }),
    metric({
      id: "replacement_urgency",
      name: "Replacement urgency score",
      category: "equipment",
      value:
        input.ageYears != null && input.expectedLifeYears != null && input.expectedLifeYears !== 0
          ? Math.min(100, pct(input.ageYears, input.expectedLifeYears))
          : null,
      formula: "min(100, (ageYears / expectedLifeYears) * 100)",
      sourceFields: ["ageYears", "expectedLifeYears"],
      period,
      units: "score_0_100",
      assumptions: ["Heuristic only; not an engineering certification"],
      citations: cites,
      required: [input.ageYears, input.expectedLifeYears],
      requiredNames: ["ageYears", "expectedLifeYears"],
    }),
  ];
}

export function computeTrainingMetrics(input: {
  completed?: number | null;
  required?: number | null;
  expiringSoon?: number | null;
  missingRecords?: number | null;
  period?: string | null;
  citations?: string[];
}): GovernmentMetric[] {
  const cites = input.citations ?? [];
  const period = input.period ?? null;
  return [
    metric({
      id: "completion_rate",
      name: "Training completion rate",
      category: "training",
      value:
        input.completed != null && input.required != null
          ? pct(input.completed, input.required)
          : null,
      formula: "(completed / required) * 100",
      sourceFields: ["completed", "required"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.completed, input.required],
      requiredNames: ["completed", "required"],
    }),
    metric({
      id: "expiration_risk",
      name: "Expiration risk share",
      category: "training",
      value:
        input.expiringSoon != null && input.required != null
          ? pct(input.expiringSoon, input.required)
          : null,
      formula: "(expiringSoon / required) * 100",
      sourceFields: ["expiringSoon", "required"],
      period,
      units: "percent",
      assumptions: ["Expiring-soon window defined by source"],
      citations: cites,
      required: [input.expiringSoon, input.required],
      requiredNames: ["expiringSoon", "required"],
    }),
    metric({
      id: "missing_record_rate",
      name: "Missing-record rate",
      category: "training",
      value:
        input.missingRecords != null && input.required != null
          ? pct(input.missingRecords, input.required)
          : null,
      formula: "(missingRecords / required) * 100",
      sourceFields: ["missingRecords", "required"],
      period,
      units: "percent",
      assumptions: [],
      citations: cites,
      required: [input.missingRecords, input.required],
      requiredNames: ["missingRecords", "required"],
    }),
  ];
}
