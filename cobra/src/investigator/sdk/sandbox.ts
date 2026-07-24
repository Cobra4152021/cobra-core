/** KC-008 — sandbox rules and permission allowlist enforcement. */

import type { PluginManifest } from "./types.js";

/** Documented constraints plugins cannot bypass (alpha1 reference). */
export const SANDBOX_RULES = {
  noDirectDatabaseAccess: "Plugins cannot open raw database connections outside Cobra APIs.",
  noFilesystemWrite: "Plugins cannot write to host filesystem except via approved vault APIs.",
  noNetworkEgress: "Plugins cannot initiate arbitrary network egress without explicit permission.",
  noProcessSpawn: "Plugins cannot spawn subprocesses or shell commands.",
  noSecretAccess: "Plugins cannot read environment secrets or session tokens directly.",
  noAuthBypass: "Plugins cannot disable auth, CSRF, or org-boundary checks.",
  permissionAllowlist: "All declared permissions must match the marketplace allowlist patterns.",
  manifestRequired: "Every pack must ship a valid cobra-domain.json manifest.",
  signingRecommended: "Community packs should be signed before production install.",
} as const;

/** Permission patterns permitted in alpha1 marketplace packs. */
export const PERMISSION_ALLOWLIST: readonly string[] = [
  "marketplace.view",
  "government.*",
  "labor.*",
  "research.*",
  "studio.*",
  "use_investigator.plan",
  "use_investigator.report",
  "use_investigator.metrics",
  "use_investigator.templates",
  "use_investigator.evidence",
];

function permissionMatchesAllowlist(permission: string): boolean {
  const p = permission.trim();
  for (const pattern of PERMISSION_ALLOWLIST) {
    if (pattern.endsWith(".*")) {
      const prefix = pattern.slice(0, -1);
      if (p.startsWith(prefix)) return true;
    } else if (p === pattern) {
      return true;
    }
  }
  return false;
}

export function extractPermissionIds(manifest: PluginManifest): string[] {
  return manifest.permissions.map((entry) =>
    typeof entry === "string" ? entry.trim() : entry.id.trim(),
  );
}

/** Reject manifests declaring permissions outside the allowlist. Throws on violation. */
export function assertSandboxSafe(manifest: PluginManifest): void {
  const denied: string[] = [];
  for (const id of extractPermissionIds(manifest)) {
    if (!permissionMatchesAllowlist(id)) {
      denied.push(id);
    }
  }
  if (denied.length) {
    throw new Error(
      `Sandbox violation: permissions not allowed: ${denied.join(", ")}. ` +
        `Allowed patterns: ${PERMISSION_ALLOWLIST.join(", ")}`,
    );
  }
}

/** Non-throwing variant returning compatibility-style result. */
export function checkSandboxSafe(manifest: PluginManifest): { safe: boolean; denied: string[] } {
  const denied = extractPermissionIds(manifest).filter((id) => !permissionMatchesAllowlist(id));
  return { safe: denied.length === 0, denied };
}
