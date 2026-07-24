/** Cobra Labor & Employment Relations domain (KC-006). */

export const LABOR_DOMAIN_ID = "labor" as const;
export const LABOR_DOMAIN_VERSION = "0.1.0";

export const LABOR_DISCLAIMERS = [
  "Informational and investigative support only.",
  "Not legal advice.",
  "Not a determination of contract violation, unfair labor practice, or liability.",
  "Does not replace attorneys, union representatives, labor relations professionals, arbitrators, or mediators.",
  "Conclusions depend on records provided; missing records may materially affect findings.",
  "Human review required before filing, bargaining, publication, or action.",
] as const;

export const LABOR_REVIEW_REQUIREMENTS = [
  "Confirm citations resolve to organization-authorized evidence.",
  "Preserve competing hypotheses and contrary evidence.",
  "Do not assert ULP, breach, or liability without authorized human determination.",
  "Label fact, inference, allegation, hypothesis, past practice claim, and unresolved issues distinctly.",
  "Acknowledge sensitivity of personnel and labor-relations records before publish.",
] as const;

export const LABOR_DEFAULT_REPORT_SECTIONS = [
  "executive_summary",
  "scope",
  "contract_articles_reviewed",
  "timeline",
  "evidence",
  "supporting_evidence",
  "contrary_evidence",
  "missing_evidence",
  "findings",
  "recommendations",
  "confidence",
  "appendix",
  "citations",
] as const;

export interface LaborDomainDefinition {
  id: typeof LABOR_DOMAIN_ID;
  version: string;
  name: string;
  description: string;
  defaultDisclaimers: readonly string[];
  defaultReviewRequirements: readonly string[];
  defaultReportSections: readonly string[];
}

export const LABOR_DOMAIN: LaborDomainDefinition = {
  id: LABOR_DOMAIN_ID,
  version: LABOR_DOMAIN_VERSION,
  name: "Cobra Labor",
  description:
    "Evidence-based labor-management investigation workspace for CBAs, MOUs, grievances, arbitration prep, staffing compliance, and institutional labor knowledge.",
  defaultDisclaimers: LABOR_DISCLAIMERS,
  defaultReviewRequirements: LABOR_REVIEW_REQUIREMENTS,
  defaultReportSections: LABOR_DEFAULT_REPORT_SECTIONS,
};
