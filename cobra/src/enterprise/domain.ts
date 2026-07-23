/** KC-010 Enterprise Platform domain metadata. */

export const ENTERPRISE_DOMAIN_ID = "enterprise" as const;
export const ENTERPRISE_DOMAIN_VERSION = "0.1.0";

export const ENTERPRISE_DISCLAIMERS = [
  "Enterprise governance features enforce organization policy — not legal compliance by themselves.",
  "SSO, SCIM, and RBAC configuration must be reviewed by your security team before production use.",
  "AI governance allowlists and budgets reduce risk but do not guarantee model output safety.",
  "BYOM routing sends requests to customer-managed endpoints; data residency is customer responsibility.",
  "Audit logs support investigation workflows; retention and legal hold rules vary by jurisdiction.",
  "Deployment profiles describe topology options; actual HA and air-gap certification requires infra review.",
  "Human approval is required before publishing investigations, reports, or marketplace artifacts.",
] as const;

export const ENTERPRISE_REVIEW_REQUIREMENTS = [
  "Verify SSO issuer, redirect URIs, and SCIM role mappings in staging.",
  "Confirm policy rules cover all licensed domain packs and resource types.",
  "Validate seat counts and pack entitlements match contract.",
  "Review AI model allowlist and daily cost caps.",
  "Ensure secret connector scopes follow least privilege.",
  "Test approval workflow transitions for each publish path.",
] as const;

export const ENTERPRISE_DEFAULT_ROLES = [
  "owner",
  "admin",
  "analyst",
  "viewer",
  "legal",
  "security",
] as const;

export const ENTERPRISE_FEATURE_FLAGS = [
  "ENTERPRISE_SSO",
  "ENTERPRISE_SCIM",
  "ENTERPRISE_POLICY_RBAC",
  "ENTERPRISE_APPROVALS",
  "ENTERPRISE_AI_GOVERNANCE",
  "ENTERPRISE_BYOM",
  "ENTERPRISE_AUDIT_CENTER",
  "ENTERPRISE_DEPLOYMENT_PROFILES",
] as const;

export interface EnterpriseDomainDefinition {
  id: typeof ENTERPRISE_DOMAIN_ID;
  version: string;
  name: string;
  description: string;
  defaultRoles: readonly string[];
  defaultDisclaimers: readonly string[];
  defaultReviewRequirements: readonly string[];
  featureFlags: readonly string[];
}

export const ENTERPRISE_DOMAIN: EnterpriseDomainDefinition = {
  id: ENTERPRISE_DOMAIN_ID,
  version: ENTERPRISE_DOMAIN_VERSION,
  name: "Cobra Enterprise Platform",
  description:
    "Organization structure, SSO/SCIM, policy RBAC, approvals, AI governance, BYOM, licensing, and deployment profiles for regulated teams.",
  defaultRoles: ENTERPRISE_DEFAULT_ROLES,
  defaultDisclaimers: ENTERPRISE_DISCLAIMERS,
  defaultReviewRequirements: ENTERPRISE_REVIEW_REQUIREMENTS,
  featureFlags: ENTERPRISE_FEATURE_FLAGS,
};
