import type { CkeStore } from "../db/store.js";

export class Metrics {
  private latencies: Record<string, number[]> = {};

  constructor(private store: CkeStore) {}

  observe(name: string, ms: number): void {
    (this.latencies[name] ??= []).push(ms);
  }

  snapshot(orgId?: string) {
    const filterOrg = <T extends { orgId: string }>(xs: Iterable<T>) =>
      orgId ? [...xs].filter((x) => x.orgId === orgId) : [...xs];

    const avg = (arr: number[]) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);

    return {
      entity_count: filterOrg(this.store.entities.values()).length,
      relationship_count: filterOrg(this.store.relationships.values()).length,
      memory_size: filterOrg(this.store.memories.values()).length,
      fact_count: filterOrg(this.store.facts.values()).length,
      timeline_count: filterOrg(this.store.timeline.values()).length,
      decision_count: filterOrg(this.store.decisions.values()).length,
      conflict_open: [...this.store.conflicts.values()].filter(
        (c) => c.status === "open" && (!orgId || c.orgId === orgId),
      ).length,
      graph_size: filterOrg(this.store.relationships.values()).length,
      search_index_size: orgId
        ? this.store.searchIndex.filter((r) => r.orgId === orgId).length
        : this.store.searchIndex.length,
      latency_ms: {
        search: avg(this.latencies.search ?? []),
        reasoning: avg(this.latencies.reasoning ?? []),
        timeline: avg(this.latencies.timeline ?? []),
        embedding: avg(this.latencies.embedding ?? []),
      },
      cache_hit_rate: null as number | null,
    };
  }
}
