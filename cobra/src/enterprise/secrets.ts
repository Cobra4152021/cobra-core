import type { SecretConnectorMeta } from "./types.js";

const SECRET_PATTERNS = [
  /(?:api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['"]?([a-zA-Z0-9_\-./+=]{8,})/gi,
  /\b(sk-[a-zA-Z0-9]{20,})\b/g,
  /\b(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)\b/g,
];

/** Redact likely secrets from log text. */
export function redactSecret(text: string, replacement = "[REDACTED]"): string {
  let out = text;
  for (const pattern of SECRET_PATTERNS) {
    out = out.replace(pattern, replacement);
  }
  return out;
}

export interface ScopeValidationResult {
  valid: boolean;
  missingScopes: string[];
}

/** Validate connector has required scopes for an action. */
export function validateConnectorScope(
  connector: SecretConnectorMeta,
  requiredScopes: string[],
): ScopeValidationResult {
  const granted = new Set(connector.scopes.map((s) => s.toLowerCase()));
  const missing = requiredScopes.filter((s) => !granted.has(s.toLowerCase()));
  return { valid: missing.length === 0, missingScopes: missing };
}

/** Check if secret rotation is due based on lastRotatedAt and interval. */
export function rotationDue(
  connector: SecretConnectorMeta,
  now = new Date(),
): { due: boolean; daysSinceRotation: number | null; reason: string } {
  if (!connector.lastRotatedAt) {
    return { due: true, daysSinceRotation: null, reason: "Never rotated" };
  }

  const last = new Date(connector.lastRotatedAt);
  if (Number.isNaN(last.getTime())) {
    return { due: true, daysSinceRotation: null, reason: "Invalid lastRotatedAt" };
  }

  const days = (now.getTime() - last.getTime()) / (1000 * 60 * 60 * 24);
  const due = days >= connector.rotationIntervalDays;

  return {
    due,
    daysSinceRotation: Math.floor(days),
    reason: due
      ? `Rotation overdue (${Math.floor(days)}d >= ${connector.rotationIntervalDays}d)`
      : `Rotation not due (${Math.floor(days)}d < ${connector.rotationIntervalDays}d)`,
  };
}
