import type { AiGovernancePolicy, ByomEndpointConfig, ByomRouteRequest, ByomRouteResult } from "./types.js";

export interface ByomValidationIssue {
  field: string;
  message: string;
}

/** Normalize BYOM endpoint config. */
export function normalizeByomEndpoint(raw: ByomEndpointConfig): ByomEndpointConfig {
  return {
    provider: raw.provider,
    baseUrl: raw.baseUrl.replace(/\/$/, ""),
    apiVersion: raw.apiVersion?.trim() || undefined,
    modelAlias: raw.modelAlias ? { ...raw.modelAlias } : undefined,
  };
}

/** Validate OpenAI-compatible endpoint shape. */
export function validateOpenAiCompatible(config: ByomEndpointConfig): ByomValidationIssue[] {
  const issues: ByomValidationIssue[] = [];
  const normalized = normalizeByomEndpoint(config);

  if (!/^https?:\/\//i.test(normalized.baseUrl)) {
    issues.push({ field: "baseUrl", message: "baseUrl must be http(s)" });
  }

  if (normalized.provider === "openai_compatible" && !normalized.baseUrl.includes("/v1")) {
    if (!normalized.apiVersion) {
      issues.push({
        field: "apiVersion",
        message: "OpenAI-compatible endpoints should specify apiVersion or include /v1 in baseUrl",
      });
    }
  }

  return issues;
}

/** Route model request through governance policy and endpoint aliases. */
export function routeModel(
  policy: AiGovernancePolicy,
  endpoint: ByomEndpointConfig,
  request: ByomRouteRequest,
): ByomRouteResult {
  const normalized = normalizeByomEndpoint(endpoint);
  const model = request.model.trim();

  const blocked = policy.blockedModels.some((m) => m.toLowerCase() === model.toLowerCase());
  if (blocked) {
    return { routed: false, model, reason: `Model '${model}' blocked by governance policy` };
  }

  if (policy.allowedModels.length > 0) {
    const allowed = policy.allowedModels.some((m) => m.toLowerCase() === model.toLowerCase());
    if (!allowed) {
      return { routed: false, model, reason: `Model '${model}' not on allowlist` };
    }
  }

  const alias = normalized.modelAlias?.[model] ?? model;
  const version = normalized.apiVersion ?? "v1";
  const target = `${normalized.baseUrl}/${version}/chat/completions`;

  return {
    routed: true,
    model: alias,
    endpoint: target,
    reason: `Routed to ${normalized.provider} endpoint`,
  };
}
