/** Government data sensitivity labels (KC-005). */

export type GovernmentSensitivity =
  | "public"
  | "internal"
  | "confidential"
  | "personnel"
  | "labor_relations"
  | "security_sensitive"
  | "legally_restricted"
  | "unknown";

export const GOVERNMENT_SENSITIVITY_LABELS: GovernmentSensitivity[] = [
  "public",
  "internal",
  "confidential",
  "personnel",
  "labor_relations",
  "security_sensitive",
  "legally_restricted",
  "unknown",
];

const PUBLISH_WARN_SET = new Set<GovernmentSensitivity>([
  "personnel",
  "labor_relations",
  "security_sensitive",
  "legally_restricted",
  "confidential",
]);

export function publishWarningsForSensitivity(labels: GovernmentSensitivity[]): string[] {
  const warns: string[] = [];
  const set = new Set(labels);
  if (set.has("personnel")) warns.push("Cited sources may include personnel data — review before publication.");
  if (set.has("labor_relations"))
    warns.push("Cited sources may include protected labor-relations information.");
  if (set.has("security_sensitive"))
    warns.push("Cited sources may include security procedures — restrict distribution.");
  if (set.has("legally_restricted"))
    warns.push("Cited sources may be legally restricted — confirm disclosure authority.");
  if (set.has("confidential") && !set.has("personnel"))
    warns.push("Cited sources are labeled confidential — confirm audience.");
  return warns;
}

export function requiresPublishReview(labels: GovernmentSensitivity[]): boolean {
  return labels.some((l) => PUBLISH_WARN_SET.has(l));
}
