/** Unified studio search index (KC-007). */

export type StudioSearchHitKind =
  | "cke"
  | "vault"
  | "investigation"
  | "report"
  | "template"
  | "contract"
  | "policy"
  | "government"
  | "labor"
  | "timeline";

export interface StudioSearchHit {
  id: string;
  kind: StudioSearchHitKind;
  title: string;
  snippet: string;
  updatedAt: string | null;
  tags?: string[];
}

export interface StudioSearchIndex {
  hits: StudioSearchHit[];
  builtAt: string;
}

export interface StudioSearchOptions {
  q?: string;
  kinds?: StudioSearchHitKind[];
  limit?: number;
}

export function buildUnifiedSearchIndex(
  hits: StudioSearchHit[],
  builtAt = new Date().toISOString(),
): StudioSearchIndex {
  const sorted = [...hits].sort((a, b) => {
    const ta = a.updatedAt ?? "";
    const tb = b.updatedAt ?? "";
    return tb.localeCompare(ta) || a.title.localeCompare(b.title);
  });
  return { hits: sorted, builtAt };
}

export function searchStudioIndex(
  index: StudioSearchIndex,
  options: StudioSearchOptions = {},
): StudioSearchHit[] {
  const q = options.q?.trim().toLowerCase();
  const kinds = options.kinds?.length ? new Set(options.kinds) : null;
  const limit = options.limit != null && options.limit > 0 ? options.limit : undefined;

  let results = index.hits.filter((hit) => {
    if (kinds && !kinds.has(hit.kind)) return false;
    if (q) {
      const hay = `${hit.title} ${hit.snippet} ${(hit.tags ?? []).join(" ")}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  if (limit != null) {
    results = results.slice(0, limit);
  }

  return results;
}
