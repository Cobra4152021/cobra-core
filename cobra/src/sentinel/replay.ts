import type { ReplayToken } from "./types.js";
import { newOpaqueId } from "./ids.js";

export function buildReplayToken(input: {
  randomHex: string;
  featureFlags: Record<string, boolean | string>;
  browser?: string | null;
  route?: string | null;
  apiRequestIds?: string[];
  workerVersion?: string | null;
  correlationId: string;
  payloadHashes?: string[];
}): ReplayToken {
  return {
    replayId: newOpaqueId("replay", input.randomHex),
    featureFlags: { ...input.featureFlags },
    browser: input.browser ?? null,
    route: input.route ?? null,
    apiRequestIds: [...(input.apiRequestIds ?? [])],
    workerVersion: input.workerVersion ?? null,
    correlationId: input.correlationId,
    payloadHashes: [...(input.payloadHashes ?? [])],
  };
}
