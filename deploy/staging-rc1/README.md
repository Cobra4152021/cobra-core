# KC-016 — Deploy Cobra Core RC1 to Staging

**Certified only**

| Field | Value |
|-------|--------|
| Version | `v0.9.0-rc1` |
| Revision | `ec400d83a9cc8105557bda2105f177cc619638b2` |
| Branch | `kc-rc1-certification` |
| Tag | `v0.9.0-rc1` |

**Not production.** Do not create a production Core app from these files.

## Recommendation: Fly.io (Internal Alpha)

| Target | Verdict | Why |
|--------|---------|-----|
| **Fly.io** | **Recommended** | `flyctl` available; remote Docker builder (no local Docker); automatic HTTPS; cheap shared VM for **mock** Protocol V1; fast Internal Alpha |
| Cloudflare Containers | Later | Needs local Docker to build/push; extra Worker wiring; overkill for mock RC1 |
| Render / Railway | Acceptable alt | Similar PaaS HTTPS; no CLI authenticated in this environment |
| Docker VM | Good ops control | Manual TLS/proxy; use when Fly unavailable |
| GPU VM | **Not for RC1 mock** | Required only when `COBRA_INFERENCE_MODE=local` / real Qwen3-8B weights |

RC1 Core binds **loopback only** by design. Staging uses `staging_edge.py` on `0.0.0.0:$PORT` with Fly TLS termination, proxying to Core on `127.0.0.1`.

## Architecture

```
Internet (HTTPS)
  → Fly edge TLS
  → staging_edge.py :8080
       → GET /version (edge)
       → GET /health (edge enrich + Core)
       → GET /metrics (proxy → Core)
       → POST /v1/chat/completions (proxy → Core)
  → Protocol V1 Core 127.0.0.1:18080  (certified package)
```

**Organization isolation:** Computer remains system of record (session, RBAC, org). Staging edge requires `X-Cobra-Org-Id` on inference as defense-in-depth only.

## Startup command

```bash
python deploy/staging-rc1/staging_edge.py
# container CMD: python /app/staging_edge.py
```

## Environment variables

See `.env.example`. Required:

- `COBRA_CORE_AUTH_SECRET`

Pinned:

- `COBRA_CORE_REVISION=ec400d83a9cc8105557bda2105f177cc619638b2`

Kill switch:

- `COBRA_CORE_ENABLED=false` → 503

Admission (Core):

- `COBRA_CORE_MAX_CONCURRENT`
- `COBRA_CORE_DAILY_REQUEST_LIMIT` (optional)

## Deploy (Fly.io)

```bash
# 1) Login (interactive once)
flyctl auth login

# 2) From cobra-core repo root at RC1 tree
flyctl apps create cobra-core-staging-rc1
flyctl secrets set COBRA_CORE_AUTH_SECRET="..." -a cobra-core-staging-rc1
flyctl deploy --remote-only -c fly.staging-rc1.toml
```

Staging URL (after create):

`https://cobra-core-staging-rc1.fly.dev`

## Health / version

Authenticated:

```bash
curl -sS -H "Authorization: Bearer $COBRA_CORE_AUTH_SECRET" \
  https://cobra-core-staging-rc1.fly.dev/health
```

Expected (minimum):

```json
{
  "status": "healthy",
  "version": "v0.9.0-rc1",
  "revision": "ec400d83a9cc8105557bda2105f177cc619638b2"
}
```

(Plus Protocol V1 identity fields for Cobra Computer.)

```bash
curl -sS -H "Authorization: Bearer $COBRA_CORE_AUTH_SECRET" \
  https://cobra-core-staging-rc1.fly.dev/version
```

## Smoke / rollback

- Smoke: [SMOKE.md](./SMOKE.md) / `smoke.ps1`
- Rollback: [ROLLBACK.md](./ROLLBACK.md)

## Local without Docker

```bash
pip install .
$env:COBRA_CORE_AUTH_SECRET = "dev-only-secret"
$env:PORT = "8080"
python deploy/staging-rc1/staging_edge.py
```

Then run smoke against `http://127.0.0.1:8080`.
