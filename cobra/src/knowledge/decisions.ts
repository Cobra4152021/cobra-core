import type { CkeStore } from "../db/store.js";
import { filterReadable, projectScopedOrThrow } from "../permissions/index.js";
import type { AuthContext, CitationRef, Decision, DecisionStatus, Visibility } from "../types.js";
import { newId, now } from "../util.js";

export class DecisionEngine {
  constructor(private store: CkeStore) {}

  record(
    ctx: AuthContext,
    input: {
      title: string;
      status: DecisionStatus;
      reason?: string;
      alternatives?: string[];
      decisionMaker?: string;
      evidence?: string[];
      citations?: CitationRef[];
      projectId?: string | null;
      decidedAt?: number;
      visibility?: Visibility;
    },
  ): Decision {
    projectScopedOrThrow(ctx, input.projectId);
    const ts = now();
    const d: Decision = {
      id: newId("dec"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      title: input.title,
      status: input.status,
      reason: input.reason ?? null,
      alternatives: input.alternatives ?? [],
      decisionMaker: input.decisionMaker ?? ctx.userId,
      evidence: input.evidence ?? [],
      citations: input.citations ?? [],
      decidedAt: input.decidedAt ?? ts,
      permissions: {
        orgId: ctx.orgId,
        projectId: input.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: input.visibility ?? "project",
      },
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.decisions.set(d.id, d);
    return d;
  }

  list(ctx: AuthContext, projectId?: string | null): Decision[] {
    const rows = [...this.store.decisions.values()].filter((d) => {
      if (d.orgId !== ctx.orgId) return false;
      if (projectId != null && d.projectId !== projectId) return false;
      return true;
    });
    return filterReadable(ctx, rows).sort((a, b) => b.decidedAt - a.decidedAt);
  }
}
