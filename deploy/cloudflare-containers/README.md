# KC-016 — Cobra Core on Cloudflare Containers (staging)

**Certified revision:** `ec400d83a9cc8105557bda2105f177cc619638b2` (`v0.9.0-rc1`)  
**Worker:** `cobra-core-staging`  
**Not production.**

## No Docker on your laptop

Cloudflare Containers need a Linux `amd64` image build. That build runs in **GitHub Actions** (cloud runner with Docker), not on your PC.

| Where | Docker? |
|-------|---------|
| Your computer | **No** |
| GitHub Actions `ubuntu-latest` | Yes (ephemeral) |
| Cloudflare (runtime) | Runs the pushed image |

## One-time GitHub secrets

In https://github.com/Cobra4152021/cobra-core/settings/secrets/actions add:

| Secret | Purpose |
|--------|---------|
| `CLOUDFLARE_API_TOKEN` | API token with Workers edit + Containers + Account read |
| `COBRA_CORE_AUTH_SECRET` | Bearer token shared with Cobra Computer staging |

Create the Cloudflare token at: https://dash.cloudflare.com/profile/api-tokens  
Use a custom token including **Account → Cloudflare Workers → Edit** (and Containers if listed).

## Deploy (cloud only)

1. Merge/push `kc-016-staging-deploy` (or run workflow manually).
2. GitHub → **Actions** → **Deploy Cobra Core Staging (Cloudflare Containers)** → **Run workflow**.
3. When green, open:
   `https://cobra-core-staging.<your-subdomain>.workers.dev`

Smoke:

```bash
curl -sS -H "Authorization: Bearer $COBRA_CORE_AUTH_SECRET" \
  https://cobra-core-staging.<subdomain>.workers.dev/health
```

## Connect Cobra Computer staging

```bash
# Same auth secret as Core
npx wrangler secret put COBRA_CORE_AUTH_SECRET --env staging
npx wrangler vars set COBRA_CORE_BASE_URL="https://cobra-core-staging.<subdomain>.workers.dev" --env staging
npx wrangler vars set COBRA_CORE_REVISION="ec400d83a9cc8105557bda2105f177cc619638b2" --env staging
npx wrangler vars set COBRA_CORE_ENABLED="true" --env staging
npx wrangler vars set RESEARCH_LLM_ENABLED="true" --env staging
npx wrangler deploy --env staging
```

## Why public HTTPS (not only a service binding)

Cobra Computer’s adapter calls `fetch(COBRA_CORE_BASE_URL)`. A workers.dev HTTPS URL is required until Computer is changed to a Worker service binding.

## Kill switch / rollback

See [ROLLBACK.md](./ROLLBACK.md).
