/** KC-012 — Cobra Sentinel types */

export type SentinelSeverity = "critical" | "high" | "medium" | "low";

export type SentinelBugStatus = "new" | "investigating" | "resolved" | "closed";

export type SentinelFeedbackCategory =
  | "bug"
  | "feature_request"
  | "performance"
  | "security"
  | "ui"
  | "documentation"
  | "ai_result"
  | "other";

export type SentinelFeedbackStatus =
  | "new"
  | "acknowledged"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "verified"
  | "closed";

export type SentinelTriageDomain =
  | "rbac"
  | "csrf"
  | "idor"
  | "database"
  | "queue"
  | "storage"
  | "ui"
  | "sdk"
  | "marketplace"
  | "government"
  | "labor"
  | "research"
  | "enterprise"
  | "studio"
  | "investigator"
  | "network"
  | "unknown";

export interface CorrelationContext {
  requestId: string;
  sessionId: string | null;
  correlationId: string;
  investigationId: string | null;
}

export interface DiagnosticBundle {
  workerVersion: string | null;
  coreVersion: string;
  browser: string | null;
  os: string | null;
  viewport: string | null;
  route: string | null;
  featureFlags: Record<string, boolean | string>;
  orgId: string | null;
  role: string | null;
  apiEndpoint: string | null;
  requestIds: string[];
  performance: Record<string, number | null>;
  stack: string | null;
  memoryMb: number | null;
}

export interface TriageResult {
  domain: SentinelTriageDomain;
  confidence: number;
  likelyCauses: string[];
  autoClose: false;
}

export interface ReplayToken {
  replayId: string;
  featureFlags: Record<string, boolean | string>;
  browser: string | null;
  route: string | null;
  apiRequestIds: string[];
  workerVersion: string | null;
  correlationId: string;
  payloadHashes: string[];
}
