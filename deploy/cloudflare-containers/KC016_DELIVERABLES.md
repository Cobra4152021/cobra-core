# KC-016 Deliverables — Cloudflare Containers

**Date:** 2026-07-25  
**Certified Core:** `v0.9.0-rc1` / `ec400d83a9cc8105557bda2105f177cc619638b2`  
**GPU required?** **No** (mock inference)

## Success criteria status

| Criterion | Status |
|-----------|--------|
| Core running on Cloudflare Containers | **BLOCKED** — Docker CLI/daemon not available on this machine |
| Health reports RC1 revision | Implemented in staging edge; **not live-verified** |
| Computer staging E2E proposal | **Not run** (no Core URL) |
| Human approval mandatory | Unchanged on Computer (prior KC-015) |
| Production disabled | Unchanged |

## 1–2. Files created / modified

**Created**

- `Dockerfile.cobra-core-staging`
- `wrangler.cobra-core-staging.jsonc`
- `deploy/cloudflare-containers/src/index.ts`
- `deploy/cloudflare-containers/package.json`
- `deploy/cloudflare-containers/tsconfig.json`
- `deploy/cloudflare-containers/README.md`
- `deploy/cloudflare-containers/DEPLOYMENT_SUMMARY.md`
- `deploy/cloudflare-containers/ROLLBACK.md`
- `deploy/cloudflare-containers/KC016_DELIVERABLES.md`

**Modified**

- `deploy/staging-rc1/staging_edge.py` — honor `COBRA_CORE_KILL_SWITCH`
- `.dockerignore` — exclude CF node_modules

## 3. Docker image name

Built by Wrangler as Cloudflare Registry image for Worker `cobra-core-staging`  
Local Dockerfile label: `cobra-core-staging` / `v0.9.0-rc1`

## 4. Cloudflare Container / Worker name

- Worker: `cobra-core-staging`
- Container class: `CobraCoreContainer`
- Instance name: `staging-rc1`

## 5. Wrangler configuration

`wrangler.cobra-core-staging.jsonc` (repo root)

## 6. Required secrets

```bash
npx wrangler secret put COBRA_CORE_AUTH_SECRET -c wrangler.cobra-core-staging.jsonc
```

## 7. Required variables

| Var | Value |
|-----|--------|
| `APP_ENV` | `staging` |
| `COBRA_CORE_VERSION` | `v0.9.0-rc1` |
| `COBRA_CORE_REVISION` | `ec400d83a9cc8105557bda2105f177cc619638b2` |
| `COBRA_CORE_KILL_SWITCH` | `false` |

## 8–9. Health / version

After deploy (Bearer required):

- `GET /health` → includes `status`, `version`, `revision` (+ Protocol V1 fields)
- `GET /version` → certified pin JSON

## 10. Staging URL or service binding

**Intended public URL (Computer-compatible):**

`https://cobra-core-staging.<account-subdomain>.workers.dev`

**Why public HTTPS:** Computer uses `fetch(COBRA_CORE_BASE_URL)`. Service binding preferred later; not wired yet.

**Actual URL:** *not provisioned* (Docker blocker).

## 11. Test results

| Test | Result |
|------|--------|
| Local staging edge (prior KC-016) | PASS (health/version/completion/401) |
| `wrangler deploy` Containers | **FAIL** — Docker CLI not launchable |
| winget Docker Desktop install | **FAIL** — admin elevation required |
| Wrangler auth | PASS (`cobra4152020@gmail.com`) |
| Protocol V1 source changes | None (by design) |

## 12. End-to-end validation

Not executed — no live Core URL.

## 13. Rollback

See `ROLLBACK.md`.

## 14. Estimated monthly staging cost

- Instance: `basic` (1/4 vCPU, 1 GiB, 4 GB), `max_instances=2`, sleep after 15m idle  
- Expectation: **low tens of USD/month** for light Internal Alpha (Workers Paid + Containers); confirm on Cloudflare billing after first week.

## 15. Remaining blockers

1. **No local Docker required.** Add GitHub Actions secrets, then run workflow:
   - `CLOUDFLARE_API_TOKEN`
   - `COBRA_CORE_AUTH_SECRET`
   - Actions → **Deploy Cobra Core Staging (Cloudflare Containers)** → Run workflow
2. Point Computer staging `COBRA_CORE_BASE_URL` at the workers.dev URL and enable Core flags.
3. Run smoke + Research OS proposal E2E as admin.

## Resource sizing (confirmed)

| Item | Value |
|------|--------|
| vCPU | 0.25 (`basic`) |
| RAM | 1 GiB |
| Disk | 4 GB |
| Concurrency | 2 |
| Cold start | First request after sleep: tens of seconds |
| GPU | **Not required** for mock RC1 |
