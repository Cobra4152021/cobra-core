/**
 * Competing Hypotheses Engine (KC-004B).
 * Multiple explanations with support, contradiction, confidence, and gaps.
 */

import type { ConfidenceLevel } from "./types.js";
import type { EvidenceItem, ConflictItem } from "./findings.js";
import type { InvestigationStrategy } from "./strategy.js";

export interface HypothesisDraft {
  id: string;
  title: string;
  summary: string;
  supportingEvidence: string[];
  contradictingEvidence: string[];
  confidence: ConfidenceLevel;
  missingEvidence: string[];
  status: "active" | "weakened" | "unsupported";
}

function confidenceFromSupport(
  support: number,
  contradict: number,
  missing: number,
): ConfidenceLevel {
  if (support === 0) return "insufficient_evidence";
  if (contradict >= support) return "low";
  if (support >= 3 && contradict === 0 && missing <= 1) return "high";
  if (support >= 2 && contradict <= 1) return "medium";
  return "low";
}

function tokens(s: string): string[] {
  return s
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 3);
}

function evidenceMatches(item: EvidenceItem, needles: string[]): boolean {
  const hay = `${item.label} ${item.excerpt ?? ""}`.toLowerCase();
  return needles.some((n) => hay.includes(n.toLowerCase()));
}

/**
 * Build competing hypotheses. Never collapses to a single explanation.
 */
export function buildCompetingHypotheses(input: {
  title: string;
  questions: string[];
  strategy: InvestigationStrategy;
  evidence: EvidenceItem[];
  conflicts: ConflictItem[];
  missingEvidence: string[];
}): HypothesisDraft[] {
  const hypotheses: HypothesisDraft[] = [];
  const prompt = input.title.toLowerCase();

  const candidates: { title: string; needles: string[]; missing: string[] }[] = [];

  if (/overtime|ot\b/.test(prompt) || input.strategy.id === "union_contract_review") {
    candidates.push(
      {
        title: "Vacancy-driven overtime",
        needles: ["vacanc", "staff", "fte", "headcount", "hiring"],
        missing: ["staffing tables", "vacancy reports"],
      },
      {
        title: "Workload or demand surge",
        needles: ["workload", "demand", "volume", "caseload"],
        missing: ["workload metrics", "demand series"],
      },
      {
        title: "Contractual or policy non-compliance",
        needles: ["contract", "agreement", "policy", "grievance", "limit"],
        missing: ["collective agreement", "overtime policy"],
      },
      {
        title: "Budget or scheduling practice change",
        needles: ["budget", "schedule", "approval", "transfer"],
        missing: ["budget lines", "scheduling records"],
      },
    );
  } else if (input.strategy.id === "budget_audit" || /budget|variance/.test(prompt)) {
    candidates.push(
      {
        title: "Unauthorized or unrecorded spending",
        needles: ["unauthorized", "overrun", "actual", "spend"],
        missing: ["approvals", "actuals"],
      },
      {
        title: "Authorized transfer or supplement",
        needles: ["transfer", "supplement", "approved", "decision"],
        missing: ["transfer memos", "decision records"],
      },
      {
        title: "Classification or accounting error",
        needles: ["reclass", "error", "coding", "account"],
        missing: ["ledger extracts", "reconciliation"],
      },
    );
  } else if (input.strategy.id === "technical_root_cause") {
    candidates.push(
      {
        title: "Recent change introduced the defect",
        needles: ["change", "deploy", "release", "config"],
        missing: ["change records", "deploy logs"],
      },
      {
        title: "Capacity or dependency failure",
        needles: ["timeout", "capacity", "dependency", "latency"],
        missing: ["monitoring", "dependency health"],
      },
      {
        title: "Pre-existing latent defect",
        needles: ["latent", "legacy", "intermittent", "race"],
        missing: ["historical incidents", "code review notes"],
      },
    );
  } else {
    // Generic: one hypothesis per top question + an alternative
    for (const q of input.questions.slice(0, 3)) {
      const n = tokens(q).slice(0, 4);
      candidates.push({
        title: `Explanation addressing: ${q.slice(0, 80)}`,
        needles: n,
        missing: input.strategy.evidencePriorities.slice(0, 2),
      });
    }
    candidates.push({
      title: "Insufficient evidence — no durable explanation yet",
      needles: [],
      missing: input.strategy.evidencePriorities.slice(0, 4),
    });
  }

  // Always keep at least two active alternatives
  if (candidates.length < 2) {
    candidates.push({
      title: "Alternative explanation not yet tested",
      needles: tokens(input.title).slice(0, 3),
      missing: input.missingEvidence.slice(0, 3),
    });
  }

  let i = 0;
  for (const c of candidates.slice(0, 6)) {
    i += 1;
    const supporting = input.evidence
      .filter((e) => (c.needles.length ? evidenceMatches(e, c.needles) : false))
      .map((e) => e.id || e.label);
    const contradicting = input.conflicts
      .filter((conf) => {
        const s = conf.summary.toLowerCase();
        return c.needles.some((n) => s.includes(n)) || /conflict|disagree|contradict/.test(s);
      })
      .map((conf) => conf.summary);

    // Soft contradiction: evidence that matches competing needles more strongly
    for (const other of candidates) {
      if (other === c) continue;
      for (const e of input.evidence) {
        if (evidenceMatches(e, other.needles) && !evidenceMatches(e, c.needles)) {
          const id = e.id || e.label;
          if (!contradicting.includes(id) && contradicting.length < 6) {
            contradicting.push(`Supports alternative "${other.title}": ${id}`);
          }
        }
      }
    }

    const missing = [
      ...new Set([
        ...c.missing.filter((m) =>
          !input.evidence.some((e) => evidenceMatches(e, tokens(m))),
        ),
        ...input.missingEvidence.slice(0, 2),
      ]),
    ].slice(0, 6);

    const confidence = confidenceFromSupport(
      supporting.length,
      contradicting.length,
      missing.length,
    );
    const status: HypothesisDraft["status"] =
      supporting.length === 0
        ? "unsupported"
        : contradicting.length >= supporting.length
          ? "weakened"
          : "active";

    hypotheses.push({
      id: `hyp_${i}`,
      title: c.title,
      summary:
        supporting.length === 0
          ? "No supporting evidence retrieved yet. Keep as an open alternative."
          : `Supported by ${supporting.length} evidence item(s); ${contradicting.length} contradicting signal(s); ${missing.length} gap(s).`,
      supportingEvidence: supporting,
      contradictingEvidence: contradicting,
      confidence,
      missingEvidence: missing,
      status,
    });
  }

  return hypotheses;
}
