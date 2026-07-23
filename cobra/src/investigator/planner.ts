/**
 * Investigation planner — works WITHOUT an LLM (KC-004 / KC-004B).
 * Uses Strategy Engine for questions, evidence priorities, and deliverables.
 */

import type { InvestigationPlan, Priority } from "./types.js";
import { getTemplate } from "./templates.js";
import { selectStrategy } from "./strategy.js";
import { getGovernmentTemplate } from "./domains/government/templates.js";
import { getLaborTemplate } from "./domains/labor/templates.js";
import { getResearchTemplate } from "./domains/research/templates.js";

function inferPriority(title: string, description: string, fallback: Priority): Priority {
  const t = `${title} ${description}`.toLowerCase();
  if (/critical|urgent|immediate|safety/.test(t)) return "critical";
  if (/high|serious|material/.test(t)) return "high";
  if (/low|minor|informational/.test(t)) return "low";
  return fallback;
}

function uniqueStrings(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    const k = item.toLowerCase().trim();
    if (!k || seen.has(k)) continue;
    seen.add(k);
    out.push(item.trim());
  }
  return out;
}

/**
 * Build a deterministic investigation plan. No LLM required.
 */
export function planInvestigation(input: {
  title: string;
  description?: string | null;
  templateId?: string | null;
  strategyId?: string | null;
  knownFacts?: string[];
}): InvestigationPlan {
  const strategy = selectStrategy({
    title: input.title,
    description: input.description,
    templateId: input.templateId,
    strategyId: input.strategyId,
  });
  const template = getTemplate(input.templateId ?? strategy.templateId);
  const govTemplate = getGovernmentTemplate(input.templateId);
  const laborTemplate = getLaborTemplate(input.templateId);
  const researchTemplate = getResearchTemplate(input.templateId);
  const domainTemplate = researchTemplate ?? laborTemplate ?? govTemplate;
  const known = input.knownFacts ?? [];

  const questions = uniqueStrings([
    ...(domainTemplate?.defaultQuestions ?? template?.defaultQuestions ?? []),
    ...strategy.questions,
  ]).slice(0, 12);

  const evidenceNeeded = uniqueStrings([
    ...(domainTemplate?.evidenceNeeded ?? template?.evidenceNeeded ?? []),
    ...strategy.evidencePriorities,
    "Knowledge Engine memories and facts",
    "Evidence Vault documents and citations",
    "Timeline events and decisions",
    "Recorded conflicts",
  ]);

  const unknown = questions.map((q) => `Unresolved: ${q}`);

  return {
    goal: input.title.trim() || "Investigate the stated problem",
    questions,
    evidenceNeeded,
    knownFacts: known,
    unknownFacts: unknown,
    assumptions: [
      "Accessible evidence is limited to the caller's organization and project scope.",
      "Conclusions require citations; unsupported claims are marked insufficient evidence.",
      "Conflicts between sources are preserved, not silently resolved.",
      "Competing hypotheses remain visible until disconfirmed.",
    ],
    steps: [
      "Select investigation strategy and finalize scope",
      "Collect evidence from Knowledge Engine and Evidence Vault",
      "Score evidence quality",
      "Build timeline of relevant events and decisions",
      "Detect conflicts and missing evidence",
      "Generate competing hypotheses",
      "Draft findings with citations and confidence",
      "Draft recommendations linked to findings",
      "Run review checklist",
      "Generate citation-backed report",
      "Review and publish or archive",
    ],
    priority: inferPriority(
      input.title,
      input.description ?? "",
      domainTemplate?.riskLevel === "critical" || domainTemplate?.riskLevel === "high"
        ? "high"
        : strategy.defaultPriority,
    ),
    deliverables: uniqueStrings([
      ...(domainTemplate?.deliverables ?? template?.deliverables ?? []),
      ...strategy.expectedDeliverables,
      "competing hypotheses",
      "missing evidence",
      "confidence summary",
      "review checklist",
    ]),
    templateId: domainTemplate?.id ?? template?.id ?? strategy.templateId,
    strategyId: strategy.id,
    strategyName: strategy.name,
    confidenceRules: strategy.confidenceRules,
    methodology: [
      `Strategy: ${strategy.name} (${strategy.id})`,
      researchTemplate
        ? "Research Edition domain pack (KC-009)"
        : laborTemplate
          ? "Labor Edition domain pack (KC-006)"
          : govTemplate
            ? "Government Edition domain pack (KC-005)"
            : "Deterministic planner (no required LLM)",
      "CKE/Evidence Vault retrieval with citation allowlist",
      "Evidence quality scoring across seven dimensions",
      "Competing hypotheses retained",
      "Missing evidence detection",
      "Separated confidence + readiness review gate",
      ...(laborTemplate
        ? ["Not legal advice; no liability, ULP, or breach determination"]
        : []),
      ...(researchTemplate
        ? ["Evidence synthesis only; not peer review or scientific publication"]
        : []),
    ],
  };
}
