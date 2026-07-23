import type { AuditCategory, AuditEvent, AuditFilter } from "./types.js";

const ACTION_CATEGORY_MAP: Record<string, AuditCategory> = {
  login: "authentication",
  logout: "authentication",
  sso_login: "authentication",
  token_refresh: "authentication",
  permission_denied: "authorization",
  policy_evaluated: "authorization",
  role_assigned: "authorization",
  record_read: "data_access",
  record_export: "data_access",
  record_delete: "data_access",
  config_update: "configuration",
  sso_config_change: "configuration",
  scim_sync: "configuration",
  approval_transition: "governance",
  model_blocked: "governance",
  budget_exceeded: "governance",
  deploy: "deployment",
  profile_change: "deployment",
};

/** Categorize audit action string into facet bucket. */
export function categorizeAuditAction(action: string): AuditCategory {
  const normalized = action.toLowerCase().replace(/[\s-]+/g, "_");
  if (ACTION_CATEGORY_MAP[normalized]) return ACTION_CATEGORY_MAP[normalized];

  if (/login|auth|sso|session/.test(normalized)) return "authentication";
  if (/deny|permission|role|policy/.test(normalized)) return "authorization";
  if (/read|export|download|query|delete|write/.test(normalized)) return "data_access";
  if (/config|setting|scim|sso/.test(normalized)) return "configuration";
  if (/approval|governance|model|budget|retention/.test(normalized)) return "governance";
  if (/deploy|profile|node|cluster/.test(normalized)) return "deployment";

  return "unknown";
}

export interface AuditFacets {
  categories: Record<AuditCategory, number>;
  resourceTypes: Record<string, number>;
  actors: Record<string, number>;
}

/** Filter audit events by org, category, actor, resource, query, and time range. */
export function filterAuditEvents(events: AuditEvent[], filter: AuditFilter = {}): AuditEvent[] {
  return events.filter((event) => {
    if (filter.orgId && event.orgId !== filter.orgId) return false;
    if (filter.actorUserId && event.actorUserId !== filter.actorUserId) return false;
    if (filter.resourceType && event.resourceType !== filter.resourceType) return false;

    if (filter.category && categorizeAuditAction(event.action) !== filter.category) return false;

    if (filter.from && event.timestamp < filter.from) return false;
    if (filter.to && event.timestamp > filter.to) return false;

    if (filter.query) {
      const q = filter.query.toLowerCase();
      const haystack = [
        event.action,
        event.resourceType,
        event.resourceId,
        event.actorUserId,
        ...Object.values(event.metadata ?? {}),
      ]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(q)) return false;
    }

    return true;
  });
}

/** Build searchable facet counts from audit events. */
export function buildAuditFacets(events: AuditEvent[]): AuditFacets {
  const categories: Record<AuditCategory, number> = {
    authentication: 0,
    authorization: 0,
    data_access: 0,
    configuration: 0,
    governance: 0,
    deployment: 0,
    unknown: 0,
  };
  const resourceTypes: Record<string, number> = {};
  const actors: Record<string, number> = {};

  for (const event of events) {
    const cat = categorizeAuditAction(event.action);
    categories[cat] += 1;
    resourceTypes[event.resourceType] = (resourceTypes[event.resourceType] ?? 0) + 1;
    actors[event.actorUserId] = (actors[event.actorUserId] ?? 0) + 1;
  }

  return { categories, resourceTypes, actors };
}
