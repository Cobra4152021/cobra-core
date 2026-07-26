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
  /** KC-022/023 Adaptive Intelligence Router */
  AIR_ENABLED?: string;
  AIR_POLICY_ID?: string;
  AIR_EXCLUDE_PROVIDERS?: string;
  /** KC-025 Investigation Skills Framework */
  ISF_ENABLED?: string;
  /** KC-026 Reliability & Resilience Framework */
  RRF_ENABLED?: string;
  /** KC-027/028 Knowledge & Evidence Framework */
  KEF_ENABLED?: string;
  KEF_ALLOW_REQUEST_SEED?: string;
  KEF_EVIDENCE_VAULT_ENABLED?: string;
  KEF_EVIDENCE_VAULT_BASE_URL?: string;
  KEF_EVIDENCE_VAULT_TIMEOUT_MS?: string;
  KEF_EVIDENCE_VAULT_MAX_RESULTS?: string;
  KEF_EVIDENCE_VAULT_REQUIRE_TLS?: string;
  KEF_EVIDENCE_VAULT_ALLOW_PRIVATE_HOSTS?: string;
  /** Wrangler secrets — never log / never put in vars. */
  OPENAI_API_KEY?: string;
  KEF_EVIDENCE_VAULT_AUTH_TOKEN?: string;
};

const CERTIFIED_REVISION = "ec400d83a9cc8105557bda2105f177cc619638b2";
const CERTIFIED_VERSION = "v0.9.0-rc1";

export class CobraCoreContainer extends Container<Env> {
  defaultPort = 8080;
  /** Keep warm enough for Internal Alpha; sleep after idle. */
  sleepAfter = "15m";
  /** Required for Evidence Vault HTTPS egress (public Workers hostname). */
  enableInternet = true;

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
      AIR_ENABLED: pick("AIR_ENABLED", "true"),
      AIR_POLICY_ID: pick("AIR_POLICY_ID", "default_v1"),
      AIR_EXCLUDE_PROVIDERS: pick("AIR_EXCLUDE_PROVIDERS"),
      ISF_ENABLED: pick("ISF_ENABLED", "true"),
      RRF_ENABLED: pick("RRF_ENABLED", "true"),
      KEF_ENABLED: pick("KEF_ENABLED", "true"),
      KEF_ALLOW_REQUEST_SEED: pick("KEF_ALLOW_REQUEST_SEED", "false"),
      KEF_EVIDENCE_VAULT_ENABLED: pick("KEF_EVIDENCE_VAULT_ENABLED", "false"),
      KEF_EVIDENCE_VAULT_BASE_URL: pick("KEF_EVIDENCE_VAULT_BASE_URL"),
      KEF_EVIDENCE_VAULT_TIMEOUT_MS: pick("KEF_EVIDENCE_VAULT_TIMEOUT_MS", "10000"),
      KEF_EVIDENCE_VAULT_MAX_RESULTS: pick("KEF_EVIDENCE_VAULT_MAX_RESULTS", "25"),
      KEF_EVIDENCE_VAULT_REQUIRE_TLS: pick("KEF_EVIDENCE_VAULT_REQUIRE_TLS", "true"),
      KEF_EVIDENCE_VAULT_ALLOW_PRIVATE_HOSTS: pick(
        "KEF_EVIDENCE_VAULT_ALLOW_PRIVATE_HOSTS",
        "false",
      ),
      KEF_EVIDENCE_VAULT_AUTH_TOKEN: pick("KEF_EVIDENCE_VAULT_AUTH_TOKEN"),
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
        routes: [
          "/health",
          "/version",
          "/metrics",
          "/v1/chat/completions",
          "/cial-gate",
          "/air-gate",
          "/isf-gate",
          "/air/route",
          "/air/catalog",
          "/air/audit",
          "/air/metrics",
          "/isf/execute",
          "/isf/skills",
          "/isf/audit",
          "/isf/metrics",
          "/rrf/audit",
          "/rrf/metrics",
        ],
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

    // KC-023 Worker-side AIR gate probe (booleans / non-secret vars only).
    if (url.pathname === "/air-gate" && request.method === "GET") {
      return json({
        appEnv: env.APP_ENV,
        airEnabled: env.AIR_ENABLED ?? "true",
        airPolicyId: env.AIR_POLICY_ID ?? null,
        airExcludeProviders: env.AIR_EXCLUDE_PROVIDERS ?? "",
        cialProfile: env.CIAL_PROFILE ?? null,
        liveFlag: env.CIAL_LIVE_PROVIDER_ENABLED ?? null,
        openaiModel: env.OPENAI_MODEL ?? null,
        openaiKeyConfigured: Boolean(env.OPENAI_API_KEY?.trim()),
      });
    }

    // KC-025 Worker-side ISF gate probe (booleans / non-secret vars only).
    if (url.pathname === "/isf-gate" && request.method === "GET") {
      return json({
        appEnv: env.APP_ENV,
        isfEnabled: env.ISF_ENABLED ?? "true",
        airEnabled: env.AIR_ENABLED ?? "true",
        cialProfile: env.CIAL_PROFILE ?? null,
        liveFlag: env.CIAL_LIVE_PROVIDER_ENABLED ?? null,
        openaiModel: env.OPENAI_MODEL ?? null,
        openaiKeyConfigured: Boolean(env.OPENAI_API_KEY?.trim()),
      });
    }

    // KC-026 Worker-side RRF gate probe (booleans / non-secret vars only).
    if (url.pathname === "/rrf-gate" && request.method === "GET") {
      return json({
        appEnv: env.APP_ENV,
        rrfEnabled: env.RRF_ENABLED ?? "true",
        isfEnabled: env.ISF_ENABLED ?? "true",
        airEnabled: env.AIR_ENABLED ?? "true",
        cialProfile: env.CIAL_PROFILE ?? null,
        liveFlag: env.CIAL_LIVE_PROVIDER_ENABLED ?? null,
      });
    }

    // KC-028 Worker-side KEF/Vault gate probe (booleans / non-secret vars only).
    if (url.pathname === "/kef-gate" && request.method === "GET") {
      return json({
        appEnv: env.APP_ENV,
        kefEnabled: env.KEF_ENABLED ?? "true",
        vaultEnabled: env.KEF_EVIDENCE_VAULT_ENABLED ?? "false",
        allowRequestSeed: env.KEF_ALLOW_REQUEST_SEED ?? "false",
        vaultBaseUrlHost: (() => {
          try {
            return env.KEF_EVIDENCE_VAULT_BASE_URL
              ? new URL(env.KEF_EVIDENCE_VAULT_BASE_URL).host
              : null;
          } catch {
            return null;
          }
        })(),
        vaultTokenConfigured: Boolean(env.KEF_EVIDENCE_VAULT_AUTH_TOKEN?.trim()),
        isfEnabled: env.ISF_ENABLED ?? "true",
        airEnabled: env.AIR_ENABLED ?? "true",
        rrfEnabled: env.RRF_ENABLED ?? "true",
        cialProfile: env.CIAL_PROFILE ?? null,
        liveFlag: env.CIAL_LIVE_PROVIDER_ENABLED ?? null,
        // KC-028.1: prove which DO name this Worker script targets.
        containerInstance: "staging-rc1-kc0281c",
        workerBuild: "kc0281c",
        enableInternet: true,
      });
    }

    // Shared staging instance (stateless mock Protocol V1).
    // Bump the name after auth-secret rotation so a fresh Container boots with
    // current Worker secrets (DO constructor envVars are not hot-reloaded).
    // Bump after OPENAI secret/var binding so containers pick up new envVars.
    // kc0281c: post-rollback restore (Vault enabled).
    const container = getContainer(env.COBRA_CORE_CONTAINER, "staging-rc1-kc0281c");
    return container.fetch(request);
  },
};
