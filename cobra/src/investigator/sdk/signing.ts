/** KC-008 — package checksum and signed metadata (alpha1, HMAC-ready structure). */

import { createHash } from "node:crypto";
import type { PackSigningStatus, SignedPackageMeta } from "./types.js";

export function checksumSha256Hex(payload: string | Buffer): string {
  return createHash("sha256").update(payload).digest("hex");
}

export function verifyChecksum(payload: string | Buffer, expectedHex: string): boolean {
  const actual = checksumSha256Hex(payload);
  return actual === expectedHex.trim().toLowerCase();
}

export interface BuildSignedPackageMetaInput {
  packId: string;
  publisher: string;
  payload: string | Buffer;
  versionHistory?: string[];
  signingStatus?: PackSigningStatus;
  /** Placeholder for future HMAC/signature verification. */
  signature?: string | null;
}

/** Build signed package metadata. Alpha1: checksum only; signature is a placeholder unless verified. */
export function buildSignedPackageMeta(input: BuildSignedPackageMetaInput): SignedPackageMeta {
  const signingStatus = input.signingStatus ?? "unsigned";
  const checksum = checksumSha256Hex(input.payload);

  let signature: string | null = input.signature ?? null;
  if (signingStatus === "builtin") {
    signature = null;
  } else if (signingStatus === "unsigned") {
    signature = null;
  } else if (signingStatus === "verified" && !signature) {
    signature = "hmac-placeholder";
  }

  return {
    packId: input.packId,
    publisher: input.publisher,
    signature,
    checksumSha256: checksum,
    versionHistory: input.versionHistory ?? [],
    signingStatus,
  };
}
