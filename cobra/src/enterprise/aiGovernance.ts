import type { AiGovernancePolicy, CostBudgetUsage, TokenBudgetUsage } from "./types.js";

export interface GovernanceCheckResult {
  allowed: boolean;
  reason: string;
}

/** Evaluate model against allowlist/blocklist policy. */
export function evaluateModelAllowlist(
  policy: AiGovernancePolicy,
  model: string,
): GovernanceCheckResult {
  const normalized = model.trim().toLowerCase();

  if (policy.blockedModels.some((m) => m.toLowerCase() === normalized)) {
    return { allowed: false, reason: `Model '${model}' is blocked by governance policy` };
  }

  if (policy.allowedModels.length === 0) {
    return { allowed: true, reason: "No allowlist configured; blocklist passed" };
  }

  const allowed = policy.allowedModels.some(
    (m) => m.toLowerCase() === normalized || normalized.startsWith(`${m.toLowerCase()}:`),
  );

  if (!allowed) {
    return { allowed: false, reason: `Model '${model}' is not on the allowlist` };
  }

  return { allowed: true, reason: `Model '${model}' is allowlisted` };
}

/** Check per-request token budget. */
export function checkTokenBudget(
  policy: AiGovernancePolicy,
  usage: TokenBudgetUsage,
): GovernanceCheckResult {
  const limit = policy.maxTokensPerRequest;
  if (usage.tokensUsed > limit) {
    return {
      allowed: false,
      reason: `Token usage ${usage.tokensUsed} exceeds per-request limit ${limit}`,
    };
  }
  if (usage.tokensLimit > 0 && usage.tokensUsed > usage.tokensLimit) {
    return {
      allowed: false,
      reason: `Token usage ${usage.tokensUsed} exceeds request limit ${usage.tokensLimit}`,
    };
  }
  return { allowed: true, reason: "Token budget within limits" };
}

/** Check daily cost budget. */
export function checkCostBudget(
  policy: AiGovernancePolicy,
  usage: CostBudgetUsage,
): GovernanceCheckResult {
  const limit = policy.maxCostUsdPerDay;
  if (usage.costUsd > limit) {
    return {
      allowed: false,
      reason: `Daily cost $${usage.costUsd.toFixed(4)} exceeds limit $${limit}`,
    };
  }
  if (usage.costLimitUsd > 0 && usage.costUsd > usage.costLimitUsd) {
    return {
      allowed: false,
      reason: `Cost $${usage.costUsd.toFixed(4)} exceeds configured limit $${usage.costLimitUsd}`,
    };
  }
  return { allowed: true, reason: "Cost budget within limits" };
}

/** Determine if record exceeds retention and may be purged. */
export function evaluateRetention(
  policy: AiGovernancePolicy,
  recordCreatedAt: string,
  now = new Date(),
): GovernanceCheckResult {
  const created = new Date(recordCreatedAt);
  if (Number.isNaN(created.getTime())) {
    return { allowed: false, reason: "Invalid recordCreatedAt timestamp" };
  }

  const ageDays = (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
  if (ageDays > policy.retentionDays) {
    return {
      allowed: true,
      reason: `Record age ${Math.floor(ageDays)}d exceeds retention ${policy.retentionDays}d`,
    };
  }

  return {
    allowed: false,
    reason: `Record within retention window (${policy.retentionDays}d)`,
  };
}
