/** Government strategy selection hints (KC-005). */

import type { StrategyId } from "../../strategy.js";
import { getGovernmentTemplate, isGovernmentTemplateId } from "./templates.js";

export function strategyForGovernmentTemplate(templateId: string | null | undefined): StrategyId | null {
  const t = getGovernmentTemplate(templateId);
  return (t?.strategyId as StrategyId | undefined) ?? null;
}

export function selectGovernmentStrategyHint(input: {
  title: string;
  description?: string | null;
  templateId?: string | null;
}): StrategyId | null {
  if (isGovernmentTemplateId(input.templateId)) {
    return strategyForGovernmentTemplate(input.templateId);
  }
  const prompt = `${input.title}\n${input.description ?? ""}`;
  if (/overtime|ot\b/i.test(prompt)) return "staffing_analysis";
  if (/vacanc|staffing|fte|headcount/i.test(prompt)) return "staffing_analysis";
  if (/budget|variance|expenditure/i.test(prompt)) return "budget_audit";
  if (/grant/i.test(prompt)) return "compliance_investigation";
  if (/policy|procedure/i.test(prompt)) return "policy_review";
  if (/fleet|equipment|lifecycle/i.test(prompt)) return "technical_root_cause";
  if (/training|certification/i.test(prompt)) return "compliance_investigation";
  if (/workload|deployment|calls for service/i.test(prompt)) return "staffing_analysis";
  if (/mou|collective|labor agreement|contract impact/i.test(prompt)) return "union_contract_review";
  if (/procurement|purchase order|solicitation/i.test(prompt)) return "compliance_investigation";
  return null;
}
