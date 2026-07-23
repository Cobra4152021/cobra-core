import { createHash, randomUUID } from "node:crypto";

export function newId(prefix = ""): string {
  const id = randomUUID();
  return prefix ? `${prefix}_${id}` : id;
}

export function now(): number {
  return Date.now();
}

export function contentHash(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}

export function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 64);
}

export function clampConfidence(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}
