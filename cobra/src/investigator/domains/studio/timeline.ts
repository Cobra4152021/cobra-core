/** Studio timeline transforms (KC-007). */

export type StudioTimelineEventKind =
  | "evidence"
  | "finding"
  | "report"
  | "email"
  | "policy"
  | "budget"
  | "contract"
  | "meeting"
  | "staffing"
  | "grievance"
  | "arbitration"
  | "other";

export interface StudioTimelineEvent {
  id: string;
  at: string;
  kind: StudioTimelineEventKind;
  label: string;
  sourceId: string | null;
  citationId: string | null;
  notes: string | null;
}

export interface StudioTimelineFilter {
  q?: string;
  kinds?: StudioTimelineEventKind[];
  from?: string;
  to?: string;
}

export interface ComparedTimelineEvent extends StudioTimelineEvent {
  side: "a" | "b" | "both";
}

export function buildStudioTimeline(
  events: Array<Partial<StudioTimelineEvent> & Pick<StudioTimelineEvent, "id" | "at" | "label">>,
): StudioTimelineEvent[] {
  return events
    .map((e) => ({
      id: e.id,
      at: e.at,
      kind: e.kind ?? "other",
      label: e.label,
      sourceId: e.sourceId ?? null,
      citationId: e.citationId ?? null,
      notes: e.notes ?? null,
    }))
    .sort((a, b) => String(a.at).localeCompare(String(b.at)));
}

export function filterStudioTimeline(
  events: StudioTimelineEvent[],
  filter: StudioTimelineFilter = {},
): StudioTimelineEvent[] {
  const q = filter.q?.trim().toLowerCase();
  const kinds = filter.kinds?.length ? new Set(filter.kinds) : null;

  return events.filter((e) => {
    if (kinds && !kinds.has(e.kind)) return false;
    if (filter.from && String(e.at) < filter.from) return false;
    if (filter.to && String(e.at) > filter.to) return false;
    if (q) {
      const hay = `${e.label} ${e.notes ?? ""} ${e.kind}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

export function compareTimelines(
  a: StudioTimelineEvent[],
  b: StudioTimelineEvent[],
): ComparedTimelineEvent[] {
  const byKey = (e: StudioTimelineEvent) => `${e.at}|${e.kind}|${e.label}`;
  const mapA = new Map(a.map((e) => [byKey(e), e]));
  const mapB = new Map(b.map((e) => [byKey(e), e]));
  const keys = new Set([...mapA.keys(), ...mapB.keys()]);
  const merged: ComparedTimelineEvent[] = [];

  for (const key of [...keys].sort()) {
    const inA = mapA.get(key);
    const inB = mapB.get(key);
    if (inA && inB) {
      merged.push({ ...inA, side: "both" });
    } else if (inA) {
      merged.push({ ...inA, side: "a" });
    } else if (inB) {
      merged.push({ ...inB, side: "b" });
    }
  }

  return merged.sort((x, y) => String(x.at).localeCompare(String(y.at)));
}
