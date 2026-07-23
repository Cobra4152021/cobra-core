/** KC-008 — pure install/upgrade/disable/remove planning (no I/O). */

import { extractPermissionIds } from "./sandbox.js";
import type {
  CatalogPackRef,
  CompatibilityResult,
  DomainPackRegistration,
  InstalledPackRef,
  InstallPlan,
  PlanInstallResult,
  PlanUpgradeResult,
} from "./types.js";

function parseSemver(version: string): [number, number, number] | null {
  const m = /^(\d+)\.(\d+)\.(\d+)/.exec(version.trim());
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

export function compareSemver(a: string, b: string): number {
  const pa = parseSemver(a);
  const pb = parseSemver(b);
  if (!pa || !pb) return 0;
  for (let i = 0; i < 3; i++) {
    if (pa[i]! < pb[i]!) return -1;
    if (pa[i]! > pb[i]!) return 1;
  }
  return 0;
}

function extractFeatureFlagKeys(registration: DomainPackRegistration): string[] {
  return registration.manifest.featureFlags.map((f) =>
    typeof f === "string" ? f.trim() : f.key.trim(),
  );
}

export function compatibilityCheck(
  manifest: DomainPackRegistration["manifest"],
  cobraVersion: string,
  installed: InstalledPackRef[],
): CompatibilityResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (compareSemver(cobraVersion, manifest.minimumCobraVersion) < 0) {
    errors.push(
      `Cobra ${cobraVersion} is below minimum ${manifest.minimumCobraVersion} for ${manifest.id}`,
    );
  }

  for (const dep of manifest.dependencies) {
    if (dep.optional) continue;
    const found = installed.find((p) => p.packId === dep.packId && p.enabled);
    if (!found) {
      errors.push(`Required dependency not installed: ${dep.packId}`);
    } else if (dep.versionRange) {
      const min = dep.versionRange.replace(/^>=/, "").trim();
      if (min && compareSemver(found.version, min) < 0) {
        errors.push(`Dependency ${dep.packId}@${found.version} below ${dep.versionRange}`);
      }
    }
  }

  if (manifest.supportedEditions.length === 0) {
    warnings.push(`${manifest.id} declares no supported editions`);
  }

  return { compatible: errors.length === 0, errors, warnings };
}

export function resolveDependencies(
  catalog: CatalogPackRef[],
  packId: string,
  installed: InstalledPackRef[],
): { resolved: string[]; missing: string[]; warnings: string[] } {
  const byId = new Map(catalog.map((c) => [c.packId, c.registration]));
  const resolved: string[] = [];
  const missing: string[] = [];
  const warnings: string[] = [];
  const visiting = new Set<string>();

  function walk(id: string): void {
    if (visiting.has(id)) {
      warnings.push(`Circular dependency detected at ${id}`);
      return;
    }
    visiting.add(id);

    const reg = byId.get(id);
    if (!reg) {
      if (!installed.some((p) => p.packId === id && p.enabled)) {
        missing.push(id);
      }
      visiting.delete(id);
      return;
    }

    for (const dep of reg.manifest.dependencies) {
      if (dep.optional) continue;
      const alreadyInstalled = installed.some((p) => p.packId === dep.packId && p.enabled);
      if (!alreadyInstalled && !resolved.includes(dep.packId)) {
        walk(dep.packId);
        if (!missing.includes(dep.packId)) {
          resolved.push(dep.packId);
        }
      }
    }

    if (!resolved.includes(id) && !installed.some((p) => p.packId === id)) {
      resolved.push(id);
    }

    visiting.delete(id);
  }

  walk(packId);
  return { resolved, missing, warnings };
}

export function planInstall(
  catalogPack: DomainPackRegistration,
  installed: InstalledPackRef[],
  cobraVersion: string,
  catalog: CatalogPackRef[] = [{ packId: catalogPack.packId, registration: catalogPack }],
): PlanInstallResult {
  const compatibility = compatibilityCheck(catalogPack.manifest, cobraVersion, installed);
  if (!compatibility.compatible) {
    return { success: false, compatibility };
  }

  const existing = installed.find((p) => p.packId === catalogPack.packId);
  if (existing?.enabled) {
    return {
      success: false,
      compatibility: {
        compatible: false,
        errors: [`Pack already installed: ${catalogPack.packId}`],
        warnings: compatibility.warnings,
      },
    };
  }

  const { resolved, missing, warnings: depWarnings } = resolveDependencies(
    catalog,
    catalogPack.packId,
    installed,
  );

  if (missing.length) {
    return {
      success: false,
      compatibility: {
        compatible: false,
        errors: missing.map((id) => `Missing dependency in catalog: ${id}`),
        warnings: [...compatibility.warnings, ...depWarnings],
      },
    };
  }

  const dependenciesToInstall = resolved.filter((id) => id !== catalogPack.packId);

  const plan: InstallPlan = {
    action: "install",
    packId: catalogPack.packId,
    version: catalogPack.manifest.version,
    dependenciesToInstall,
    permissionsGranted: extractPermissionIds(catalogPack.manifest),
    featureFlagsEnabled: extractFeatureFlagKeys(catalogPack),
    warnings: [...compatibility.warnings, ...depWarnings],
  };

  return { success: true, plan };
}

export function planUpgrade(
  catalogPack: DomainPackRegistration,
  installed: InstalledPackRef[],
  cobraVersion: string,
): PlanUpgradeResult {
  const existing = installed.find((p) => p.packId === catalogPack.packId);
  if (!existing) {
    return {
      success: false,
      compatibility: {
        compatible: false,
        errors: [`Pack not installed: ${catalogPack.packId}`],
        warnings: [],
      },
    };
  }

  const compatibility = compatibilityCheck(catalogPack.manifest, cobraVersion, installed);
  if (!compatibility.compatible) {
    return { success: false, compatibility };
  }

  if (compareSemver(catalogPack.manifest.version, existing.version) <= 0) {
    return {
      success: false,
      compatibility: {
        compatible: false,
        errors: [`Catalog version ${catalogPack.manifest.version} is not newer than ${existing.version}`],
        warnings: compatibility.warnings,
      },
    };
  }

  const plan: InstallPlan = {
    action: "upgrade",
    packId: catalogPack.packId,
    version: catalogPack.manifest.version,
    dependenciesToInstall: [],
    permissionsGranted: extractPermissionIds(catalogPack.manifest),
    featureFlagsEnabled: extractFeatureFlagKeys(catalogPack),
    warnings: compatibility.warnings,
  };

  return { success: true, plan };
}

export function planDisable(
  packId: string,
  installed: InstalledPackRef[],
): InstallPlan | null {
  const existing = installed.find((p) => p.packId === packId);
  if (!existing?.enabled) return null;

  return {
    action: "disable",
    packId,
    version: existing.version,
    dependenciesToInstall: [],
    permissionsGranted: [],
    featureFlagsEnabled: [],
    warnings: [`Disabling ${packId} may affect dependent features.`],
  };
}

export function planRemove(
  packId: string,
  installed: InstalledPackRef[],
  dependents?: string[],
): InstallPlan | null {
  const existing = installed.find((p) => p.packId === packId);
  if (!existing) return null;

  const warnings: string[] = [];
  if (dependents?.length) {
    warnings.push(`Remove blocked or requires removing dependents first: ${dependents.join(", ")}`);
  }

  return {
    action: "remove",
    packId,
    version: existing.version,
    dependenciesToInstall: [],
    permissionsGranted: [],
    featureFlagsEnabled: [],
    warnings,
  };
}

export function detectUpdates(
  installed: InstalledPackRef[],
  catalog: CatalogPackRef[],
): Array<{ packId: string; currentVersion: string; availableVersion: string }> {
  const updates: Array<{ packId: string; currentVersion: string; availableVersion: string }> = [];
  for (const inst of installed) {
    const cat = catalog.find((c) => c.packId === inst.packId);
    if (!cat) continue;
    const available = cat.registration.manifest.version;
    if (compareSemver(available, inst.version) > 0) {
      updates.push({
        packId: inst.packId,
        currentVersion: inst.version,
        availableVersion: available,
      });
    }
  }
  return updates;
}
