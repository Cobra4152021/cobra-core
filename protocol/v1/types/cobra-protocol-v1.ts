/**
 * Cobra Protocol V1 — TypeScript types (governance package).
 * Protocol Version: 1
 * Compatibility Version: 1
 * Schema Version: 1.0.0
 *
 * Authority: Cobra Computer frozen contract.
 * Do not redesign the protocol in this file.
 */

export const COBRA_PROTOCOL_VERSION = "1" as const;
export const COBRA_COMPATIBILITY_VERSION = "1" as const;
export const COBRA_SCHEMA_VERSION = "1.0.0" as const;

export type ProtocolVersion = typeof COBRA_PROTOCOL_VERSION;
export type CompatibilityVersion = typeof COBRA_COMPATIBILITY_VERSION;

export type ChatRole = "system" | "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface Capabilities {
  streaming: boolean;
  vision: boolean;
  toolCalling: boolean;
  jsonMode: boolean;
  thinking: boolean;
  embeddings: boolean;
  /** Future keys are allowed; clients must ignore unknowns. */
  [key: string]: boolean;
}

export interface Latency {
  queue_ms: number;
  provider_latency_ms: number;
  inference_ms: number;
  total_ms: number;
}

export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface NormalizedError {
  code: string;
  message: string;
  /** Protocol V1: always false. */
  retryable: false;
  requestId: string;
}

export interface Limits {
  maxContext: number | null;
  maxOutputTokens: number | null;
  timeoutMs: number;
}

export interface HealthResponse {
  protocolVersion: ProtocolVersion;
  compatibilityVersion: CompatibilityVersion;
  providerId: string;
  model: string;
  revision: string;
  gitSha: string;
  capabilities: Capabilities;
  provider: string;
  enabled: boolean;
  authenticated: boolean;
  reachable: boolean;
  reason: string;
  limits: Limits;
  latency: Latency;
  requestId?: string;
}

export interface CompletionRequest {
  model: string;
  stream: false;
  max_tokens: number;
  messages: ChatMessage[];
}

export interface CompletionChoice {
  index?: number;
  finish_reason?: string;
  message: {
    role?: string;
    content: string;
  };
}

export interface CompletionResponse {
  id?: string;
  object?: string;
  model?: string;
  choices: CompletionChoice[];
  usage: Usage;
  latency?: Latency;
  protocolVersion?: ProtocolVersion;
  compatibilityVersion?: CompatibilityVersion;
  requestId?: string;
  providerId?: string;
  revision?: string;
  gitSha?: string;
  capabilities?: Capabilities;
}

/** Computer-side one-shot-backed stream events (not native SSE). */
export type StreamEvent =
  | { type: "delta"; text: string; requestId: string }
  | { type: "done"; text: string; requestId: string }
  | { type: "error"; requestId: string; error: NormalizedError };

export interface StreamingFixture {
  mode: "one-shot-backed";
  wire: {
    method: "POST";
    path: "/v1/chat/completions";
    stream: false;
  };
  events: StreamEvent[];
}

export interface ProtocolManifest {
  protocolVersion: ProtocolVersion;
  compatibilityVersion: CompatibilityVersion;
  schemaVersion: string;
  schemaHash: string;
  fixtureHash: string;
  generatedAt: string;
  sourceCommit: string;
}
