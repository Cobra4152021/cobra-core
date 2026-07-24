import type { SentinelTriageDomain, TriageResult } from "./types.js";

const RULES: Array<{ domain: SentinelTriageDomain; pattern: RegExp; cause: string; weight: number }> = [
  { domain: "csrf", pattern: /csrf|x-hidden-grid-auth|missing required header/i, cause: "Missing or invalid CSRF header", weight: 0.92 },
  { domain: "rbac", pattern: /forbidden|route policy|permission|rbac|not configured/i, cause: "RBAC / route policy denial", weight: 0.9 },
  { domain: "idor", pattern: /not found|cross[- ]?org|idor/i, cause: "Possible IDOR or missing org-scoped row", weight: 0.75 },
  { domain: "database", pattern: /d1|sqlite|database|sql/i, cause: "D1 / SQL failure", weight: 0.88 },
  { domain: "queue", pattern: /queue|consumer|message batch/i, cause: "Queue processing failure", weight: 0.86 },
  { domain: "storage", pattern: /\br2\b|storage|bucket|object not/i, cause: "R2 / storage failure", weight: 0.86 },
  { domain: "marketplace", pattern: /marketplace|pack install|signing/i, cause: "Marketplace / pack install path", weight: 0.84 },
  { domain: "government", pattern: /government/i, cause: "Government domain path", weight: 0.8 },
  { domain: "labor", pattern: /\blabor\b|grievance|union/i, cause: "Labor domain path", weight: 0.8 },
  { domain: "research", pattern: /research|templateid required/i, cause: "Research domain path", weight: 0.8 },
  { domain: "enterprise", pattern: /enterprise|scim|sso|byom/i, cause: "Enterprise platform path", weight: 0.8 },
  { domain: "studio", pattern: /studio|dashboard|timeline/i, cause: "Intelligence Studio path", weight: 0.78 },
  { domain: "sdk", pattern: /\bsdk\b|manifest|plugin/i, cause: "SDK / pack manifest path", weight: 0.78 },
  { domain: "investigator", pattern: /investigator|investigation/i, cause: "Investigator pipeline path", weight: 0.76 },
  { domain: "network", pattern: /network|fetch failed|timeout|econn/i, cause: "Network / timeout", weight: 0.82 },
  { domain: "ui", pattern: /react|render|hydration|typeerror|referenceerror/i, cause: "Client UI exception", weight: 0.7 },
];

/** Rule-based triage (alpha1). Never auto-closes. */
export function triageEvent(input: {
  message?: string | null;
  stack?: string | null;
  route?: string | null;
  category?: string | null;
}): TriageResult {
  const hay = [input.message, input.stack, input.route, input.category].filter(Boolean).join("\n");
  let best: (typeof RULES)[number] | null = null;
  for (const rule of RULES) {
    if (rule.pattern.test(hay) && (!best || rule.weight > best.weight)) best = rule;
  }
  if (!best) {
    return {
      domain: "unknown",
      confidence: 0.35,
      likelyCauses: ["Insufficient signal for automated classification"],
      autoClose: false,
    };
  }
  return {
    domain: best.domain,
    confidence: best.weight,
    likelyCauses: [best.cause, "Confirm with request/correlation IDs before closing"],
    autoClose: false,
  };
}
