import type { CkeStore } from "../db/store.js";
import { filterReadable, projectScopedOrThrow } from "../permissions/index.js";
import type { AuthContext, CitationRef, TimelineEvent, Visibility } from "../types.js";
import { clampConfidence, newId, now } from "../util.js";

export class TimelineEngine {
  constructor(private store: CkeStore) {}

  add(
    ctx: AuthContext,
    input: {
      title: string;
      eventType: string;
      occurredAt: number;
      projectId?: string | null;
      entityId?: string | null;
      body?: string;
      citations?: CitationRef[];
      confidence?: number;
      visibility?: Visibility;
    },
  ): TimelineEvent {
    projectScopedOrThrow(ctx, input.projectId);
    const ev: TimelineEvent = {
      id: newId("tl"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      entityId: input.entityId ?? null,
      eventType: input.eventType,
      title: input.title,
      body: input.body ?? null,
      occurredAt: input.occurredAt,
      citations: input.citations ?? [],
      confidence: clampConfidence(input.confidence ?? 0.7),
      permissions: {
        orgId: ctx.orgId,
        projectId: input.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: input.visibility ?? "project",
      },
      createdAt: now(),
    };
    this.store.timeline.set(ev.id, ev);
    return ev;
  }

  list(
    ctx: AuthContext,
    opts: {
      projectId?: string | null;
      entityId?: string | null;
      from?: number;
      to?: number;
    } = {},
  ): TimelineEvent[] {
    const rows = [...this.store.timeline.values()].filter((e) => {
      if (e.orgId !== ctx.orgId) return false;
      if (opts.projectId != null && e.projectId !== opts.projectId) return false;
      if (opts.entityId != null && e.entityId !== opts.entityId) return false;
      if (opts.from != null && e.occurredAt < opts.from) return false;
      if (opts.to != null && e.occurredAt > opts.to) return false;
      return true;
    });
    return filterReadable(ctx, rows).sort((a, b) => a.occurredAt - b.occurredAt);
  }
}
