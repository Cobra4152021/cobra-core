# KC-016 — Cobra Core on Cloudflare Containers (staging)

**Certified revision:** `ec400d83a9cc8105557bda2105f177cc619638b2` (`v0.9.0-rc1`)  
**Worker name:** `cobra-core-staging`  
**Not production.**

## Phase 1 summary

See [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md).

## Why a public HTTPS URL

Cobra Computer’s Protocol V1 client uses absolute `fetch(COBRA_CORE_BASE_URL)`.  
A **workers.dev HTTPS URL** is therefore required for Internal Alpha without changing Computer to a service binding.

Preferred later: Computer staging `services` binding → `cobra-core-staging` (no public Core URL).

## Prerequisites

1. Docker Desktop **running** (`docker info` succeeds) — **required** by Cloudflare Containers
2. Workers Paid plan + Containers enabled
3. Wrangler authenticated (`npx wrangler whoami`)

## Deploy (staging only)

From **cobra-core repository root**:

```bash
# Install Worker deps once
cd deploy/cloudflare-containers && npm install && cd ../..

# Secret (never commit)
npx wrangler secret put COBRA_CORE_AUTH_SECRET -c wrangler.cobra-core-staging.jsonc

# Deploy Worker + build/push container image
npx wrangler deploy -c wrangler.cobra-core-staging.jsonc
```

Expected URL:

`https://cobra-core-staging.<YOUR_SUBDOMAIN>.workers.dev`

## Connect Cobra Computer staging

```bash
# On Computer staging Worker only:
npx wrangler secret put COBRA_CORE_AUTH_SECRET --env staging   # same value
npx wrangler vars set COBRA_CORE_BASE_URL="https://cobra-core-staging.<subdomain>.workers.dev" --env staging
npx wrangler vars set COBRA_CORE_REVISION="ec400d83a9cc8105557bda2105f177cc619638b2" --env staging
npx wrangler vars set COBRA_CORE_ENABLED="true" --env staging
npx wrangler vars set RESEARCH_LLM_ENABLED="true" --env staging
npx wrangler deploy --env staging
```

## Endpoints

| Path | Auth | Notes |
|------|------|--------|
| `GET /health` | Bearer | `status`, `version`, `revision` + Protocol V1 fields |
| `GET /version` | Bearer | Certified pin |
| `GET /metrics` | Bearer | Prometheus |
| `POST /v1/chat/completions` | Bearer + `X-Cobra-Org-Id` | Protocol V1 |

## Kill switch

```bash
npx wrangler vars set COBRA_CORE_KILL_SWITCH="true" -c wrangler.cobra-core-staging.jsonc
npx wrangler deploy -c wrangler.cobra-core-staging.jsonc
```

## Rollback

See [ROLLBACK.md](./ROLLBACK.md).

## Current machine blocker

Docker Desktop is **not installed** here (winget install failed without admin).  
Wrangler is authenticated. Deploy cannot complete until Docker is available.
