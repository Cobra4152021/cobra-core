# KC-028.1 — Service Topology

## Current (certified)

**Public HTTPS**

```
Worker (cobra-core-staging)
  → Container DO (Protocol V1 + staging edge)
  → HTTPS egress
  → Computer Vault Worker (hidden-grid-os-staging)
```

### Measured characteristics

- Reliability: health/search/file green after UA fix
- Latency: search dominates (~3s); file ops ~150 ms; skills ~0.5 s to `pending_approval`
- Ops: no extra Worker bindings; uses existing Vault public URL + secret

## Alternative (not migrated)

**Cloudflare Service Binding / Worker-to-Worker**

### Advantages

- Avoids public edge / Bot Fight Mode on container egress
- Lower and more predictable latency
- Keeps traffic on Cloudflare’s internal path
- Simpler auth options (binding trust + service tokens)

### Trade-offs

- Requires Computer Vault Worker binding wiring
- Cross-repo deploy coordination
- Still must preserve org/case authorization checks

## Recommendation

Prefer **service binding** for production when approved.  
**Do not migrate automatically** under KC-028.1 — staging cert remains on public HTTPS.

## Preferred production topology (future)

```
Core Worker
  → service binding
  → Computer Vault Worker
  → R2 / search internals
```

Keep container outbound internet disabled for Vault once binding is live; retain public HTTPS only as break-glass.
