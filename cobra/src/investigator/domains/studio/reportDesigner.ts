/** Report designer transforms (KC-007). */

export type StudioReportSectionId =
  | "cover"
  | "executive_summary"
  | "investigation_overview"
  | "timeline"
  | "findings"
  | "evidence_summary"
  | "metrics"
  | "graph_snapshot"
  | "recommendations"
  | "confidence"
  | "appendix"
  | "citations";

export interface StudioReportSection {
  id: StudioReportSectionId;
  label: string;
  required: boolean;
  defaultOrder: number;
}

export interface StudioReportLayout {
  sections: StudioReportSection[];
  orderedSectionIds: StudioReportSectionId[];
}

export interface StudioExportResult {
  exportStatus: "placeholder";
  message: string;
}

export const STUDIO_REPORT_SECTION_CATALOG: StudioReportSection[] = [
  { id: "cover", label: "Cover", required: true, defaultOrder: 0 },
  { id: "executive_summary", label: "Executive summary", required: true, defaultOrder: 1 },
  { id: "investigation_overview", label: "Investigation overview", required: false, defaultOrder: 2 },
  { id: "timeline", label: "Timeline", required: false, defaultOrder: 3 },
  { id: "findings", label: "Findings", required: true, defaultOrder: 4 },
  { id: "evidence_summary", label: "Evidence summary", required: false, defaultOrder: 5 },
  { id: "metrics", label: "Metrics", required: false, defaultOrder: 6 },
  { id: "graph_snapshot", label: "Relationship graph", required: false, defaultOrder: 7 },
  { id: "recommendations", label: "Recommendations", required: false, defaultOrder: 8 },
  { id: "confidence", label: "Confidence", required: true, defaultOrder: 9 },
  { id: "appendix", label: "Appendix", required: false, defaultOrder: 10 },
  { id: "citations", label: "Citations", required: true, defaultOrder: 11 },
];

const catalogById = new Map(STUDIO_REPORT_SECTION_CATALOG.map((s) => [s.id, s]));

export function composeReportLayout(sectionIds: StudioReportSectionId[]): StudioReportLayout {
  const orderedSectionIds = sectionIds.filter((id) => catalogById.has(id));
  const sections = orderedSectionIds.map((id) => catalogById.get(id)!);
  return { sections, orderedSectionIds };
}

export function exportReportPlaceholder(): StudioExportResult {
  return {
    exportStatus: "placeholder",
    message: "Export pipeline not enabled",
  };
}
