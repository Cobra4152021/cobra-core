# Known Limitations — v0.9.0-rc1

1. **Loopback only** — no public bind in this RC.
2. **Single shared Bearer secret** — no per-user identity inside Core process.
3. **Process-local quotas/concurrency** — not durable across restarts or multi-process.
4. **CobraBench not re-run** — official score remains **0.840**; status `prepared-not-run`.
5. **Real-GPU soak / second Phase 4 wave** — requires separate GPU authorization and host.
6. **Local GPU generate cancellation** — cooperative for mock; local generate may finish in background after timeout discard.
7. **One-shot streaming only** — not native SSE (Protocol V1 allowed behavior).
8. **No multi-tenant org isolation inside Core** — org isolation is enforced by Cobra Computer Worker.
