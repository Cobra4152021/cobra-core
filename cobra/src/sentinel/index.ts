/** KC-012 — Cobra Sentinel (investigate Cobra itself). */

export * from "./types.js";
export * from "./ids.js";
export * from "./redact.js";
export * from "./triage.js";
export * from "./feedback.js";
export * from "./replay.js";

export const SENTINEL_CORE_VERSION = "0.1.0-alpha1";
export const SENTINEL_DOMAIN = {
  id: "cobra.sentinel",
  title: "Cobra Sentinel",
  version: SENTINEL_CORE_VERSION,
  description: "Telemetry, diagnostics, feedback, and operational intelligence for Cobra.",
} as const;
