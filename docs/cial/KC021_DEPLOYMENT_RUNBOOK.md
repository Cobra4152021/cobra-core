# KC-021 — Deployment Runbook (Staging)

## Preconditions

- Branch: `kc-021-live-provider-cert` (reviewed, tested, pushed)
- Secrets in GitHub Actions:
  - `CLOUDFLARE_API_TOKEN`
  - `COBRA_CORE_AUTH_SECRET`
  - `OPENAI_API_KEY` (optional until live enablement)
- **Do not** put API keys in `wrangler` `vars` or git

## Safe deploy sequence

1. Deploy with defaults (`CIAL_LIVE_PROVIDER_ENABLED=false`, `CIAL_PROVIDER=mock`).
2. Confirm Core health / version / certified revision pin.
3. Confirm mock proposal path still reaches `pending_approval` (Computer).
4. Bind `OPENAI_API_KEY` secret (workflow step or `wrangler secret put`).
5. Set non-secret vars for endpoint/model (no keys):
   - `OPENAI_BASE_URL`
   - `OPENAI_MODEL`
   - `CIAL_DEFAULT_MODEL`
   - timeouts / retries / quotas as needed
6. Bump container instance name if envVars must reload (already `staging-rc1-kc021a` in KC-021).
7. Only then set `CIAL_LIVE_PROVIDER_ENABLED=true` and `CIAL_PROVIDER=openai`.
8. Redeploy Worker / bump instance again so container sees new vars.
9. Run live health + harness (`python scripts/kc021/cert_harness.py --live`).
10. Record workflow run, image tag/digest, Worker version, timestamp (no secrets).

## Authoritative build

GitHub Actions: `Deploy Cobra Core Staging (Cloudflare Containers)`  
No local Docker release builds.

## Production

Refuse. Do not set live flags or Core enablement in production.
