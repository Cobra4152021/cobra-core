import type { CkeStore } from "../db/store.js";
import type { AuthContext, CitationRef } from "../types.js";
import { clampConfidence, newId, now } from "../util.js";

/**
 * Evidence Vault integration surface.
 * Never invent citations — only store what callers provide with document hashes.
 */
export class CitationEngine {
  constructor(private store: CkeStore) {}

  create(
    ctx: AuthContext,
    input: {
      evidenceKind: string;
      documentId?: string;
      documentHash?: string;
      page?: number;
      lineStart?: number;
      lineEnd?: number;
      uri?: string;
      excerpt?: string;
      projectId?: string | null;
      confidence?: number;
    },
  ): CitationRef {
    if (!input.documentId && !input.documentHash && !input.uri && !input.excerpt) {
      throw new Error("Citation requires documentId, documentHash, uri, or excerpt evidence");
    }
    const ref: CitationRef & { orgId: string; projectId?: string | null; createdAt: number } = {
      id: newId("cite"),
      evidenceKind: input.evidenceKind,
      documentId: input.documentId ?? null,
      documentHash: input.documentHash ?? null,
      page: input.page ?? null,
      lineStart: input.lineStart ?? null,
      lineEnd: input.lineEnd ?? null,
      uri: input.uri ?? null,
      excerpt: input.excerpt ?? null,
      confidence: clampConfidence(input.confidence ?? 1),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      createdAt: now(),
    };
    this.store.citations.set(ref.id, ref);
    return {
      id: ref.id,
      evidenceKind: ref.evidenceKind,
      documentId: ref.documentId,
      documentHash: ref.documentHash,
      page: ref.page,
      lineStart: ref.lineStart,
      lineEnd: ref.lineEnd,
      uri: ref.uri,
      excerpt: ref.excerpt,
      confidence: ref.confidence,
    };
  }

  get(id: string): CitationRef | null {
    const c = this.store.citations.get(id);
    if (!c) return null;
    return {
      id: c.id,
      evidenceKind: c.evidenceKind,
      documentId: c.documentId,
      documentHash: c.documentHash,
      page: c.page,
      lineStart: c.lineStart,
      lineEnd: c.lineEnd,
      uri: c.uri,
      excerpt: c.excerpt,
      confidence: c.confidence,
    };
  }

  /** Reject fabricated citation ids not present in vault. */
  resolveAll(ids: string[]): CitationRef[] {
    const out: CitationRef[] = [];
    for (const id of ids) {
      const c = this.get(id);
      if (!c) throw new Error(`Unknown citation id: ${id}`);
      out.push(c);
    }
    return out;
  }
}
