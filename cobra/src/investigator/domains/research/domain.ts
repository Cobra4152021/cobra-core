/** Cobra Research Edition domain (KC-009). */

export const RESEARCH_DOMAIN_ID = "research" as const;
export const RESEARCH_DOMAIN_VERSION = "0.1.0";

export const RESEARCH_DISCLAIMERS = [
  "Evidence synthesis and investigative support only.",
  "Not scientific peer review or publication certification.",
  "Not legal advice or regulatory determination.",
  "Conclusions depend on sources provided; missing or low-quality sources may materially affect findings.",
  "Heuristic reliability scores are indicative only and require human judgment.",
  "Human review required before publication, policy action, or external distribution.",
] as const;

export const RESEARCH_REVIEW_REQUIREMENTS = [
  "Verify citations resolve to authorized sources.",
  "Preserve competing hypotheses and contrary evidence.",
  "Label fact, inference, hypothesis, and unresolved issues distinctly.",
  "Do not overstate confidence from heuristic scores alone.",
  "Acknowledge source limitations and potential bias before publish.",
] as const;

export interface ResearchDomainDefinition {
  id: typeof RESEARCH_DOMAIN_ID;
  version: string;
  name: string;
  description: string;
  defaultDisclaimers: readonly string[];
  defaultReviewRequirements: readonly string[];
}

export const RESEARCH_DOMAIN: ResearchDomainDefinition = {
  id: RESEARCH_DOMAIN_ID,
  version: RESEARCH_DOMAIN_VERSION,
  name: "Cobra Research",
  description:
    "Evidence-based research and investigation workspace for literature review, evidence synthesis, field studies, intelligence assessment, and long-form anomaly investigations.",
  defaultDisclaimers: RESEARCH_DISCLAIMERS,
  defaultReviewRequirements: RESEARCH_REVIEW_REQUIREMENTS,
};
