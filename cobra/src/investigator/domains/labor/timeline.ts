/** Labor evidence timeline (KC-006). */

export type LaborTimelineSourceKind =
  | "contract"
  | "email"
  | "policy"
  | "personnel_order"
  | "meeting_notes"
  | "grievance"
  | "arbitration"
  | "staffing_report"
  | "payroll"
  | "other";

export interface LaborTimelineEvent {
  id: string;
  at: string;
  kind: LaborTimelineSourceKind;
  label: string;
  citationId: string | null;
  notes: string | null;
}

export function buildLaborTimeline(
  events: Array<Partial<LaborTimelineEvent> & Pick<LaborTimelineEvent, "id" | "at" | "label">>,
): LaborTimelineEvent[] {
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
