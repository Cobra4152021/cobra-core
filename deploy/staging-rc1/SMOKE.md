# KC-016 Smoke-test instructions

## Prerequisites

- Staging URL (e.g. `https://cobra-core-staging-rc1.fly.dev`)
- `COBRA_CORE_AUTH_SECRET` matching the Fly secret

## PowerShell

```powershell
$env:COBRA_CORE_BASE_URL = "https://cobra-core-staging-rc1.fly.dev"
$env:COBRA_CORE_AUTH_SECRET = "<secret>"
./deploy/staging-rc1/smoke.ps1
```

## curl

```bash
export BASE=https://cobra-core-staging-rc1.fly.dev
export SECRET=...

curl -sS -H "Authorization: Bearer $SECRET" "$BASE/health" | jq .
curl -sS -H "Authorization: Bearer $SECRET" "$BASE/version" | jq .

# Anonymous must fail
curl -sS -o /dev/null -w "%{http_code}\n" "$BASE/health"   # expect 401

# Inference
curl -sS -H "Authorization: Bearer $SECRET" \
  -H "Content-Type: application/json" \
  -H "X-Cobra-Org-Id: org_staging_smoke" \
  -d '{"model":"cobra-core-qwen3-8b","stream":false,"max_tokens":32,"messages":[{"role":"user","content":"ping"}]}' \
  "$BASE/v1/chat/completions" | jq .
```

## Pass criteria

| Check | Expect |
|-------|--------|
| `/health` | 200, `status=healthy`, `version=v0.9.0-rc1`, revision pin |
| `/version` | 200, same revision |
| Anonymous | 401 |
| Completions | 200 with `choices` |
| Kill switch | `COBRA_CORE_ENABLED=false` → 503 |
