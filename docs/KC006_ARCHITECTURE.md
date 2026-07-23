# KC-006 — Labor domain (cobra-core)

Pure TypeScript pack at `cobra/src/investigator/domains/labor/`.

Mirrored into Worker at `worker/cobra/investigator/domains/labor/`. Planner/strategy resolve `labor_*` template IDs into existing Strategy Engine strategies. Reuses Government staffing/overtime metrics. No LLM required.

**14 templates** · migration hint `0050_cobra_labor` · API namespace `/api/investigator/labor/*`

See hidden-grid-os-qwen-live `docs/KC006_*.md` for API, security, pilots, and certification.

Branches: `kc-006-cobra-labor-core` (core) / `kc-006-cobra-labor` (Worker).

Production: all `LABOR_*` flags **false**.
