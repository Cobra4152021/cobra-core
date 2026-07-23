import type { RoleMappingRule, ScimUserPayload, ScimUserRecord } from "./types.js";

export interface ScimValidationIssue {
  field: string;
  message: string;
}

/** Map membership payload to internal SCIM user record. */
export function mapMembershipToScimUser(
  payload: ScimUserPayload,
  options?: { id?: string; defaultRoles?: string[] },
): ScimUserRecord {
  const emails =
    payload.emails?.map((e) => e.value).filter(Boolean) ??
    (payload.userName.includes("@") ? [payload.userName] : []);

  const given = payload.name?.givenName ?? "";
  const family = payload.name?.familyName ?? "";
  const displayName = [given, family].filter(Boolean).join(" ") || payload.userName;

  return {
    id: options?.id ?? payload.externalId ?? payload.userName,
    userName: payload.userName,
    active: payload.active !== false,
    emails,
    displayName,
    externalId: payload.externalId,
    roles: options?.defaultRoles ?? [],
  };
}

/** Validate SCIM user create payload. */
export function validateScimUserCreate(payload: ScimUserPayload): ScimValidationIssue[] {
  const issues: ScimValidationIssue[] = [];

  if (!payload.userName?.trim()) {
    issues.push({ field: "userName", message: "userName is required" });
  }

  if (payload.emails?.length) {
    for (const email of payload.emails) {
      if (!email.value?.includes("@")) {
        issues.push({ field: "emails", message: `Invalid email: ${email.value ?? ""}` });
      }
    }
  }

  if (payload.active === false && !payload.userName) {
    issues.push({ field: "active", message: "Cannot deactivate user without userName" });
  }

  return issues;
}

/** Apply group-to-role mapping rules to a SCIM user record. */
export function applyRoleMapping(
  user: ScimUserRecord,
  groups: string[],
  rules: RoleMappingRule[],
): ScimUserRecord {
  const roles = new Set(user.roles);

  for (const group of groups) {
    for (const rule of rules) {
      const pattern = rule.groupPattern.replace(/\*/g, ".*");
      const re = new RegExp(`^${pattern}$`, "i");
      if (re.test(group)) {
        roles.add(rule.role);
      }
    }
  }

  return { ...user, roles: [...roles] };
}
