/** KC-010 Enterprise Platform — shared types (pure TypeScript). */

export type SsoProviderType =
  | "oidc"
  | "saml"
  | "azure_ad"
  | "google_workspace"
  | "okta"
  | "auth0"
  | "keycloak";

export type ScimOp = "create" | "update" | "patch" | "delete" | "replace";

export type ApprovalState = "draft" | "review" | "approved" | "published" | "archived";

export type ApprovalAction =
  | "submit_for_review"
  | "request_changes"
  | "approve"
  | "publish"
  | "archive"
  | "reopen";

export type PolicyDecision = "allow" | "deny";

export type EnterpriseResourceType =
  | "report"
  | "sdk"
  | "studio"
  | "marketplace"
  | "domain_pack"
  | "investigation";

export type DeploymentProfileId =
  | "cloud"
  | "hybrid"
  | "air_gapped"
  | "on_premises"
  | "single_node"
  | "ha";

export type ByomProvider = "openai_compatible" | "azure_openai" | "bedrock" | "vertex" | "custom";

export interface OrgUnitBase {
  id: string;
  name: string;
  parentId?: string | null;
}

export interface Department extends OrgUnitBase {
  kind: "department";
  headUserId?: string;
}

export interface BusinessUnit extends OrgUnitBase {
  kind: "business_unit";
  costCenter?: string;
}

export interface NestedTeam extends OrgUnitBase {
  kind: "team";
  memberUserIds: string[];
}

export type OrgUnit = Department | BusinessUnit | NestedTeam;

export interface OrgPolicy {
  id: string;
  orgId: string;
  name: string;
  rules: PolicyRule[];
  enabled: boolean;
}

export interface PolicyRule {
  id: string;
  action: string;
  resourceType: EnterpriseResourceType | "*";
  roles: string[];
  effect: PolicyDecision;
  resourceIdPattern?: string;
}

export interface SsoConfig {
  provider: SsoProviderType;
  issuer: string;
  clientId: string;
  redirectUri: string;
  scopes?: string[];
  metadataUrl?: string;
}

export interface ScimUserPayload {
  userName: string;
  active?: boolean;
  emails?: Array<{ value: string; primary?: boolean }>;
  name?: { givenName?: string; familyName?: string };
  externalId?: string;
  groups?: string[];
}

export interface ScimUserRecord {
  id: string;
  userName: string;
  active: boolean;
  emails: string[];
  displayName: string;
  externalId?: string;
  roles: string[];
}

export interface RoleMappingRule {
  groupPattern: string;
  role: string;
}

export interface PolicyEvaluationInput {
  actorRole: string;
  action: string;
  resourceType: EnterpriseResourceType;
  resourceId: string;
  domainPack?: string;
  orgId: string;
}

export interface PolicyEvaluationResult {
  decision: PolicyDecision;
  reason: string;
  matchedRuleId?: string;
}

export interface ApprovalTransitionResult {
  ok: boolean;
  nextState?: ApprovalState;
  error?: string;
}

export interface ApprovalChainStep {
  role: string;
  order: number;
  required: boolean;
}

export interface CollaborationEvent {
  id: string;
  orgId: string;
  actorUserId: string;
  type: "comment" | "mention" | "assignment" | "status_change" | "approval";
  resourceType: EnterpriseResourceType;
  resourceId: string;
  message?: string;
  mentionUserIds?: string[];
  assigneeUserId?: string;
  createdAt: string;
}

export interface AiGovernancePolicy {
  orgId: string;
  allowedModels: string[];
  blockedModels: string[];
  maxTokensPerRequest: number;
  maxCostUsdPerDay: number;
  retentionDays: number;
  requireHumanReview: boolean;
}

export interface TokenBudgetUsage {
  tokensUsed: number;
  tokensLimit: number;
}

export interface CostBudgetUsage {
  costUsd: number;
  costLimitUsd: number;
}

export interface ByomEndpointConfig {
  provider: ByomProvider;
  baseUrl: string;
  apiVersion?: string;
  modelAlias?: Record<string, string>;
}

export interface ByomRouteRequest {
  model: string;
  orgId: string;
}

export interface ByomRouteResult {
  routed: boolean;
  model: string;
  endpoint?: string;
  reason: string;
}

export interface SecretConnectorMeta {
  id: string;
  orgId: string;
  name: string;
  provider: string;
  scopes: string[];
  lastRotatedAt?: string;
  rotationIntervalDays: number;
}

export interface DeploymentProfile {
  id: DeploymentProfileId;
  name: string;
  description: string;
  requiresInternet: boolean;
  supportsByom: boolean;
  supportsSso: boolean;
  maxNodes: number | null;
}

export interface LicenseEntitlement {
  orgId: string;
  edition: string;
  seatLimit: number;
  seatsUsed: number;
  packs: string[];
  expiresAt?: string;
}

export interface AuditEvent {
  id: string;
  orgId: string;
  actorUserId: string;
  action: string;
  resourceType: string;
  resourceId: string;
  timestamp: string;
  metadata?: Record<string, string>;
}

export type AuditCategory =
  | "authentication"
  | "authorization"
  | "data_access"
  | "configuration"
  | "governance"
  | "deployment"
  | "unknown";

export interface AuditFilter {
  orgId?: string;
  category?: AuditCategory;
  actorUserId?: string;
  resourceType?: string;
  query?: string;
  from?: string;
  to?: string;
}

export interface EnterpriseMetricInput {
  orgId: string;
  activeUsers: number;
  pendingApprovals: number;
  policyDenials: number;
  aiRequests: number;
  auditEvents: number;
}

export interface EnterpriseMetricsSnapshot {
  orgId: string;
  activeUsers: number;
  pendingApprovals: number;
  policyDenials: number;
  aiRequests: number;
  auditEvents: number;
  healthScore: number;
}
