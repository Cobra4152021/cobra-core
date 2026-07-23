/** Research timeline builder (KC-009). */

export type ResearchTimelineKind =
  | "publication"
  | "event"
  | "field_observation"
  | "experiment"
  | "discovery"
  | "policy_change"
  | "sighting"
  | "other";

export interface ResearchTimelineEvent {
  id: string;
  at: string;
  kind: ResearchTimelineKind;
  label: string;
  citationId: string | null;
  notes: string | null;
}

export function buildResearchTimeline(
  events: Array<Partial<ResearchTimelineEvent> & Pick<ResearchTimelineEvent, "id" | "at" | "label">>,
): ResearchTimelineEvent[] {
  return events
    .map((e) => ({
      id: e.id,
      at: e.at,
      kind: e.kind ?? "other",
      label: e.label,
      citationId: e.citationId ?? null,
      notes: e.notes ?? null,
    }))
    .sort((a, b) => String(a.at).localeCompare(String(b.at)));
}

export function filterResearchTimeline(
  events: ResearchTimelineEvent[],
  filter: { kinds?: ResearchTimelineKind[]; after?: string; before?: string },
): ResearchTimelineEvent[] {
  return events.filter((e) => {
    if (filter.kinds?.length && !filter.kinds.includes(e.kind)) return false;
    if (filter.after && String(e.at) < filter.after) return false;
    if (filter.before && String(e.at) > filter.before) return false;
    return true;
  });
}
