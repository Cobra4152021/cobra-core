/** Past practice engine (KC-006). */

export type PastPracticeConfidence = "high" | "medium" | "low" | "insufficient";

export interface PastPracticeAssessment {
  allegedPractice: string;
  historicalInstances: string[];
  exceptions: string[];
  durationNotes: string | null;
  consistencyNotes: string | null;
  managementChanges: string[];
  writtenPolicy: string | null;
  actualPracticeNotes: string | null;
  supportingEvidence: string[];
  confidence: PastPracticeConfidence;
  limitations: string[];
  disclaimer: string;
}

export function assessPastPractice(input: {
  allegedPractice: string;
  historicalInstances?: string[];
  exceptions?: string[];
  durationNotes?: string | null;
  consistencyNotes?: string | null;
  managementChanges?: string[];
  writtenPolicy?: string | null;
  actualPracticeNotes?: string | null;
  supportingEvidence?: string[];
}): PastPracticeAssessment {
  const instances = input.historicalInstances ?? [];
  const exceptions = input.exceptions ?? [];
  let confidence: PastPracticeConfidence = "insufficient";
  if (instances.length >= 3 && exceptions.length === 0 && input.durationNotes) {
    confidence = "medium";
  } else if (instances.length >= 5 && exceptions.length <= 1 && input.durationNotes) {
    confidence = "high";
  } else if (instances.length > 0) {
    confidence = "low";
  }

  return {
    allegedPractice: input.allegedPractice.trim(),
    historicalInstances: instances,
    exceptions,
    durationNotes: input.durationNotes ?? null,
    consistencyNotes: input.consistencyNotes ?? null,
    managementChanges: input.managementChanges ?? [],
    writtenPolicy: input.writtenPolicy ?? null,
    actualPracticeNotes: input.actualPracticeNotes ?? null,
    supportingEvidence: input.supportingEvidence ?? [],
    confidence,
    limitations: [
      "Past practice doctrines vary by jurisdiction and agreement.",
      "Exceptions and management changes may undermine consistency claims.",
      "Human determination required.",
    ],
    disclaimer: "Not a binding past-practice ruling. Not legal advice.",
  };
}
