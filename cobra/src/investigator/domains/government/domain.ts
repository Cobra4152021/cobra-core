/** Cobra Government domain definition (KC-005). */

export const GOVERNMENT_DOMAIN_ID = "government" as const;
export const GOVERNMENT_DOMAIN_VERSION = "0.1.0";

export const GOVERNMENT_DISCLAIMERS = [
  "Informational and investigative support only.",
  "Not legal advice.",
  "Not an audit opinion unless reviewed and issued by an authorized auditor.",
  "Not a disciplinary finding.",
  "Not a final compliance determination.",
  "Conclusions depend on records provided; missing records may materially affect findings.",
  "Human review required before publication or action.",
] as const;

export const GOVERNMENT_REVIEW_REQUIREMENTS = [
  "Confirm citations resolve to organization-authorized evidence.",
  "Preserve competing hypotheses and contrary evidence.",
  "Label fact, inference, allegation, hypothesis, professional judgment, and unresolved issues distinctly.",
  "Do not assert fraud, misconduct, corruption, or criminality without sufficient cited evidence.",
  "Acknowledge data limitations and privacy sensitivity before publish.",
] as const;

export const GOVERNMENT_DEFAULT_ROLES = [
  "owner",
  "admin",
  "researcher",
] as const;

export const GOVERNMENT_DEFAULT_REPORT_SECTIONS = [
  "cover",
  "executive_summary",
  "authority_and_purpose",
  "investigation_objective",
  "scope",
  "methodology",
  "evidence_reviewed",
  "data_limitations",
  "background",
  "timeline",
  "metrics_and_trends",
  "competing_hypotheses",
  "findings",
  "contrary_or_mitigating_evidence",
  "missing_evidence",
  "recommendations",
  "management_questions",
  "confidence_and_readiness",
  "appendix",
  "citations",
  "report_version_and_audit_metadata",
] as const;

export interface GovernmentDomainDefinition {
  id: typeof GOVERNMENT_DOMAIN_ID;
  version: string;
  name: string;
  description: string;
  defaultRoles: readonly string[];
  defaultDisclaimers: readonly string[];
  defaultReviewRequirements: readonly string[];
  defaultReportSections: readonly string[];
}

export const GOVERNMENT_DOMAIN: GovernmentDomainDefinition = {
  id: GOVERNMENT_DOMAIN_ID,
  version: GOVERNMENT_DOMAIN_VERSION,
  name: "Cobra Government",
  description:
    "Evidence-based investigation workspace for cities, counties, public safety agencies, auditors, and labor-management review teams.",
  defaultRoles: GOVERNMENT_DEFAULT_ROLES,
  defaultDisclaimers: GOVERNMENT_DISCLAIMERS,
  defaultReviewRequirements: GOVERNMENT_REVIEW_REQUIREMENTS,
  defaultReportSections: GOVERNMENT_DEFAULT_REPORT_SECTIONS,
};
