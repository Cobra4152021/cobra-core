import type { CkeStore } from "../db/store.js";
import { assertReadable, filterReadable, projectScopedOrThrow } from "../permissions/index.js";
import type { AuthContext, Entity, EntityType, Visibility } from "../types.js";
import { clampConfidence, newId, now } from "../util.js";

const PATTERNS: Array<{ type: EntityType; re: RegExp }> = [
  { type: "technology", re: /\b(GPT-OSS|SigLIP|Qwen|Claude|Gemma|Benchmark Lab|Evidence Vault|Cloudflare|D1|Workers)\b/gi },
  { type: "project", re: /\b(Cobra|Hidden Grid|Argentina Farm|Union Book|Leadership Series|King Cobra|CKE)\b/g },
  { type: "organization", re: /\b(OpenAI|Google|Anthropic|Cobra Core|Dynamic Mining)\b/g },
  { type: "location", re: /\b(Argentina|Dubai|UTC)\b/g },
];

function normalizeName(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

export class EntityEngine {
  constructor(private store: CkeStore) {}

  upsert(
    ctx: AuthContext,
    input: {
      type: EntityType;
      canonicalName: string;
      aliases?: string[];
      description?: string;
      projectId?: string | null;
      confidence?: number;
      visibility?: Visibility;
    },
  ): Entity {
    projectScopedOrThrow(ctx, input.projectId);
    const name = normalizeName(input.canonicalName);
    const existing = [...this.store.entities.values()].find(
      (e) =>
        e.orgId === ctx.orgId &&
        e.projectId === (input.projectId ?? null) &&
        e.canonicalName.toLowerCase() === name.toLowerCase(),
    );
    const ts = now();
    if (existing) {
      existing.aliases = Array.from(new Set([...existing.aliases, ...(input.aliases ?? [])]));
      if (input.description) existing.description = input.description;
      existing.confidence = Math.max(existing.confidence, clampConfidence(input.confidence ?? 0.5));
      existing.updatedAt = ts;
      return existing;
    }
    const ent: Entity = {
      id: newId("ent"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      type: input.type,
      canonicalName: name,
      aliases: input.aliases ?? [],
      description: input.description ?? null,
      confidence: clampConfidence(input.confidence ?? 0.55),
      permissions: {
        orgId: ctx.orgId,
        projectId: input.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: input.visibility ?? (input.projectId ? "project" : "organization"),
      },
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.entities.set(ent.id, ent);
    return ent;
  }

  get(ctx: AuthContext, id: string): Entity | null {
    const e = this.store.entities.get(id);
    if (!e || e.orgId !== ctx.orgId) return null;
    assertReadable(ctx, e.permissions);
    return e;
  }

  list(ctx: AuthContext, opts: { projectId?: string | null; type?: EntityType } = {}): Entity[] {
    const rows = [...this.store.entities.values()].filter((e) => {
      if (e.orgId !== ctx.orgId) return false;
      if (opts.projectId != null && e.projectId !== opts.projectId) return false;
      if (opts.type && e.type !== opts.type) return false;
      return true;
    });
    return filterReadable(ctx, rows);
  }

  /** Deterministic heuristic extractor — LLM extraction can replace later. */
  extractFromText(ctx: AuthContext, text: string, projectId?: string | null): Entity[] {
    const found: Entity[] = [];
    const seen = new Set<string>();
    for (const { type, re } of PATTERNS) {
      re.lastIndex = 0;
      let m: RegExpExecArray | null;
      while ((m = re.exec(text))) {
        const name = normalizeName(m[0]);
        const key = `${type}:${name.toLowerCase()}`;
        if (seen.has(key)) continue;
        seen.add(key);
        found.push(
          this.upsert(ctx, {
            type,
            canonicalName: name,
            projectId,
            confidence: 0.7,
            description: `Extracted as ${type} from text`,
          }),
        );
      }
    }
    return found;
  }

  findDuplicates(ctx: AuthContext, projectId?: string | null): Array<[Entity, Entity]> {
    const list = this.list(ctx, { projectId });
    const pairs: Array<[Entity, Entity]> = [];
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i];
        const b = list[j];
        if (a.type !== b.type) continue;
        const names = new Set(
          [a.canonicalName, ...a.aliases, b.canonicalName, ...b.aliases].map((x) => x.toLowerCase()),
        );
        if (names.size < a.aliases.length + b.aliases.length + 2) {
          pairs.push([a, b]);
        } else if (a.canonicalName.toLowerCase() === b.canonicalName.toLowerCase()) {
          pairs.push([a, b]);
        }
      }
    }
    return pairs;
  }
}
