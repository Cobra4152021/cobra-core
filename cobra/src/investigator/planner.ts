/**
 * Investigation planner — works WITHOUT an LLM (KC-004).
 * Deterministic question decomposition + plan structure.
 */

import type { InvestigationPlan, Priority } from "./types.js";
import { getTemplate } from "./templates.js";

const DOMAIN_HINTS: { re: RegExp; questions: string[]; evidence: string[] }[] = [
  {
    re: /overtime|ot\b|extra\s*hours/i,
    questions: [
      "How has overtime volume changed over the relevant period?",
      "What staffing levels and vacancies existed during the increase?",
      "What budget authority covered overtime?",
      "Were contractual or policy limits exceeded?",
      "What historical trends precede the increase?",
    ],
    evidence: ["overtime logs", "staffing/vacancy data", "budget lines", "contracts/policy", "historical series"],
  },
  {
    re: /budget|spending|expenditure|cost/i,
    questions: [
      "What was budgeted versus actual?",
      "Which line items drove variance?",
      "Were supplements or transfers authorized?",
      "Do source documents agree on totals?",
    ],
    evidence: ["budgets", "actuals", "transfer memos", "decision records"],
  },
  {
    re: /staff|vacanc|hiring|workforce|fte/i,
    questions: [
      "What headcount and vacancy rates applied?",
      "When did staffing changes occur?",
      "How did workload compare to capacity?",
    ],
    evidence: ["staffing tables", "vacancy reports", "workload metrics"],
  },
  {
    re: /policy|compliance|regulation|audit/i,
    questions: [
      "Which policies or rules apply?",
      "Where does practice diverge from policy?",
      "What exceptions were approved?",
    ],
    evidence: ["policies", "procedures", "exception approvals"],
  },
];

function inferPriority(title: string, description: string): Priority {
  const t = `${title} ${description}`.toLowerCase();
  if (/critical|urgent|immediate|safety/.test(t)) return "critical";
  if (/high|serious|material/.test(t)) return "high";
  if (/low|minor|informational/.test(t)) return "low";
  return "medium";
}

function decomposeQuestions(prompt: string, templateQuestions: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const add = (q: string) => {
    const k = q.toLowerCase().trim();
    if (!k || seen.has(k)) return;
    seen.add(k);
    out.push(q.trim());
  };

  for (const q of templateQuestions) add(q);
  for (const hint of DOMAIN_HINTS) {
    if (hint.re.test(prompt)) {
      for (const q of hint.questions) add(q);
    }
  }

  // Generic investigation scaffold if still thin
  if (out.length < 3) {
    add(`What is the precise problem stated in: "${prompt.slice(0, 120)}"?`);
    add("What evidence is already available in the Knowledge Engine and Evidence Vault?");
    add("What facts are unknown or unsupported?");
    add("What competing explanations should be tested?");
    add("What timeline of decisions and events is relevant?");
  }

  return out.slice(0, 12);
}

function evidenceNeeded(prompt: string, templateEvidence: string[]): string[] {
  const set = new Set<string>(templateEvidence);
  for (const hint of DOMAIN_HINTS) {
    if (hint.re.test(prompt)) {
      for (const e of hint.evidence) set.add(e);
    }
  }
  set.add("Knowledge Engine memories and facts");
  set.add("Evidence Vault documents and citations");
  set.add("Timeline events and decisions");
  set.add("Recorded conflicts");
  return [...set];
}

/**
 * Build a deterministic investigation plan. No LLM required.
 */
export function planInvestigation(input: {
  title: string;
  description?: string | null;
  templateId?: string | null;
  knownFacts?: string[];
}): InvestigationPlan {
  const template = getTemplate(input.templateId);
  const prompt = `${input.title}\n${input.description ?? ""}`.trim();
  const questions = decomposeQuestions(prompt, template?.defaultQuestions ?? []);
  const known = input.knownFacts ?? [];
  const unknown = questions.map((q) => `Unresolved: ${q}`);

  return {
    goal: input.title.trim() || "Investigate the stated problem",
    questions,
    evidenceNeeded: evidenceNeeded(prompt, template?.evidenceNeeded ?? []),
    knownFacts: known,
    unknownFacts: unknown,
    assumptions: [
      "Accessible evidence is limited to the caller's organization and project scope.",
      "Conclusions require citations; unsupported claims are marked insufficient evidence.",
      "Conflicts between sources are preserved, not silently resolved.",
    ],
    steps: [
      "Finalize investigation scope and questions",
      "Collect evidence from Knowledge Engine and Evidence Vault",
      "Build timeline of relevant events and decisions",
      "Detect conflicts and contradictions",
      "Draft findings with citations and confidence",
      "Draft recommendations linked to findings",
      "Generate citation-backed report",
      "Review and publish or archive",
    ],
    priority: inferPriority(input.title, input.description ?? ""),
    deliverables: template?.deliverables ?? [
      "investigation plan",
      "evidence inventory",
      "timeline",
      "findings",
      "conflicts",
      "recommendations",
      "citation-backed report",
    ],
    templateId: template?.id ?? null,
  };
}
