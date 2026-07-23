/**
 * Missing Evidence Engine (KC-004B).
 * Detects missing documents, approvals, payroll, policies, contracts, timeline gaps.
 */

import type { EvidenceItem } from "./findings.js";
import type { InvestigationStrategy } from "./strategy.js";

export interface MissingEvidenceItem {
  category:
    | "document"
    | "approval"
    | "payroll"
    | "policy"
    | "contract"
    | "timeline_gap"
    | "other";
  label: string;
  reason: string;
  priority: "critical" | "high" | "medium" | "low";
}

export interface MissingEvidenceReport {
  items: MissingEvidenceItem[];
  evidenceNeededSection: string[];
}

function present(evidence: EvidenceItem[], needles: string[]): boolean {
  return evidence.some((e) => {
    const hay = `${e.kind} ${e.label} ${e.excerpt ?? ""}`.toLowerCase();
    return needles.some((n) => hay.includes(n.toLowerCase()));
  });
}

const CATALOG: {
  category: MissingEvidenceItem["category"];
  label: string;
  needles: string[];
  priority: MissingEvidenceItem["priority"];
  strategies?: string[];
}[] = [
  {
    category: "contract",
    label: "Collective agreement / contract text",
    needles: ["agreement", "contract", "collective"],
    priority: "critical",
    strategies: ["union_contract_review"],
  },
  {
    category: "payroll",
    label: "Payroll / overtime extracts",
    needles: ["payroll", "overtime", "timesheet", "ot "],
    priority: "high",
    strategies: ["union_contract_review", "staffing_analysis", "budget_audit"],
  },
  {
    category: "document",
    label: "Staffing / vacancy tables",
    needles: ["vacanc", "staffing", "headcount", "fte"],
    priority: "high",
    strategies: ["staffing_analysis", "union_contract_review"],
  },
  {
    category: "document",
    label: "Budget and actuals",
    needles: ["budget", "actual", "variance", "expenditure"],
    priority: "critical",
    strategies: ["budget_audit"],
  },
  {
    category: "approval",
    label: "Approvals / decision records",
    needles: ["approval", "approved", "decision", "authorize", "transfer memo"],
    priority: "high",
  },
  {
    category: "policy",
    label: "Governing policy / procedure",
    needles: ["policy", "procedure", "directive", "regulation"],
    priority: "high",
    strategies: ["policy_review", "compliance_investigation", "union_contract_review"],
  },
  {
    category: "timeline_gap",
    label: "Contemporaneous timeline covering the period of interest",
    needles: ["timeline", "chronolog", "dated", "202"],
    priority: "medium",
  },
  {
    category: "document",
    label: "Incident / change records",
    needles: ["incident", "change record", "deploy", "outage"],
    priority: "high",
    strategies: ["technical_root_cause", "security_investigation"],
  },
];

export function detectMissingEvidence(input: {
  strategy: InvestigationStrategy;
  evidence: EvidenceItem[];
  evidenceNeeded: string[];
  timelineLines: string[];
}): MissingEvidenceReport {
  const items: MissingEvidenceItem[] = [];

  for (const entry of CATALOG) {
    if (entry.strategies && !entry.strategies.includes(input.strategy.id)) continue;
    if (!present(input.evidence, entry.needles)) {
      items.push({
        category: entry.category,
        label: entry.label,
        reason: `No retrieved evidence matched indicators for "${entry.label}".`,
        priority: entry.priority,
      });
    }
  }

  for (const needed of input.evidenceNeeded) {
    const needles = needed.toLowerCase().split(/[^a-z0-9]+/).filter((t) => t.length > 3);
    if (!present(input.evidence, needles.length ? needles : [needed.toLowerCase()])) {
      const already = items.some((i) => i.label.toLowerCase() === needed.toLowerCase());
      if (!already) {
        items.push({
          category: "other",
          label: needed,
          reason: "Listed as strategy evidence priority but not retrieved.",
          priority: "medium",
        });
      }
    }
  }

  if (input.timelineLines.length === 0) {
    items.push({
      category: "timeline_gap",
      label: "Timeline events for the investigation window",
      reason: "No timeline events were collected.",
      priority: "high",
    });
  } else if (input.timelineLines.length < 3) {
    items.push({
      category: "timeline_gap",
      label: "Additional timeline coverage",
      reason: "Timeline is sparse (<3 events); gaps may hide causal sequence.",
      priority: "medium",
    });
  }

  // Deduplicate by label
  const seen = new Set<string>();
  const unique = items.filter((i) => {
    const k = i.label.toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  const evidenceNeededSection = unique.map(
    (i) => `[${i.priority}/${i.category}] ${i.label} — ${i.reason}`,
  );

  return { items: unique.slice(0, 20), evidenceNeededSection };
}
