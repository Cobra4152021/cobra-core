/** Pattern investigator (KC-006) — evidence-supported clustering only. */

export type LaborPatternCategory =
  | "contract_dispute"
  | "staffing_issue"
  | "discipline_pattern"
  | "promotion_issue"
  | "policy_change"
  | "grievance_category"
  | "overtime_complaint"
  | "other";

export interface LaborPatternHit {
  category: LaborPatternCategory;
  label: string;
  count: number;
  exampleIds: string[];
  note: string;
}

export function detectLaborPatterns(
  items: Array<{ id: string; text: string; category?: string }>,
): LaborPatternHit[] {
  const buckets: Record<LaborPatternCategory, string[]> = {
    contract_dispute: [],
    staffing_issue: [],
    discipline_pattern: [],
    promotion_issue: [],
    policy_change: [],
    grievance_category: [],
    overtime_complaint: [],
    other: [],
  };

  for (const item of items) {
    const t = `${item.category ?? ""} ${item.text}`.toLowerCase();
    let cat: LaborPatternCategory = "other";
    // Overtime before generic grievance so OT grievances cluster as overtime_complaint.
    if (/overtime|holdover|\bot\b/.test(t)) cat = "overtime_complaint";
    else if (/grievance/.test(t)) cat = "grievance_category";
    else if (/staff|vacanc|minimum\s*staff/.test(t)) cat = "staffing_issue";
    else if (/disciplin/.test(t)) cat = "discipline_pattern";
    else if (/promot/.test(t)) cat = "promotion_issue";
    else if (/policy|directive/.test(t)) cat = "policy_change";
    else if (/contract|mou|article|cba/.test(t)) cat = "contract_dispute";
    buckets[cat].push(item.id);
  }

  const hits: LaborPatternHit[] = [];
  for (const [category, ids] of Object.entries(buckets) as [LaborPatternCategory, string[]][]) {
    if (ids.length < 2) continue;
    hits.push({
      category,
      label: category.replace(/_/g, " "),
      count: ids.length,
      exampleIds: ids.slice(0, 5),
      note: "Evidence-supported recurrence only. Does not infer wrongdoing or liability.",
    });
  }
  return hits;
}
