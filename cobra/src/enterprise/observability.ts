import type { EnterpriseMetricInput, EnterpriseMetricsSnapshot } from "./types.js";

/** Aggregate enterprise health metrics into a snapshot with health score. */
export function aggregateEnterpriseMetrics(input: EnterpriseMetricInput): EnterpriseMetricsSnapshot {
  const denialRate = input.aiRequests > 0 ? input.policyDenials / input.aiRequests : 0;
  const approvalBacklog = input.pendingApprovals;
  const auditVolume = input.auditEvents;

  let healthScore = 100;
  healthScore -= Math.min(40, denialRate * 100);
  healthScore -= Math.min(30, approvalBacklog * 2);
  healthScore -= Math.min(10, auditVolume > 10_000 ? 10 : 0);
  healthScore = Math.max(0, Math.round(healthScore));

  return {
    orgId: input.orgId,
    activeUsers: input.activeUsers,
    pendingApprovals: input.pendingApprovals,
    policyDenials: input.policyDenials,
    aiRequests: input.aiRequests,
    auditEvents: input.auditEvents,
    healthScore,
  };
}

/** Merge multiple org metric inputs (rollup). */
export function rollupEnterpriseMetrics(inputs: EnterpriseMetricInput[]): EnterpriseMetricsSnapshot {
  if (inputs.length === 0) {
    return {
      orgId: "rollup",
      activeUsers: 0,
      pendingApprovals: 0,
      policyDenials: 0,
      aiRequests: 0,
      auditEvents: 0,
      healthScore: 100,
    };
  }

  const merged: EnterpriseMetricInput = {
    orgId: "rollup",
    activeUsers: inputs.reduce((s, i) => s + i.activeUsers, 0),
    pendingApprovals: inputs.reduce((s, i) => s + i.pendingApprovals, 0),
    policyDenials: inputs.reduce((s, i) => s + i.policyDenials, 0),
    aiRequests: inputs.reduce((s, i) => s + i.aiRequests, 0),
    auditEvents: inputs.reduce((s, i) => s + i.auditEvents, 0),
  };

  return aggregateEnterpriseMetrics(merged);
}
