# KC-016 Phase 1 — Deployment summary (before changes)

**Certified build (immutable):** `v0.9.0-rc1` @ `ec400d83a9cc8105557bda2105f177cc619638b2`  
**Repo state used for packaging:** `kc-016-staging-deploy` (deploy-only commits on top of RC1; Protocol V1 sources unchanged from certified SHA)

## Inspection results

| Item | Finding |
|------|---------|
| Python | `>=3.12` (`pyproject.toml`); image pins **3.12** |
| Dependencies | hatchling / pip (`pydantic`, `PyYAML`); **no GPU** for mock Internal Alpha |
| Startup (certified) | `cobra-protocol-v1` → `cobra_core.protocol_v1.cli:main` → `serve_forever` |
| Startup (staging) | `python staging_edge.py` — edge on `0.0.0.0:$PORT`, Core loopback-only |
| Endpoints | Core: `GET /health`, `GET /metrics`, `POST /v1/chat/completions` |
| `/version` | **Not in certified Core** — provided by staging edge |
| Auth | Bearer `COBRA_CORE_AUTH_SECRET` (required) |
| Port | Core: loopback only (`127.0.0.1`). Edge: `PORT` (default 8080) |
| Kill switch | `COBRA_CORE_ENABLED=false` |
| Admission | `COBRA_CORE_MAX_CONCURRENT`, optional daily limit |
| GPU | **Not required** for `COBRA_INFERENCE_MODE=mock` |

## Cloudflare Containers approach

1. Worker `cobra-core-staging` proxies HTTP → Container (Durable Object + `@cloudflare/containers`).
2. Container runs staging edge + certified Protocol V1 (mock).
3. **Public HTTPS workers.dev URL** is required for Cobra Computer today because Computer uses `fetch(COBRA_CORE_BASE_URL)` (absolute HTTPS). Service binding is preferred long-term but needs Computer adapter changes; document both.

## Hard blocker (this machine)

- **Docker Desktop is not installed.** Cloudflare Containers `wrangler deploy` **requires a local Docker daemon** to build/push images.
- Wrangler **is** authenticated (`cobra4152020@gmail.com`).

## Sizing (mock staging)

| Resource | Recommendation |
|----------|----------------|
| Instance type | `basic` (1/4 vCPU, 1 GiB, 4 GB disk) |
| max_instances | 2 |
| Concurrency | `COBRA_CORE_MAX_CONCURRENT=2` |
| Cold start | Tens of seconds on first request after sleep |
| GPU | **None** — STOP if switching to local Qwen weights |
| Est. monthly cost | Low tens of USD for light Internal Alpha (Workers Paid + Containers basic); exact bill depends on idle/sleep and request volume |

## Reuse (no duplicate Protocol V1)

- Reuse `deploy/staging-rc1/staging_edge.py` and Dockerfile patterns.
- Do **not** modify Protocol V1 server sources under `src/cobra_core/protocol_v1/`.
