/** Article knowledge helpers (KC-006) — deterministic sectioning. */

export type LaborArticleTopic =
  | "recognition"
  | "union_rights"
  | "management_rights"
  | "hours"
  | "overtime"
  | "leave"
  | "scheduling"
  | "discipline"
  | "promotions"
  | "transfers"
  | "benefits"
  | "grievance_procedure"
  | "arbitration"
  | "other";

export interface LaborArticle {
  id: string;
  contractId: string;
  number: string;
  title: string;
  topic: LaborArticleTopic;
  text: string;
  citations: string[];
}

const TOPIC_HINTS: { re: RegExp; topic: LaborArticleTopic }[] = [
  { re: /recognition/i, topic: "recognition" },
  { re: /union\s*rights|steward/i, topic: "union_rights" },
  { re: /management\s*rights/i, topic: "management_rights" },
  { re: /hours\s*of\s*work|work\s*day|workweek/i, topic: "hours" },
  { re: /overtime|holdover/i, topic: "overtime" },
  { re: /leave|vacation|sick/i, topic: "leave" },
  { re: /schedul|shift\s*bid|seniority/i, topic: "scheduling" },
  { re: /disciplin|just\s*cause/i, topic: "discipline" },
  { re: /promot/i, topic: "promotions" },
  { re: /transfer/i, topic: "transfers" },
  { re: /benefit|insurance|pension/i, topic: "benefits" },
  { re: /grievance/i, topic: "grievance_procedure" },
  { re: /arbitration/i, topic: "arbitration" },
];

export function inferArticleTopic(title: string, text = ""): LaborArticleTopic {
  const blob = `${title}\n${text}`;
  for (const h of TOPIC_HINTS) {
    if (h.re.test(blob)) return h.topic;
  }
  return "other";
}

/**
 * Split contract text on common article headings.
 * Deterministic; does not claim legal article boundaries.
 */
export function parseArticlesFromText(contractId: string, bodyText: string): LaborArticle[] {
  const text = String(bodyText ?? "").replace(/\r\n/g, "\n").trim();
  if (!text) return [];

  const parts = text.split(/\n(?=(?:ARTICLE|Article|ART\.)\s+[A-Z0-9.IVXLC]+)/);
  const articles: LaborArticle[] = [];
  let idx = 0;
  for (const part of parts) {
    const chunk = part.trim();
    if (!chunk) continue;
    const header = chunk.split("\n")[0] ?? `Article ${idx + 1}`;
    const m = header.match(/(?:ARTICLE|Article|ART\.)\s+([A-Z0-9.IVXLC]+)[:.\s-]*(.*)$/i);
    const number = m?.[1]?.trim() || String(idx + 1);
    const title = (m?.[2] || header).trim() || `Article ${number}`;
    const id = `${contractId}_art_${number.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase()}_${idx}`;
    articles.push({
      id,
      contractId,
      number,
      title,
      topic: inferArticleTopic(title, chunk),
      text: chunk,
      citations: [],
    });
    idx += 1;
  }
  if (articles.length === 0) {
    articles.push({
      id: `${contractId}_art_body`,
      contractId,
      number: "1",
      title: "Body",
      topic: "other",
      text,
      citations: [],
    });
  }
  return articles;
}

export function searchArticles(articles: LaborArticle[], query: string): LaborArticle[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return articles.filter(
    (a) =>
      a.title.toLowerCase().includes(q) ||
      a.number.toLowerCase().includes(q) ||
      a.topic.includes(q.replace(/\s+/g, "_") as LaborArticleTopic) ||
      a.text.toLowerCase().includes(q),
  );
}
