/** Government evidence taxonomy (KC-005). */

import type { GovernmentSensitivity } from "./sensitivity.js";

export type GovernmentEvidenceCategoryId =
  | "adopted_budget"
  | "revised_budget"
  | "expenditure_report"
  | "payroll"
  | "overtime_report"
  | "position_control"
  | "vacancy_report"
  | "staffing_roster"
  | "deployment_schedule"
  | "leave_report"
  | "workers_compensation_record"
  | "policy"
  | "procedure"
  | "mou"
  | "labor_agreement"
  | "ordinance"
  | "resolution"
  | "legislative_file"
  | "agenda_item"
  | "staff_report"
  | "audit_report"
  | "grant_agreement"
  | "procurement_record"
  | "contract"
  | "invoice"
  | "purchase_order"
  | "fleet_record"
  | "equipment_inventory"
  | "training_record"
  | "workload_report"
  | "incident_summary"
  | "correspondence"
  | "meeting_minutes"
  | "organizational_chart"
  | "public_data"
  | "other";

export interface GovernmentEvidenceCategory {
  id: GovernmentEvidenceCategoryId;
  label: string;
  typicalAuthority: string;
  expectedDateFields: string[];
  expectedVersionFields: string[];
  commonQualityRisks: string[];
  corroboratingSources: string[];
  privacySensitivity: GovernmentSensitivity;
  retentionNotes: string;
}

export const GOVERNMENT_EVIDENCE_CATEGORIES: GovernmentEvidenceCategory[] = [
  {
    id: "adopted_budget",
    label: "Adopted budget",
    typicalAuthority: "Finance / Budget office",
    expectedDateFields: ["fiscal_year", "adoption_date"],
    expectedVersionFields: ["budget_version", "ordinance_number"],
    commonQualityRisks: ["draft vs adopted confusion", "missing amendments"],
    corroboratingSources: ["revised_budget", "resolution"],
    privacySensitivity: "public",
    retentionNotes: "Retain per local records schedule; often permanent.",
  },
  {
    id: "revised_budget",
    label: "Revised budget",
    typicalAuthority: "Finance / Budget office",
    expectedDateFields: ["fiscal_year", "revision_date"],
    expectedVersionFields: ["revision_number"],
    commonQualityRisks: ["incomplete transfer history"],
    corroboratingSources: ["adopted_budget", "expenditure_report"],
    privacySensitivity: "internal",
    retentionNotes: "Retain with budget cycle records.",
  },
  {
    id: "expenditure_report",
    label: "Expenditure report",
    typicalAuthority: "Finance",
    expectedDateFields: ["period_start", "period_end", "as_of"],
    expectedVersionFields: ["report_run_id"],
    commonQualityRisks: ["encumbrance vs actual mix", "coding changes"],
    corroboratingSources: ["invoice", "payroll"],
    privacySensitivity: "internal",
    retentionNotes: "Fiscal retention period.",
  },
  {
    id: "payroll",
    label: "Payroll",
    typicalAuthority: "HR / Payroll",
    expectedDateFields: ["pay_period", "check_date"],
    expectedVersionFields: ["pay_cycle"],
    commonQualityRisks: ["PII exposure", "coding reclassifications"],
    corroboratingSources: ["overtime_report", "position_control"],
    privacySensitivity: "personnel",
    retentionNotes: "Personnel/payroll retention; restrict access.",
  },
  {
    id: "overtime_report",
    label: "Overtime report",
    typicalAuthority: "HR / Operations",
    expectedDateFields: ["period_start", "period_end"],
    expectedVersionFields: ["report_version"],
    commonQualityRisks: ["hours vs dollars mismatch", "incomplete units"],
    corroboratingSources: ["payroll", "deployment_schedule", "vacancy_report"],
    privacySensitivity: "personnel",
    retentionNotes: "Personnel retention; aggregate preferred for reports.",
  },
  {
    id: "position_control",
    label: "Position control",
    typicalAuthority: "HR / Budget",
    expectedDateFields: ["as_of", "fiscal_year"],
    expectedVersionFields: ["position_control_version"],
    commonQualityRisks: ["authorized vs budgeted confusion"],
    corroboratingSources: ["vacancy_report", "staffing_roster"],
    privacySensitivity: "internal",
    retentionNotes: "Position control archives.",
  },
  {
    id: "vacancy_report",
    label: "Vacancy report",
    typicalAuthority: "HR",
    expectedDateFields: ["as_of", "vacancy_start"],
    expectedVersionFields: [],
    commonQualityRisks: ["frozen vs vacant", "duration gaps"],
    corroboratingSources: ["position_control", "staffing_roster"],
    privacySensitivity: "internal",
    retentionNotes: "HR operational retention.",
  },
  {
    id: "staffing_roster",
    label: "Staffing roster",
    typicalAuthority: "HR / Operations",
    expectedDateFields: ["as_of"],
    expectedVersionFields: [],
    commonQualityRisks: ["PII", "stale assignments"],
    corroboratingSources: ["deployment_schedule", "leave_report"],
    privacySensitivity: "personnel",
    retentionNotes: "Restrict individual identifiers in published reports.",
  },
  {
    id: "deployment_schedule",
    label: "Deployment schedule",
    typicalAuthority: "Operations",
    expectedDateFields: ["shift_date", "period"],
    expectedVersionFields: [],
    commonQualityRisks: ["security sensitivity", "incomplete posts"],
    corroboratingSources: ["workload_report", "overtime_report"],
    privacySensitivity: "security_sensitive",
    retentionNotes: "Operational retention; limit public detail.",
  },
  {
    id: "leave_report",
    label: "Leave report",
    typicalAuthority: "HR",
    expectedDateFields: ["period_start", "period_end"],
    expectedVersionFields: [],
    commonQualityRisks: ["medical privacy", "category aggregation needed"],
    corroboratingSources: ["workers_compensation_record", "staffing_roster"],
    privacySensitivity: "personnel",
    retentionNotes: "Do not publish individual medical details.",
  },
  {
    id: "workers_compensation_record",
    label: "Workers’ compensation record",
    typicalAuthority: "Risk / HR",
    expectedDateFields: ["injury_date", "leave_period"],
    expectedVersionFields: [],
    commonQualityRisks: ["medical privacy"],
    corroboratingSources: ["leave_report"],
    privacySensitivity: "personnel",
    retentionNotes: "Highly restricted; aggregate only in reports.",
  },
  {
    id: "policy",
    label: "Policy",
    typicalAuthority: "Policy owner / Clerk",
    expectedDateFields: ["effective_date", "superseded_date"],
    expectedVersionFields: ["policy_number", "revision"],
    commonQualityRisks: ["stale version", "missing acknowledgments"],
    corroboratingSources: ["procedure", "training_record"],
    privacySensitivity: "public",
    retentionNotes: "Retain superseded versions for audit trail.",
  },
  {
    id: "procedure",
    label: "Procedure",
    typicalAuthority: "Department",
    expectedDateFields: ["effective_date"],
    expectedVersionFields: ["revision"],
    commonQualityRisks: ["informal practice drift"],
    corroboratingSources: ["policy"],
    privacySensitivity: "internal",
    retentionNotes: "Departmental retention.",
  },
  {
    id: "mou",
    label: "MOU",
    typicalAuthority: "Labor / Legal",
    expectedDateFields: ["effective_date", "expiration_date"],
    expectedVersionFields: ["mou_id"],
    commonQualityRisks: ["side letters missing"],
    corroboratingSources: ["labor_agreement"],
    privacySensitivity: "labor_relations",
    retentionNotes: "Labor records retention.",
  },
  {
    id: "labor_agreement",
    label: "Labor agreement",
    typicalAuthority: "Labor / Legal",
    expectedDateFields: ["effective_date", "expiration_date"],
    expectedVersionFields: ["agreement_version"],
    commonQualityRisks: ["incomplete appendices"],
    corroboratingSources: ["mou", "payroll"],
    privacySensitivity: "labor_relations",
    retentionNotes: "Labor records retention.",
  },
  {
    id: "ordinance",
    label: "Ordinance",
    typicalAuthority: "Clerk / Legislative body",
    expectedDateFields: ["adoption_date", "effective_date"],
    expectedVersionFields: ["ordinance_number"],
    commonQualityRisks: ["amendment chain incomplete"],
    corroboratingSources: ["resolution", "legislative_file"],
    privacySensitivity: "public",
    retentionNotes: "Often permanent.",
  },
  {
    id: "resolution",
    label: "Resolution",
    typicalAuthority: "Clerk",
    expectedDateFields: ["adoption_date"],
    expectedVersionFields: ["resolution_number"],
    commonQualityRisks: ["missing attachments"],
    corroboratingSources: ["agenda_item", "staff_report"],
    privacySensitivity: "public",
    retentionNotes: "Legislative retention.",
  },
  {
    id: "legislative_file",
    label: "Legislative file",
    typicalAuthority: "Clerk",
    expectedDateFields: ["filed_date"],
    expectedVersionFields: ["file_number"],
    commonQualityRisks: ["incomplete packet"],
    corroboratingSources: ["agenda_item", "staff_report"],
    privacySensitivity: "public",
    retentionNotes: "Legislative retention.",
  },
  {
    id: "agenda_item",
    label: "Agenda item",
    typicalAuthority: "Clerk",
    expectedDateFields: ["meeting_date"],
    expectedVersionFields: ["item_number"],
    commonQualityRisks: ["late substitutes"],
    corroboratingSources: ["meeting_minutes", "staff_report"],
    privacySensitivity: "public",
    retentionNotes: "Meeting records retention.",
  },
  {
    id: "staff_report",
    label: "Staff report",
    typicalAuthority: "Department",
    expectedDateFields: ["report_date"],
    expectedVersionFields: ["report_id"],
    commonQualityRisks: ["unsupported assertions"],
    corroboratingSources: ["agenda_item", "expenditure_report"],
    privacySensitivity: "internal",
    retentionNotes: "Administrative retention.",
  },
  {
    id: "audit_report",
    label: "Audit report",
    typicalAuthority: "Auditor / IG",
    expectedDateFields: ["report_date", "period_covered"],
    expectedVersionFields: ["report_number"],
    commonQualityRisks: ["scope limitations omitted"],
    corroboratingSources: ["expenditure_report", "policy"],
    privacySensitivity: "internal",
    retentionNotes: "Audit retention schedule.",
  },
  {
    id: "grant_agreement",
    label: "Grant agreement",
    typicalAuthority: "Grants office",
    expectedDateFields: ["award_date", "period_start", "period_end"],
    expectedVersionFields: ["award_number", "amendment"],
    commonQualityRisks: ["amendments missing", "match rules unclear"],
    corroboratingSources: ["expenditure_report", "procurement_record"],
    privacySensitivity: "internal",
    retentionNotes: "Grant retention (often 3–7 years after closeout).",
  },
  {
    id: "procurement_record",
    label: "Procurement record",
    typicalAuthority: "Purchasing",
    expectedDateFields: ["solicitation_date", "award_date"],
    expectedVersionFields: ["solicitation_number"],
    commonQualityRisks: ["incomplete competition file"],
    corroboratingSources: ["contract", "purchase_order"],
    privacySensitivity: "internal",
    retentionNotes: "Procurement retention.",
  },
  {
    id: "contract",
    label: "Contract",
    typicalAuthority: "Purchasing / Legal",
    expectedDateFields: ["effective_date", "expiration_date"],
    expectedVersionFields: ["contract_number", "amendment"],
    commonQualityRisks: ["missing amendments"],
    corroboratingSources: ["invoice", "procurement_record"],
    privacySensitivity: "internal",
    retentionNotes: "Contract retention.",
  },
  {
    id: "invoice",
    label: "Invoice",
    typicalAuthority: "Finance / Vendor",
    expectedDateFields: ["invoice_date", "service_period"],
    expectedVersionFields: ["invoice_number"],
    commonQualityRisks: ["duplicate payments", "wrong PO"],
    corroboratingSources: ["purchase_order", "contract"],
    privacySensitivity: "internal",
    retentionNotes: "Fiscal retention.",
  },
  {
    id: "purchase_order",
    label: "Purchase order",
    typicalAuthority: "Purchasing",
    expectedDateFields: ["po_date"],
    expectedVersionFields: ["po_number"],
    commonQualityRisks: ["change orders missing"],
    corroboratingSources: ["invoice", "contract"],
    privacySensitivity: "internal",
    retentionNotes: "Procurement retention.",
  },
  {
    id: "fleet_record",
    label: "Fleet record",
    typicalAuthority: "Fleet / Public works",
    expectedDateFields: ["purchase_date", "disposal_date"],
    expectedVersionFields: ["asset_id"],
    commonQualityRisks: ["incomplete maintenance history"],
    corroboratingSources: ["equipment_inventory", "invoice"],
    privacySensitivity: "internal",
    retentionNotes: "Asset lifecycle retention.",
  },
  {
    id: "equipment_inventory",
    label: "Equipment inventory",
    typicalAuthority: "Asset management",
    expectedDateFields: ["as_of", "acquisition_date"],
    expectedVersionFields: ["inventory_version"],
    commonQualityRisks: ["ghost assets", "missing serials"],
    corroboratingSources: ["fleet_record", "purchase_order"],
    privacySensitivity: "internal",
    retentionNotes: "Inventory cycle retention.",
  },
  {
    id: "training_record",
    label: "Training record",
    typicalAuthority: "Training / HR",
    expectedDateFields: ["completion_date", "expiration_date"],
    expectedVersionFields: ["course_id"],
    commonQualityRisks: ["PII", "missing certificates"],
    corroboratingSources: ["policy", "procedure"],
    privacySensitivity: "personnel",
    retentionNotes: "Aggregate for publication; restrict individuals.",
  },
  {
    id: "workload_report",
    label: "Workload report",
    typicalAuthority: "Operations / CAD",
    expectedDateFields: ["period_start", "period_end"],
    expectedVersionFields: ["report_run"],
    commonQualityRisks: ["definition changes", "security sensitivity"],
    corroboratingSources: ["incident_summary", "deployment_schedule"],
    privacySensitivity: "security_sensitive",
    retentionNotes: "Limit operational detail in public reports.",
  },
  {
    id: "incident_summary",
    label: "Incident summary",
    typicalAuthority: "Operations",
    expectedDateFields: ["incident_date"],
    expectedVersionFields: [],
    commonQualityRisks: ["PII", "restricted details"],
    corroboratingSources: ["workload_report"],
    privacySensitivity: "security_sensitive",
    retentionNotes: "Use summaries; avoid victim/suspect identifiers.",
  },
  {
    id: "correspondence",
    label: "Correspondence",
    typicalAuthority: "Department",
    expectedDateFields: ["sent_date"],
    expectedVersionFields: [],
    commonQualityRisks: ["incomplete threads", "private contacts"],
    corroboratingSources: ["meeting_minutes"],
    privacySensitivity: "internal",
    retentionNotes: "Email/records retention; redact contacts for publish.",
  },
  {
    id: "meeting_minutes",
    label: "Meeting minutes",
    typicalAuthority: "Clerk / Department",
    expectedDateFields: ["meeting_date"],
    expectedVersionFields: [],
    commonQualityRisks: ["draft vs approved"],
    corroboratingSources: ["agenda_item"],
    privacySensitivity: "public",
    retentionNotes: "Meeting records retention.",
  },
  {
    id: "organizational_chart",
    label: "Organizational chart",
    typicalAuthority: "HR / Administration",
    expectedDateFields: ["as_of"],
    expectedVersionFields: ["chart_version"],
    commonQualityRisks: ["stale structure"],
    corroboratingSources: ["position_control"],
    privacySensitivity: "internal",
    retentionNotes: "Administrative retention.",
  },
  {
    id: "public_data",
    label: "Public data",
    typicalAuthority: "External / open data",
    expectedDateFields: ["publication_date", "as_of"],
    expectedVersionFields: ["dataset_version"],
    commonQualityRisks: ["methodology opacity"],
    corroboratingSources: ["expenditure_report", "workload_report"],
    privacySensitivity: "public",
    retentionNotes: "Cite source URL/version.",
  },
  {
    id: "other",
    label: "Other",
    typicalAuthority: "Various",
    expectedDateFields: ["as_of"],
    expectedVersionFields: [],
    commonQualityRisks: ["unclear provenance"],
    corroboratingSources: [],
    privacySensitivity: "unknown",
    retentionNotes: "Classify before publication.",
  },
];

export function getEvidenceCategory(id: string): GovernmentEvidenceCategory | null {
  return GOVERNMENT_EVIDENCE_CATEGORIES.find((c) => c.id === id) ?? null;
}
