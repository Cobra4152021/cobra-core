/** Contract comparison (KC-006) — deterministic text diffs. */

export type ContractChangeKind =
  | "added"
  | "removed"
  | "modified"
  | "renumbered"
  | "unchanged";

export interface ContractArticleDiff {
  kind: ContractChangeKind;
  oldNumber: string | null;
  newNumber: string | null;
  oldTitle: string | null;
  newTitle: string | null;
  summary: string;
  categoryHint:
    | "benefit"
    | "leave"
    | "staffing"
    | "discipline"
    | "wage"
    | "overtime"
    | "promotion"
    | "other";
}

export interface ContractComparisonResult {
  oldContractId: string;
  newContractId: string;
  diffs: ContractArticleDiff[];
  disclaimer: string;
}

function hintCategory(title: string): ContractArticleDiff["categoryHint"] {
  const t = title.toLowerCase();
  if (/benefit|insurance|pension/.test(t)) return "benefit";
  if (/leave|vacation|sick/.test(t)) return "leave";
  if (/staff|vacanc|minimum/.test(t)) return "staffing";
  if (/disciplin/.test(t)) return "discipline";
  if (/wage|salary|pay\b/.test(t)) return "wage";
  if (/overtime|holdover/.test(t)) return "overtime";
  if (/promot/.test(t)) return "promotion";
  return "other";
}

function norm(s: string): string {
  return s.toLowerCase().replace(/\s+/g, " ").trim();
}

export function compareContractArticles(
  oldContractId: string,
  newContractId: string,
  oldArticles: Array<{ number: string; title: string; text: string }>,
  newArticles: Array<{ number: string; title: string; text: string }>,
): ContractComparisonResult {
  const diffs: ContractArticleDiff[] = [];
  const newByTitle = new Map(newArticles.map((a) => [norm(a.title), a]));
  const usedNew = new Set<string>();

  for (const oldA of oldArticles) {
    const key = norm(oldA.title);
    const match = newByTitle.get(key);
    if (!match) {
      // try number match
      const byNum = newArticles.find((n) => n.number === oldA.number && !usedNew.has(n.number + norm(n.title)));
      if (!byNum) {
        diffs.push({
          kind: "removed",
          oldNumber: oldA.number,
          newNumber: null,
          oldTitle: oldA.title,
          newTitle: null,
          summary: `Removed: ${oldA.title}`,
          categoryHint: hintCategory(oldA.title),
        });
        continue;
      }
      usedNew.add(byNum.number + norm(byNum.title));
      if (norm(byNum.text) === norm(oldA.text)) {
        if (byNum.number !== oldA.number) {
          diffs.push({
            kind: "renumbered",
            oldNumber: oldA.number,
            newNumber: byNum.number,
            oldTitle: oldA.title,
            newTitle: byNum.title,
            summary: `Renumbered ${oldA.number} → ${byNum.number}`,
            categoryHint: hintCategory(oldA.title),
          });
        } else {
          diffs.push({
            kind: "unchanged",
            oldNumber: oldA.number,
            newNumber: byNum.number,
            oldTitle: oldA.title,
            newTitle: byNum.title,
            summary: "Unchanged",
            categoryHint: hintCategory(oldA.title),
          });
        }
      } else {
        diffs.push({
          kind: "modified",
          oldNumber: oldA.number,
          newNumber: byNum.number,
          oldTitle: oldA.title,
          newTitle: byNum.title,
          summary: `Modified language in ${oldA.title}`,
          categoryHint: hintCategory(oldA.title),
        });
      }
      continue;
    }
    usedNew.add(match.number + norm(match.title));
    if (norm(match.text) === norm(oldA.text)) {
      diffs.push({
        kind: match.number !== oldA.number ? "renumbered" : "unchanged",
        oldNumber: oldA.number,
        newNumber: match.number,
        oldTitle: oldA.title,
        newTitle: match.title,
        summary:
          match.number !== oldA.number
            ? `Renumbered ${oldA.number} → ${match.number}`
            : "Unchanged",
        categoryHint: hintCategory(oldA.title),
      });
    } else {
      diffs.push({
        kind: "modified",
        oldNumber: oldA.number,
        newNumber: match.number,
        oldTitle: oldA.title,
        newTitle: match.title,
        summary: `Modified language in ${oldA.title}`,
        categoryHint: hintCategory(oldA.title),
      });
    }
  }

  for (const newA of newArticles) {
    const key = newA.number + norm(newA.title);
    if (usedNew.has(key)) continue;
    const titleUsed = oldArticles.some((o) => norm(o.title) === norm(newA.title));
    if (titleUsed) continue;
    diffs.push({
      kind: "added",
      oldNumber: null,
      newNumber: newA.number,
      oldTitle: null,
      newTitle: newA.title,
      summary: `Added: ${newA.title}`,
      categoryHint: hintCategory(newA.title),
    });
  }

  return {
    oldContractId,
    newContractId,
    diffs,
    disclaimer:
      "Text comparison only. Not a legal interpretation, breach finding, or bargaining recommendation.",
  };
}
