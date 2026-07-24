/** Correlation / bug / replay ID helpers for Sentinel. */

export function newOpaqueId(prefix: string, randomHex: string): string {
  return `${prefix}_${randomHex.replace(/[^a-f0-9]/gi, "").slice(0, 24) || "0"}`;
}

export function buildCorrelationId(parts: {
  requestId: string;
  sessionId?: string | null;
  investigationId?: string | null;
}): string {
  const sid = parts.sessionId?.slice(0, 12) || "nosession";
  const inv = parts.investigationId?.slice(0, 12) || "noinv";
  return `corr_${parts.requestId.slice(0, 16)}_${sid}_${inv}`;
}

/** BUG-YYYY-###### sequential display id. */
export function formatBugNumber(year: number, seq: number): string {
  const n = Math.max(1, Math.floor(seq));
  return `BUG-${year}-${String(n).padStart(6, "0")}`;
}

export function parseBugNumber(bugId: string): { year: number; seq: number } | null {
  const m = /^BUG-(\d{4})-(\d{6})$/.exec(bugId.trim());
  if (!m) return null;
  return { year: Number(m[1]), seq: Number(m[2]) };
}
