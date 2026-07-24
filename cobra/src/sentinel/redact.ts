/** Automatic redaction — never keep secrets or evidence bodies by default. */

const SENSITIVE_KEY =
  /pass(word)?|token|secret|cookie|authorization|auth|api[_-]?key|session|evidence|prompt|file[_-]?bytes|upload/i;

const BEARER = /Bearer\s+[A-Za-z0-9._\-+=\/]+/gi;
const JWT = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g;
const COOKIE_PAIR = /(hidden_grid_session|session|token)=([^;\s]+)/gi;
const PASSWORD_PAIR = /(password|passwd|secret|api[_-]?key)\s*[:=]\s*([^\s,;]+)/gi;
const EVIDENCE_PAIR = /(evidence(_(payload|contents|bytes))?|file[_-]?bytes|upload)\s*[:=]\s*([^\s,;]+)/gi;

export function redactString(input: string): string {
  let out = String(input ?? "");
  out = out.replace(BEARER, "Bearer [REDACTED]");
  out = out.replace(JWT, "[REDACTED_JWT]");
  out = out.replace(COOKIE_PAIR, "$1=[REDACTED]");
  out = out.replace(PASSWORD_PAIR, "$1=[REDACTED]");
  out = out.replace(EVIDENCE_PAIR, "$1=[REDACTED]");
  return out;
}

export function redactValue(value: unknown, keyHint = ""): unknown {
  if (value == null) return value;
  if (SENSITIVE_KEY.test(keyHint)) return "[REDACTED]";
  if (typeof value === "string") return redactString(value);
  if (typeof value === "number" || typeof value === "boolean") return value;
  if (Array.isArray(value)) return value.map((v, i) => redactValue(v, `${keyHint}[${i}]`));
  if (typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = redactValue(v, k);
    }
    return out;
  }
  return String(value);
}

/** Hash-only payload fingerprint (no content). */
export async function hashPayload(payload: string): Promise<string> {
  const data = new TextEncoder().encode(payload);
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const dig = await crypto.subtle.digest("SHA-256", data);
    return [...new Uint8Array(dig)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  // Node fallback for tests
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(payload, "utf8").digest("hex");
}
