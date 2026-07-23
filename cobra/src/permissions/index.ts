import type { Acl, AuthContext, Visibility } from "../types.js";

export class PermissionError extends Error {
  constructor(message = "Forbidden") {
    super(message);
    this.name = "PermissionError";
  }
}

/** Deny-by-default ACL check. No cross-project leakage. */
export function canRead(ctx: AuthContext, acl: Acl): boolean {
  if (acl.orgId !== ctx.orgId) return false;
  if (ctx.isOrgAdmin && (acl.visibility === "organization" || acl.visibility === "public")) {
    return true;
  }
  if (acl.allowUserIds?.includes(ctx.userId)) return true;
  if (acl.ownerUserId && acl.ownerUserId === ctx.userId) return true;

  switch (acl.visibility as Visibility) {
    case "public":
      return true;
    case "organization":
      return true;
    case "project":
      if (!acl.projectId) return false;
      return ctx.projectIds.includes(acl.projectId);
    case "private":
      return acl.ownerUserId === ctx.userId;
    default:
      return false;
  }
}

export function canWrite(ctx: AuthContext, acl: Acl): boolean {
  if (acl.orgId !== ctx.orgId) return false;
  if (acl.ownerUserId === ctx.userId) return true;
  if (ctx.isOrgAdmin) return true;
  if (acl.visibility === "project" && acl.projectId && ctx.projectIds.includes(acl.projectId)) {
    return true;
  }
  return false;
}

export function assertReadable(ctx: AuthContext, acl: Acl): void {
  if (!canRead(ctx, acl)) throw new PermissionError("Read denied");
}

export function assertWritable(ctx: AuthContext, acl: Acl): void {
  if (!canWrite(ctx, acl)) throw new PermissionError("Write denied");
}

export function filterReadable<T extends { permissions: Acl }>(ctx: AuthContext, rows: T[]): T[] {
  return rows.filter((r) => canRead(ctx, r.permissions));
}

export function projectScopedOrThrow(ctx: AuthContext, projectId?: string | null): void {
  if (!projectId) return;
  if (!ctx.projectIds.includes(projectId) && !ctx.isOrgAdmin) {
    throw new PermissionError("Project access denied");
  }
}
