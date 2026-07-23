/** KC-008 — marketplace catalog builder. */

import type {
  DomainPackRegistration,
  MarketplaceCatalogEntry,
  MarketplaceCategory,
  MarketplaceEntryStatus,
} from "./types.js";
import { extractPermissionIds } from "./sandbox.js";

export interface BuildMarketplaceCatalogInput {
  packs: DomainPackRegistration[];
  installedPackIds?: string[];
  disabledPackIds?: string[];
}

function resolveStatus(
  packId: string,
  installed: Set<string>,
  disabled: Set<string>,
): MarketplaceEntryStatus {
  if (disabled.has(packId)) return "disabled";
  if (installed.has(packId)) return "installed";
  return "available";
}

function inferCategory(pack: DomainPackRegistration): MarketplaceCategory {
  if (pack.category) return pack.category;
  if (pack.packId.includes("government")) return "Government";
  if (pack.packId.includes("labor")) return "Labor";
  if (pack.packId.includes("studio")) return "Enterprise";
  return "Community";
}

/** Build marketplace catalog entries from registered packs. */
export function buildMarketplaceCatalog(
  input: BuildMarketplaceCatalogInput | DomainPackRegistration[],
): MarketplaceCatalogEntry[] {
  const packs = Array.isArray(input) ? input : input.packs;
  const installed = new Set(
    Array.isArray(input) ? [] : (input.installedPackIds ?? []),
  );
  const disabled = new Set(
    Array.isArray(input) ? [] : (input.disabledPackIds ?? []),
  );

  return packs.map((pack) => ({
    packId: pack.packId,
    name: pack.manifest.name,
    version: pack.manifest.version,
    author: pack.manifest.author,
    description: pack.manifest.description ?? "",
    category: inferCategory(pack),
    status: resolveStatus(pack.packId, installed, disabled),
    signingStatus: pack.signingStatus,
    templateCount: pack.templates.length,
    metricCount: pack.metrics.length,
    permissions: extractPermissionIds(pack.manifest),
  }));
}

export const MARKETPLACE_CATEGORIES: readonly MarketplaceCategory[] = [
  "Government",
  "Labor",
  "Research",
  "Enterprise",
  "Community",
] as const;
