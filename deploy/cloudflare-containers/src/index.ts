/**
 * KC-016 — Cobra Core staging Worker (Cloudflare Containers).
 *
 * Routes HTTPS traffic to the Protocol V1 container (staging edge + certified Core).
 * Staging only. Not production.
 */

import { Container, getContainer } from "@cloudflare/containers";

export type Env = {
  COBRA_CORE_CONTAINER: DurableObjectNamespace;
  APP_ENV: string;
  COBRA_CORE_VERSION: string;
  COBRA_CORE_REVISION: string;
  COBRA_CORE_KILL_SWITCH: string;
  /** Wrangler secret — never log. */
  COBRA_CORE_AUTH_SECRET: string;
};

const CERTIFIED_REVISION = "ec400d83a9cc8105557bda2105f177cc619638b2";
const CERTIFIED_VERSION = "v0.9.0-rc1";

export class CobraCoreContainer extends Container<Env> {
  defaultPort = 8080;
  /** Keep warm enough for Internal Alpha; sleep after idle. */
  sleepAfter = "15m";

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    const kill = /^(1|true|yes|on)$/i.test(String(env.COBRA_CORE_KILL_SWITCH ?? "false"));
    this.envVars = {
      APP_ENV: env.APP_ENV || "staging",
      COBRA_CORE_VERSION: env.COBRA_CORE_VERSION || CERTIFIED_VERSION,
      COBRA_CORE_REVISION: env.COBRA_CORE_REVISION || CERTIFIED_REVISION,
      COBRA_CORE_GIT_SHA: env.COBRA_CORE_REVISION || CERTIFIED_REVISION,
      COBRA_CORE_KILL_SWITCH: kill ? "true" : "false",
      COBRA_CORE_ENABLED: kill ? "false" : "true",
      COBRA_CORE_AUTH_SECRET: env.COBRA_CORE_AUTH_SECRET || "",
      COBRA_INFERENCE_MODE: "mock",
      COBRA_PROTOCOL_VERSION: "1",
      COBRA_COMPATIBILITY_VERSION: "1",
      COBRA_CORE_METRICS_ENABLED: "true",
      COBRA_CORE_MAX_CONCURRENT: "2",
      COBRA_CORE_REQUIRE_ORG_HEADER: "true",
      PORT: "8080",
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
        routes: ["/health", "/version", "/metrics", "/v1/chat/completions"],
        note: "Protocol V1 is served by the container; use Bearer auth.",
      });
    }

    // Shared staging instance (stateless mock Protocol V1).
    // Bump the name after auth-secret rotation so a fresh Container boots with
    // current Worker secrets (DO constructor envVars are not hot-reloaded).
    const container = getContainer(env.COBRA_CORE_CONTAINER, "staging-rc1-b");
    return container.fetch(request);
  },
};
