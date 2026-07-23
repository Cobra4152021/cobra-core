/** Research evidence taxonomy (KC-009). */

export type ResearchEvidenceCategoryId =
  | "peer_reviewed_paper"
  | "government_report"
  | "primary_source"
  | "secondary_source"
  | "expert_testimony"
  | "field_observation"
  | "anonymous_source"
  | "internet_article"
  | "book"
  | "newspaper"
  | "audio"
  | "geographic"
  | "environmental"
  | "other";

export interface ResearchEvidenceCategory {
  id: ResearchEvidenceCategoryId;
  label: string;
  reliabilityHint: "high" | "medium" | "low" | "variable";
  notes: string;
}

export const RESEARCH_EVIDENCE_CATEGORIES: ResearchEvidenceCategory[] = [
  { id: "peer_reviewed_paper", label: "Peer-Reviewed Paper", reliabilityHint: "high", notes: "Track journal, DOI, and peer-review status." },
  { id: "government_report", label: "Government Report", reliabilityHint: "high", notes: "Official agency or legislative publication." },
  { id: "primary_source", label: "Primary Source", reliabilityHint: "high", notes: "Original records, data, or firsthand documentation." },
  { id: "secondary_source", label: "Secondary Source", reliabilityHint: "medium", notes: "Analysis or summary of primary sources." },
  { id: "expert_testimony", label: "Expert Testimony", reliabilityHint: "variable", notes: "Credentials and conflicts of interest required." },
  { id: "field_observation", label: "Field Observation", reliabilityHint: "medium", notes: "Document observer, conditions, and instrumentation." },
  { id: "anonymous_source", label: "Anonymous Source", reliabilityHint: "low", notes: "Corroboration strongly recommended." },
  { id: "internet_article", label: "Internet Article", reliabilityHint: "low", notes: "Verify publisher and archival capture." },
  { id: "book", label: "Book", reliabilityHint: "medium", notes: "Edition, publisher, and citation page required." },
  { id: "newspaper", label: "Newspaper", reliabilityHint: "medium", notes: "Distinguish reporting from editorial." },
  { id: "audio", label: "Audio Recording", reliabilityHint: "variable", notes: "Chain of custody and transcription quality matter." },
  { id: "geographic", label: "Geographic Data", reliabilityHint: "medium", notes: "Coordinate system and acquisition method required." },
  { id: "environmental", label: "Environmental Data", reliabilityHint: "medium", notes: "Sensor calibration and sampling protocol required." },
  { id: "other", label: "Other", reliabilityHint: "variable", notes: "Classify before synthesis." },
];

export function getResearchEvidenceCategory(id: string): ResearchEvidenceCategory | null {
  return RESEARCH_EVIDENCE_CATEGORIES.find((c) => c.id === id) ?? null;
}
