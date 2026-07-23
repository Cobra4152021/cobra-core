import type {
  EnterpriseResourceType,
  OrgPolicy,
  PolicyEvaluationInput,
  PolicyEvaluationResult,
  PolicyRule,
} from "./types.js";

const RESOURCE_ACTIONS: Record<EnterpriseResourceType, readonly string[]> = {
  report: ["read", "write", "publish", "export"],
  sdk: ["read", "install", "execute", "publish"],
  studio: ["read", "write", "share", "admin"],
  marketplace: ["browse", "install", "publish"],
  domain_pack: ["read", "enable", "configure"],
  investigation: ["read", "write", "close", "publish"],
};

const ROLE_DEFAULTS: Record<string, readonly EnterpriseResourceType[]> = {
  owner: ["report", "sdk", "studio", "marketplace", "domain_pack", "investigation"],
  admin: ["report", "sdk", "studio", "marketplace", "domain_pack", "investigation"],
  analyst: ["report", "studio", "investigation"],
  viewer: ["report", "studio", "investigation"],
};

function matchesResourcePattern(pattern: string | undefined, resourceId: string): boolean {
  if (!pattern || pattern === "*") return true;
  const re = new RegExp(`^${pattern.replace(/\*/g, ".*")}$`);
  return re.test(resourceId);
}

function ruleMatches(rule: PolicyRule, input: PolicyEvaluationInput): boolean {
  if (rule.resourceType !== "*" && rule.resourceType !== input.resourceType) return false;
  if (!rule.roles.includes(input.actorRole) && !rule.roles.includes("*")) return false;
  if (rule.action !== "*" && rule.action !== input.action) return false;
  if (!matchesResourcePattern(rule.resourceIdPattern, input.resourceId)) return false;
  return true;
}

/** Enterprise policy engine — deny-by-default with explicit allow rules. */
export class PolicyEngine {
  constructor(private policies: OrgPolicy[] = []) {}

  setPolicies(policies: OrgPolicy[]): void {
    this.policies = policies;
  }

  evaluatePolicy(input: PolicyEvaluationInput): PolicyEvaluationResult {
    const allowedActions = RESOURCE_ACTIONS[input.resourceType];
    if (!allowedActions.includes(input.action)) {
      return {
        decision: "deny",
        reason: `Action '${input.action}' is not valid for resource type '${input.resourceType}'`,
      };
    }

    const orgPolicies = this.policies.filter((p) => p.orgId === input.orgId && p.enabled);
    let explicitDeny: PolicyEvaluationResult | null = null;
    let explicitAllow: PolicyEvaluationResult | null = null;

    for (const policy of orgPolicies) {
      for (const rule of policy.rules) {
        if (!ruleMatches(rule, input)) continue;
        const result: PolicyEvaluationResult = {
          decision: rule.effect,
          reason: `${rule.effect} by policy '${policy.name}' rule '${rule.id}'`,
          matchedRuleId: rule.id,
        };
        if (rule.effect === "deny") explicitDeny = result;
        if (rule.effect === "allow") explicitAllow = result;
      }
    }

    if (explicitDeny) return explicitDeny;
    if (explicitAllow) return explicitAllow;

    const roleResources = ROLE_DEFAULTS[input.actorRole];
    if (roleResources?.includes(input.resourceType)) {
      if (input.action === "publish" && !["owner", "admin"].includes(input.actorRole)) {
        return { decision: "deny", reason: "Publish requires owner or admin role" };
      }
      if (input.resourceType === "marketplace" && input.action === "publish" && input.actorRole !== "owner") {
        return { decision: "deny", reason: "Marketplace publish requires owner role" };
      }
      if (input.domainPack && input.resourceType === "domain_pack") {
        return {
          decision: "allow",
          reason: `Default allow for role '${input.actorRole}' on domain pack '${input.domainPack}'`,
        };
      }
      return {
        decision: "allow",
        reason: `Default allow for role '${input.actorRole}' on ${input.resourceType}`,
      };
    }

    return {
      decision: "deny",
      reason: `Role '${input.actorRole}' has no access to ${input.resourceType}:${input.resourceId}`,
    };
  }
}

export { RESOURCE_ACTIONS, ROLE_DEFAULTS };
