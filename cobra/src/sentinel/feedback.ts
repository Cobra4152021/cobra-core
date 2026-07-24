import type { SentinelFeedbackStatus } from "./types.js";

const ORDER: SentinelFeedbackStatus[] = [
  "new",
  "acknowledged",
  "assigned",
  "in_progress",
  "resolved",
  "verified",
  "closed",
];

export function canTransitionFeedback(
  from: SentinelFeedbackStatus,
  to: SentinelFeedbackStatus,
): boolean {
  if (from === to) return true;
  const a = ORDER.indexOf(from);
  const b = ORDER.indexOf(to);
  if (a < 0 || b < 0) return false;
  // Allow forward one step, or jump to closed from resolved/verified, or reopen to acknowledged
  if (b === a + 1) return true;
  if (to === "closed" && (from === "resolved" || from === "verified")) return true;
  if (to === "acknowledged" && from === "new") return true;
  if (from === "closed" && to === "new") return false;
  return false;
}

export function nextFeedbackStatuses(from: SentinelFeedbackStatus): SentinelFeedbackStatus[] {
  return ORDER.filter((s) => s !== from && canTransitionFeedback(from, s));
}
