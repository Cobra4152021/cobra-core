# KC-016 Rollback — Cloudflare Containers staging

## Kill switch (fast)

```bash
npx wrangler vars set COBRA_CORE_KILL_SWITCH="true" -c wrangler.cobra-core-staging.jsonc
npx wrangler deploy -c wrangler.cobra-core-staging.jsonc
```

Also disable Computer staging Core routing:

```bash
npx wrangler vars set COBRA_CORE_KILL_SWITCH="true" --env staging
# or COBRA_CORE_ENABLED=false
npx wrangler deploy --env staging
```

## Disable Worker routes / delete staging Worker

```bash
npx wrangler delete -c wrangler.cobra-core-staging.jsonc
```

**Do not** delete or modify production Computer Worker.

## Redeploy previous container image

```bash
npx wrangler containers images list
# redeploy prior known-good Worker version from dashboard or git checkout + deploy
```
