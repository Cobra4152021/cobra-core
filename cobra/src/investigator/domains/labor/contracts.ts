/** Contract intelligence models (KC-006). */

export type LaborContractKind =
  | "cba"
  | "mou"
  | "side_letter"
  | "personnel_order"
  | "policy_directive"
  | "letter_of_agreement"
  | "settlement"
  | "arbitration_award";

export interface LaborContractRecord {
  id: string;
  kind: LaborContractKind;
  title: string;
  version: string;
  effectiveDate: string | null;
  expirationDate: string | null;
  supersededBy: string | null;
  crossReferences: string[];
  relatedArticleIds: string[];
  citations: string[];
  bodyText: string;
  notes: string | null;
}

export function createContractRecord(
  input: Partial<LaborContractRecord> & Pick<LaborContractRecord, "id" | "kind" | "title">,
): LaborContractRecord {
  return {
    id: input.id,
    kind: input.kind,
    title: input.title,
    version: input.version ?? "1",
    effectiveDate: input.effectiveDate ?? null,
    expirationDate: input.expirationDate ?? null,
    supersededBy: input.supersededBy ?? null,
    crossReferences: input.crossReferences ?? [],
    relatedArticleIds: input.relatedArticleIds ?? [],
    citations: input.citations ?? [],
    bodyText: input.bodyText ?? "",
    notes: input.notes ?? null,
  };
}
