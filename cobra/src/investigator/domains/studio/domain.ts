/** Cobra Intelligence Studio domain (KC-007). */

export const STUDIO_DOMAIN_ID = "studio" as const;
export const STUDIO_DOMAIN_VERSION = "0.1.0";

export const STUDIO_DISCLAIMERS = [
  "Decision-support visualization only.",
  "Not legal advice.",
  "Consumes Investigator, Government, and Labor domain data; does not replace source analysis.",
  "Charts, graphs, and comparisons are illustrative until reviewed against authorized evidence.",
  "Human review required before publication or action.",
] as const;

export interface StudioDomainDefinition {
  id: typeof STUDIO_DOMAIN_ID;
  version: string;
  name: string;
  description: string;
  defaultDisclaimers: readonly string[];
}

export const STUDIO_DOMAIN: StudioDomainDefinition = {
  id: STUDIO_DOMAIN_ID,
  version: STUDIO_DOMAIN_VERSION,
  name: "Cobra Intelligence Studio",
  description:
    "Unified visualization and decision-support workspace for investigations, timelines, graphs, analytics, and reports.",
  defaultDisclaimers: STUDIO_DISCLAIMERS,
};
