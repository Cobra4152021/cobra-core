/** Evidence matrix builder (KC-009). */

export type EvidenceRelation =
  | "supports"
  | "contradicts"
  | "neutral"
  | "uncertain"
  | "duplicate"
  | "outlier"
  | "missing";

export interface EvidenceMatrixRow {
  id: string;
  claim: string;
  sourceId: string;
  relation: EvidenceRelation;
  notes?: string;
}

export interface EvidenceMatrix {
  rows: EvidenceMatrixRow[];
  relations: Record<EvidenceRelation, number>;
}

export interface EvidenceMatrixSummary {
  totalRows: number;
  supports: number;
  contradicts: number;
  neutral: number;
  uncertain: number;
  duplicate: number;
  outlier: number;
  missing: number;
  conflictRatio: number;
  coverageRatio: number;
}

export function buildEvidenceMatrix(rows: EvidenceMatrixRow[]): EvidenceMatrix {
  const relations: Record<EvidenceRelation, number> = {
    supports: 0,
    contradicts: 0,
    neutral: 0,
    uncertain: 0,
    duplicate: 0,
    outlier: 0,
    missing: 0,
  };

  for (const row of rows) {
    relations[row.relation] = (relations[row.relation] ?? 0) + 1;
  }

  return { rows: rows.map((r) => ({ ...r })), relations };
}

export function summarizeMatrix(matrix: EvidenceMatrix): EvidenceMatrixSummary {
  const { relations, rows } = matrix;
  const totalRows = rows.length;
  const supports = relations.supports ?? 0;
  const contradicts = relations.contradicts ?? 0;
  const neutral = relations.neutral ?? 0;
  const uncertain = relations.uncertain ?? 0;
  const duplicate = relations.duplicate ?? 0;
  const outlier = relations.outlier ?? 0;
  const missing = relations.missing ?? 0;

  const substantive = supports + contradicts + neutral + uncertain + outlier;
  const conflictRatio = substantive > 0 ? contradicts / substantive : 0;
  const coverageRatio = totalRows > 0 ? (totalRows - missing) / totalRows : 0;

  return {
    totalRows,
    supports,
    contradicts,
    neutral,
    uncertain,
    duplicate,
    outlier,
    missing,
    conflictRatio,
    coverageRatio,
  };
}
