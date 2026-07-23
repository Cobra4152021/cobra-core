import type { CkeStore } from "../db/store.js";
import type { AuthContext, Conflict, ConflictType, Fact } from "../types.js";
import { contentHash, newId, now } from "../util.js";
import { EntityEngine } from "../entity/index.js";

export class ConflictEngine {
  private entities: EntityEngine;

  constructor(private store: CkeStore) {
    this.entities = new EntityEngine(store);
  }

  open(
    ctx: AuthContext,
    input: {
      conflictType: ConflictType;
      summary: string;
      leftRef: string;
      rightRef: string;
      projectId?: string | null;
      details?: Record<string, unknown>;
    },
  ): Conflict {
    const ts = now();
    const c: Conflict = {
      id: newId("cfl"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      conflictType: input.conflictType,
      summary: input.summary,
      leftRef: input.leftRef,
      rightRef: input.rightRef,
      status: "open",
      details: input.details ?? {},
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.conflicts.set(c.id, c);
    return c;
  }

  listOpen(ctx: AuthContext, projectId?: string | null): Conflict[] {
    return [...this.store.conflicts.values()].filter(
      (c) =>
        c.orgId === ctx.orgId &&
        c.status === "open" &&
        (projectId == null || c.projectId === projectId),
    );
  }

  /** Surface contradictory facts instead of silently choosing. */
  detectFactConflicts(ctx: AuthContext, projectId?: string | null): Conflict[] {
    const facts = [...this.store.facts.values()].filter(
      (f) => f.orgId === ctx.orgId && (projectId == null || f.projectId === projectId),
    );
    const byNorm = new Map<string, Fact[]>();
    for (const f of facts) {
      const key = f.statement.toLowerCase().replace(/\s+/g, " ").trim();
      // Negation heuristic: "X is Y" vs "X is not Y"
      const neg = key.replace(/\bis not\b/g, "is");
      const bucket = byNorm.get(neg) ?? [];
      bucket.push(f);
      byNorm.set(neg, bucket);
    }
    const out: Conflict[] = [];
    for (const [, group] of byNorm) {
      const hasPos = group.some((f) => !/\bis not\b/i.test(f.statement));
      const hasNeg = group.some((f) => /\bis not\b/i.test(f.statement));
      if (hasPos && hasNeg) {
        const a = group.find((f) => !/\bis not\b/i.test(f.statement))!;
        const b = group.find((f) => /\bis not\b/i.test(f.statement))!;
        out.push(
          this.open(ctx, {
            conflictType: "contradictory_facts",
            summary: `Contradictory facts: "${a.statement}" vs "${b.statement}"`,
            leftRef: a.id,
            rightRef: b.id,
            projectId,
            details: { leftConfidence: a.confidence, rightConfidence: b.confidence },
          }),
        );
      }
    }
    for (const [a, b] of this.entities.findDuplicates(ctx, projectId)) {
      out.push(
        this.open(ctx, {
          conflictType: "duplicate_entities",
          summary: `Possible duplicate entities: ${a.canonicalName} / ${b.canonicalName}`,
          leftRef: a.id,
          rightRef: b.id,
          projectId,
        }),
      );
    }
    return out;
  }

  storeFact(
    ctx: AuthContext,
    statement: string,
    opts: { projectId?: string | null; confidence?: number; entityIds?: string[]; citationIds?: string[] } = {},
  ): Fact {
    const ts = now();
    const fact: Fact = {
      id: newId("fact"),
      orgId: ctx.orgId,
      projectId: opts.projectId ?? null,
      statement,
      confidence: opts.confidence ?? 0.6,
      entityIds: opts.entityIds ?? [],
      citations: [],
      contentHash: contentHash(statement),
      permissions: {
        orgId: ctx.orgId,
        projectId: opts.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: opts.projectId ? "project" : "organization",
      },
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.facts.set(fact.id, fact);
    return fact;
  }
}
