import type { CkeStore } from "../db/store.js";
import { assertReadable, assertWritable, filterReadable, projectScopedOrThrow } from "../permissions/index.js";
import type { AuthContext, CitationRef, Memory, MemoryType, Visibility } from "../types.js";
import { clampConfidence, contentHash, newId, now } from "../util.js";

export class MemoryEngine {
  constructor(private store: CkeStore) {}

  create(
    ctx: AuthContext,
    input: {
      type: MemoryType;
      content: string;
      projectId?: string | null;
      source: string;
      confidence?: number;
      citations?: CitationRef[];
      visibility?: Visibility;
      expiresAt?: number | null;
    },
  ): Memory {
    projectScopedOrThrow(ctx, input.projectId);
    const ts = now();
    const mem: Memory = {
      id: newId("mem"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      type: input.type,
      content: input.content,
      confidence: clampConfidence(input.confidence ?? 0.6),
      source: input.source,
      citations: input.citations ?? [],
      permissions: {
        orgId: ctx.orgId,
        projectId: input.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: input.visibility ?? (input.projectId ? "project" : "private"),
      },
      contentHash: contentHash(input.content),
      expiresAt: input.expiresAt ?? null,
      createdAt: ts,
      updatedAt: ts,
    };
    assertWritable(ctx, mem.permissions);
    this.store.memories.set(mem.id, mem);
    return mem;
  }

  get(ctx: AuthContext, id: string): Memory | null {
    const m = this.store.memories.get(id);
    if (!m || m.orgId !== ctx.orgId) return null;
    assertReadable(ctx, m.permissions);
    return m;
  }

  list(
    ctx: AuthContext,
    opts: { projectId?: string | null; type?: MemoryType; includeExpired?: boolean } = {},
  ): Memory[] {
    const t = now();
    const rows = [...this.store.memories.values()].filter((m) => {
      if (m.orgId !== ctx.orgId) return false;
      if (opts.projectId != null && m.projectId !== opts.projectId) return false;
      if (opts.type && m.type !== opts.type) return false;
      if (!opts.includeExpired && m.expiresAt != null && m.expiresAt < t) return false;
      return true;
    });
    return filterReadable(ctx, rows);
  }

  expireTemporary(ctx: AuthContext): number {
    const t = now();
    let n = 0;
    for (const [id, m] of this.store.memories) {
      if (m.orgId !== ctx.orgId) continue;
      if (m.type === "session" || (m.expiresAt != null && m.expiresAt < t)) {
        this.store.memories.delete(id);
        n++;
      }
    }
    return n;
  }
}
