/** KC-008 — parse and validate `cobra-domain.json` manifest shape. */

import type { PackDependency, PackFeatureFlag, PackPermission, PluginManifest } from "./types.js";

const SEMVER_PATTERN = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;

export interface ManifestParseSuccess {
  ok: true;
  manifest: PluginManifest;
}

export interface ManifestParseFailure {
  ok: false;
  errors: string[];
}

export type ManifestParseResult = ManifestParseSuccess | ManifestParseFailure;

const REQUIRED_STRING_FIELDS = [
  "id",
  "name",
  "version",
  "author",
  "license",
  "minimumCobraVersion",
] as const;

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function isSemverish(value: string): boolean {
  return SEMVER_PATTERN.test(value.trim());
}

function normalizeStringArray(value: unknown, field: string, errors: string[]): string[] {
  if (!Array.isArray(value)) {
    errors.push(`${field} must be an array`);
    return [];
  }
  const out: string[] = [];
  for (const item of value) {
    if (!isNonEmptyString(item)) {
      errors.push(`${field} entries must be non-empty strings`);
      continue;
    }
    out.push(item.trim());
  }
  return out;
}

function normalizeDependencies(value: unknown, errors: string[]): PackDependency[] {
  if (!Array.isArray(value)) {
    errors.push("dependencies must be an array");
    return [];
  }
  const out: PackDependency[] = [];
  for (const item of value) {
    if (!item || typeof item !== "object") {
      errors.push("dependencies entries must be objects");
      continue;
    }
    const rec = item as Record<string, unknown>;
    if (!isNonEmptyString(rec.packId)) {
      errors.push("dependencies.packId is required");
      continue;
    }
    out.push({
      packId: rec.packId.trim(),
      versionRange: isNonEmptyString(rec.versionRange) ? rec.versionRange.trim() : undefined,
      optional: rec.optional === true,
    });
  }
  return out;
}

function normalizePermissions(value: unknown, errors: string[]): Array<PackPermission | string> {
  if (!Array.isArray(value)) {
    errors.push("permissions must be an array");
    return [];
  }
  const out: Array<PackPermission | string> = [];
  for (const item of value) {
    if (isNonEmptyString(item)) {
      out.push(item.trim());
      continue;
    }
    if (item && typeof item === "object" && isNonEmptyString((item as PackPermission).id)) {
      out.push({
        id: (item as PackPermission).id.trim(),
        description:
          typeof (item as PackPermission).description === "string"
            ? (item as PackPermission).description
            : undefined,
      });
      continue;
    }
    errors.push("permissions entries must be strings or { id, description? } objects");
  }
  return out;
}

function normalizeFeatureFlags(value: unknown, errors: string[]): Array<PackFeatureFlag | string> {
  if (!Array.isArray(value)) {
    errors.push("featureFlags must be an array");
    return [];
  }
  const out: Array<PackFeatureFlag | string> = [];
  for (const item of value) {
    if (isNonEmptyString(item)) {
      out.push(item.trim());
      continue;
    }
    if (item && typeof item === "object" && isNonEmptyString((item as PackFeatureFlag).key)) {
      out.push({
        key: (item as PackFeatureFlag).key.trim(),
        defaultEnabled:
          typeof (item as PackFeatureFlag).defaultEnabled === "boolean"
            ? (item as PackFeatureFlag).defaultEnabled
            : undefined,
        description:
          typeof (item as PackFeatureFlag).description === "string"
            ? (item as PackFeatureFlag).description
            : undefined,
      });
      continue;
    }
    errors.push("featureFlags entries must be strings or { key, defaultEnabled?, description? } objects");
  }
  return out;
}

/** Parse and validate raw JSON into a PluginManifest. Fails closed on any invalid field. */
export function parseManifest(raw: unknown): ManifestParseResult {
  const errors: string[] = [];

  if (!raw || typeof raw !== "object") {
    return { ok: false, errors: ["manifest must be a JSON object"] };
  }

  const rec = raw as Record<string, unknown>;

  for (const field of REQUIRED_STRING_FIELDS) {
    if (!isNonEmptyString(rec[field])) {
      errors.push(`${field} is required and must be a non-empty string`);
    }
  }

  if (errors.length) {
    return { ok: false, errors };
  }

  const version = String(rec.version).trim();
  const minimumCobraVersion = String(rec.minimumCobraVersion).trim();

  if (!isSemverish(version)) {
    errors.push("version must be semver-ish (x.y.z)");
  }
  if (!isSemverish(minimumCobraVersion)) {
    errors.push("minimumCobraVersion must be semver-ish (x.y.z)");
  }

  const supportedEditions = normalizeStringArray(rec.supportedEditions, "supportedEditions", errors);
  if (supportedEditions.length === 0) {
    errors.push("supportedEditions must contain at least one edition");
  }

  const dependencies = normalizeDependencies(rec.dependencies ?? [], errors);
  const permissions = normalizePermissions(rec.permissions ?? [], errors);
  const featureFlags = normalizeFeatureFlags(rec.featureFlags ?? [], errors);
  const migrationList = normalizeStringArray(rec.migrationList ?? [], "migrationList", errors);

  if (rec.description !== undefined && rec.description !== null) {
    if (!isNonEmptyString(rec.description)) {
      errors.push("description must be a non-empty string when provided");
    }
  }

  if (errors.length) {
    return { ok: false, errors };
  }

  const manifest: PluginManifest = {
    id: String(rec.id).trim(),
    name: String(rec.name).trim(),
    version,
    author: String(rec.author).trim(),
    license: String(rec.license).trim(),
    minimumCobraVersion,
    supportedEditions,
    dependencies,
    permissions,
    featureFlags,
    migrationList,
    description: isNonEmptyString(rec.description) ? rec.description.trim() : undefined,
  };

  return { ok: true, manifest };
}

/** Validate an already-constructed manifest (e.g. built-in packs). */
export function validateManifest(manifest: PluginManifest): ManifestParseResult {
  return parseManifest(manifest);
}
