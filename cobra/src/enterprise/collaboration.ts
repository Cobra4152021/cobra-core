import type { CollaborationEvent, EnterpriseResourceType } from "./types.js";

export interface Assignment {
  resourceType: EnterpriseResourceType;
  resourceId: string;
  assigneeUserId: string;
  assignedByUserId: string;
  assignedAt: string;
}

/** Sort events newest-first and optionally filter by resource. */
export function buildActivityFeed(
  events: CollaborationEvent[],
  filter?: { resourceType?: EnterpriseResourceType; resourceId?: string },
): CollaborationEvent[] {
  let filtered = events;
  if (filter?.resourceType) {
    filtered = filtered.filter((e) => e.resourceType === filter.resourceType);
  }
  if (filter?.resourceId) {
    filtered = filtered.filter((e) => e.resourceId === filter.resourceId);
  }
  return [...filtered].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

/** Normalize @mention tokens to lowercase user ids without @ prefix. */
export function normalizeMention(raw: string): string {
  return raw.trim().replace(/^@+/, "").toLowerCase();
}

/** Extract mention user ids from message text (@userId tokens). */
export function extractMentions(message: string): string[] {
  const matches = message.match(/@([a-zA-Z0-9._-]+)/g) ?? [];
  return [...new Set(matches.map(normalizeMention))];
}

/** Create assignment record (pure helper). */
export function createAssignment(input: Omit<Assignment, "assignedAt"> & { assignedAt?: string }): Assignment {
  return {
    ...input,
    assignedAt: input.assignedAt ?? new Date(0).toISOString(),
  };
}

/** Resolve current assignee from assignment events (latest wins). */
export function resolveAssignee(events: CollaborationEvent[]): string | null {
  const assignments = events
    .filter((e) => e.type === "assignment" && e.assigneeUserId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return assignments[0]?.assigneeUserId ?? null;
}
