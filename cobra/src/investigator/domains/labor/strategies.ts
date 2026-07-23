/** Labor strategy mapping (KC-006). */

import { getLaborTemplate, isLaborTemplateId } from "./templates.js";

export function strategyForLaborTemplate(templateId: string | null | undefined): string | null {
  return getLaborTemplate(templateId)?.strategyId ?? null;
}

export function isLaborDomainTemplate(templateId: string | null | undefined): boolean {
  return isLaborTemplateId(templateId);
}
