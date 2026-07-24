export interface RetentionInput {
  retentionDays: number;
  createdAt: string;
  now?: Date;
}

export interface RetentionResult {
  expired: boolean;
  ageDays: number;
  reason: string;
}

export interface LegalHold {
  resourceId: string;
  active: boolean;
  reason?: string;
}

export interface SoftDeleteRecord {
  id: string;
  deletedAt: string | null;
  deletedBy?: string;
}

/** Check if record exceeds retention period. */
export function retentionCheck(input: RetentionInput): RetentionResult {
  const now = input.now ?? new Date();
  const created = new Date(input.createdAt);
  if (Number.isNaN(created.getTime())) {
    return { expired: false, ageDays: 0, reason: "Invalid createdAt" };
  }

  const ageDays = (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
  const expired = ageDays > input.retentionDays;

  return {
    expired,
    ageDays: Math.floor(ageDays),
    reason: expired
      ? `Record expired (${Math.floor(ageDays)}d > ${input.retentionDays}d)`
      : `Within retention (${Math.floor(ageDays)}d <= ${input.retentionDays}d)`,
  };
}

/** Legal hold blocks hard delete when active for resource. */
export function legalHoldBlocksDelete(holds: LegalHold[], resourceId: string): boolean {
  return holds.some((h) => h.resourceId === resourceId && h.active);
}

/** Apply soft-delete marker to record metadata. */
export function softDeleteMarker(
  record: SoftDeleteRecord,
  actorUserId: string,
  deletedAt = new Date().toISOString(),
): SoftDeleteRecord {
  return {
    ...record,
    deletedAt,
    deletedBy: actorUserId,
  };
}

/** True when record is soft-deleted. */
export function isSoftDeleted(record: SoftDeleteRecord): boolean {
  return record.deletedAt != null;
}
