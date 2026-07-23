import type { LicenseEntitlement } from "./types.js";

export interface EntitlementResult {
  allowed: boolean;
  reason: string;
}

/** Evaluate edition and pack entitlement for an org. */
export function evaluateEntitlement(
  entitlement: LicenseEntitlement,
  requiredEdition: string,
  requiredPack?: string,
): EntitlementResult {
  if (entitlement.expiresAt) {
    const expires = new Date(entitlement.expiresAt);
    if (!Number.isNaN(expires.getTime()) && expires.getTime() < Date.now()) {
      return { allowed: false, reason: "License expired" };
    }
  }

  if (entitlement.edition !== requiredEdition && requiredEdition !== "enterprise") {
    if (entitlement.edition !== "enterprise") {
      return {
        allowed: false,
        reason: `Edition '${entitlement.edition}' does not satisfy required '${requiredEdition}'`,
      };
    }
  }

  if (requiredPack && !entitlement.packs.includes(requiredPack)) {
    return { allowed: false, reason: `Pack '${requiredPack}' not licensed` };
  }

  return { allowed: true, reason: "Entitlement satisfied" };
}

/** Check seat availability for new user assignment. */
export function seatCheck(entitlement: LicenseEntitlement, additionalSeats = 1): EntitlementResult {
  const projected = entitlement.seatsUsed + additionalSeats;
  if (projected > entitlement.seatLimit) {
    return {
      allowed: false,
      reason: `Seat limit exceeded (${projected}/${entitlement.seatLimit})`,
    };
  }
  return {
    allowed: true,
    reason: `Seats available (${projected}/${entitlement.seatLimit})`,
  };
}

/** Check if domain pack is licensed. */
export function packLicense(entitlement: LicenseEntitlement, packId: string): EntitlementResult {
  if (!entitlement.packs.includes(packId)) {
    return { allowed: false, reason: `Pack '${packId}' not in license` };
  }
  return { allowed: true, reason: `Pack '${packId}' licensed` };
}
