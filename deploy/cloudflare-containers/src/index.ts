/**
 * KC-016 — Cobra Core staging Worker (Cloudflare Containers).
 *
 * Routes HTTPS traffic to the Protocol V1 container (staging edge + certified Core).
 * Staging only. Not production.
 */

import { Container, getContainer } from "@cloudflare/containers";
import { env as workerEnv } from "cloudflare:workers";

export type Env = {
  COBRA_CORE_CONTAINER: DurableObjectNamespace;
  APP_ENV: string;
  COBRA_CORE_VERSION: string;
  COBRA_CORE_REVISION: string;
  COBRA_CORE_KILL_SWITCH: string;
  /** Wrangler secret — never log. */
  COBRA_CORE_AUTH_SECRET: string;
  /** KC-021 — plain vars only (never secrets). */
  CIAL_ENABLED?: string;
  CIAL_LIVE_PROVIDER_ENABLED?: string;
  /** Profile-centric activation (default | offline | research). */
  CIAL_PROFILE?: string;
  /** @deprecated Prefer CIAL_PROFILE. Kept for compat mapping only. */
  CIAL_PROVIDER?: string;
  CIAL_DEFAULT_PROVIDER?: string;
  CIAL_DEFAULT_MODEL?: string;
  CIAL_ROUTING_POLICY?: string;
  OPENAI_BASE_URL?: string;
  OPENAI_MODEL?: string;
  OPENAI_TIMEOUT_SECONDS?: string;
  OPENAI_MAX_RETRIES?: string;
  CIAL_LIVE_MAX_INPUT_CHARS?: string;
  CIAL_LIVE_MAX_OUTPUT_TOKENS?: string;
  CIAL_LIVE_MAX_CONCURRENT?: string;
  CIAL_LIVE_DAILY_REQUEST_QUOTA?: string;
  CIAL_LIVE_DAILY_COST_CEILING?: string;
  /** Wrangler secret — never log / never put in vars. */
  OPENAI_API_KEY?: string;
};

const CERTIFIED_REVISION = "ec400d83a9cc8105557bda2105f177cc619638b2";
const CERTIFIED_VERSION = "v0.9.0-rc1";

export class CobraCoreContainer extends Container<Env> {
  defaultPort = 8080;
  /** Keep warm enough for Internal Alpha; sleep after idle. */
  sleepAfter = "15m";

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    // Prefer constructor env; fall back to module workerEnv (CF secrets pattern).
    const we = workerEnv as Env;
    const pick = (k: keyof Env, fallback = ""): string =>
      String(env[k] ?? we[k] ?? fallback);
    const kill = /^(1|true|yes|on)$/i.test(pick("COBRA_CORE_KILL_SWITCH", "false"));
    // KC-021: live provider is opt-in. Defaults keep mock / disabled.
    const liveEnabled = /^(1|true|yes|on)$/i.test(
      pick("CIAL_LIVE_PROVIDER_ENABLED", "false"),
    );
    const openaiKey = pick("OPENAI_API_KEY");
    const authSecret = pick("COBRA_CORE_AUTH_SECRET");
    this.envVars = {
      APP_ENV: pick("APP_ENV", "staging"),
      COBRA_CORE_VERSION: pick("COBRA_CORE_VERSION", CERTIFIED_VERSION),
      COBRA_CORE_REVISION: pick("COBRA_CORE_REVISION", CERTIFIED_REVISION),
      COBRA_CORE_GIT_SHA: pick("COBRA_CORE_REVISION", CERTIFIED_REVISION),
      COBRA_CORE_KILL_SWITCH: kill ? "true" : "false",
      COBRA_CORE_ENABLED: kill ? "false" : "true",
      COBRA_CORE_AUTH_SECRET: authSecret,
      COBRA_INFERENCE_MODE: "mock",
      COBRA_PROTOCOL_VERSION: "1",
      COBRA_COMPATIBILITY_VERSION: "1",
      COBRA_CORE_METRICS_ENABLED: "true",
      COBRA_CORE_MAX_CONCURRENT: "2",
      COBRA_CORE_REQUIRE_ORG_HEADER: "true",
      PORT: "8080",
      CIAL_ENABLED: pick("CIAL_ENABLED", "true"),
      CIAL_LIVE_PROVIDER_ENABLED: liveEnabled ? "true" : "false",
      CIAL_PROFILE: pick("CIAL_PROFILE", "default"),
      // Legacy vendor knobs (optional); Core maps them to profiles if CIAL_PROFILE unset.
      CIAL_PROVIDER: pick("CIAL_PROVIDER"),
      CIAL_DEFAULT_PROVIDER: pick("CIAL_DEFAULT_PROVIDER"),
      CIAL_DEFAULT_MODEL: pick("CIAL_DEFAULT_MODEL"),
      CIAL_ROUTING_POLICY: pick("CIAL_ROUTING_POLICY", "default"),
      OPENAI_BASE_URL: pick("OPENAI_BASE_URL"),
      OPENAI_MODEL: pick("OPENAI_MODEL"),
      OPENAI_TIMEOUT_SECONDS: pick("OPENAI_TIMEOUT_SECONDS", "60"),
      OPENAI_MAX_RETRIES: pick("OPENAI_MAX_RETRIES", "2"),
      OPENAI_API_KEY: openaiKey,
      CIAL_LIVE_MAX_INPUT_CHARS: pick("CIAL_LIVE_MAX_INPUT_CHARS", "32000"),
      CIAL_LIVE_MAX_OUTPUT_TOKENS: pick("CIAL_LIVE_MAX_OUTPUT_TOKENS"),
      CIAL_LIVE_MAX_CONCURRENT: pick("CIAL_LIVE_MAX_CONCURRENT", "1"),
      CIAL_LIVE_DAILY_REQUEST_QUOTA: pick("CIAL_LIVE_DAILY_REQUEST_QUOTA"),
      CIAL_LIVE_DAILY_COST_CEILING: pick("CIAL_LIVE_DAILY_COST_CEILING"),
    };
  }

  override onStart(): void {
    console.log(
      JSON.stringify({
        channel: "cobra_core_container",
        event: "start",
        version: CERTIFIED_VERSION,
        revision: CERTIFIED_REVISION,
      }),
    );
  }

  override onStop(): void {
    console.log(JSON.stringify({ channel: "cobra_core_container", event: "stop" }));
  }

  override onError(error: unknown): void {
    const message = error instanceof Error ? error.message : "container_error";
    console.log(
      JSON.stringify({
        channel: "cobra_core_container",
        event: "error",
        message: message.slice(0, 200),
      }),
    );
  }
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (env.APP_ENV !== "staging") {
      return json(
        {
          error: "Cobra Core Containers Worker refuses non-staging APP_ENV",
          appEnv: env.APP_ENV ?? null,
        },
        403,
      );
    }

    if ((env.COBRA_CORE_REVISION || "") !== CERTIFIED_REVISION) {
      return json(
        {
          error: "revision_mismatch",
          expected: CERTIFIED_REVISION,
          configured: env.COBRA_CORE_REVISION ?? null,
        },
        503,
      );
    }

    if (!env.COBRA_CORE_AUTH_SECRET?.trim()) {
      return json({ error: "COBRA_CORE_AUTH_SECRET is not configured" }, 503);
    }

    const url = new URL(request.url);

    // Worker-level identity (does not replace container /health).
    if (url.pathname === "/" && request.method === "GET") {
      return json({
        service: "cobra-core-staging",
        appEnv: env.APP_ENV,
        version: env.COBRA_CORE_VERSION,
        revision: env.COBRA_CORE_REVISION,
        killSwitch: String(env.COBRA_CORE_KILL_SWITCH ?? "false"),
        routes: ["/health", "/version", "/metrics", "/v1/chat/completions", "/cial-gate"],
        note: "Protocol V1 is served by the container; use Bearer auth.",
      });
    }

    // KC-021 Worker-side gate probe (booleans / non-secret vars only).
    if (url.pathname === "/cial-gate" && request.method === "GET") {
      return json({
        appEnv: env.APP_ENV,
        cialEnabled: env.CIAL_ENABLED ?? null,
        cialProfile: env.CIAL_PROFILE ?? null,
        liveFlag: env.CIAL_LIVE_PROVIDER_ENABLED ?? null,
        openaiModel: env.OPENAI_MODEL ?? null,
        openaiBaseUrl: env.OPENAI_BASE_URL ?? null,
        openaiKeyConfigured: Boolean(env.OPENAI_API_KEY?.trim()),
        authSecretConfigured: Boolean(env.COBRA_CORE_AUTH_SECRET?.trim()),
      });
    }

    // Shared staging instance (stateless mock Protocol V1).
    // Bump the name after auth-secret rotation so a fresh Container boots with
    // current Worker secrets (DO constructor envVars are not hot-reloaded).
    // Bump after OPENAI secret/var binding so containers pick up new envVars.
    // kc021g: gpt-5 max_completion_tokens payload fix.
    const container = getContainer(env.COBRA_CORE_CONTAINER, "staging-rc1-kc021g");
    return container.fetch(request);
  },
};
