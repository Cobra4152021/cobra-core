# KC-016 Rollback instructions (staging only)

## Immediate kill switch (preferred)

```bash
flyctl secrets set COBRA_CORE_ENABLED=false -a cobra-core-staging-rc1
# or:
flyctl secrets unset COBRA_CORE_ENABLED -a cobra-core-staging-rc1
flyctl secrets set COBRA_CORE_ENABLED=false -a cobra-core-staging-rc1
```

Note: `[env]` in `fly.staging-rc1.toml` sets defaults; **secrets override**. Prefer:

```bash
flyctl secrets set COBRA_CORE_ENABLED=false -a cobra-core-staging-rc1
```

Then confirm:

```bash
curl -sS -H "Authorization: Bearer $SECRET" \
  https://cobra-core-staging-rc1.fly.dev/health
# expect status unhealthy / kill_switch / 503
```

Also disable Computer staging routing:

```bash
npx wrangler vars set COBRA_CORE_KILL_SWITCH=true --env staging
# and/or COBRA_CORE_ENABLED=false
npx wrangler deploy --env staging
```

## Scale to zero / destroy staging app

```bash
flyctl scale count 0 -a cobra-core-staging-rc1
# nuclear (staging only):
# flyctl apps destroy cobra-core-staging-rc1
```

## Redeploy previous image

```bash
flyctl releases -a cobra-core-staging-rc1
flyctl deploy --image-label <previous> -a cobra-core-staging-rc1
# or redeploy known-good git SHA of deploy packaging + RC1 tree
```

Never roll forward to an uncertified Core commit for Internal Alpha.
