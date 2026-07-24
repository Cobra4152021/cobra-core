# Protocol V1 — Deployment Assets (prepare only)

**Phase 5B.1B** — do **not** deploy, provision GPU, or expose publicly from this document.

## Launch (local / loopback)

```bash
# PowerShell / bash — from repo root
export COBRA_CORE_AUTH_SECRET="<dev-only-fake-secret>"
export COBRA_INFERENCE_MODE=mock
export COBRA_CORE_HOST=127.0.0.1
export COBRA_CORE_PORT=8080
export COBRA_PROTOCOL_VERSION=1
export COBRA_COMPATIBILITY_VERSION=1
cobra-protocol-v1
# or: python scripts/run_protocol_v1_server.py
```

Windows helper: `scripts/protocol_v1_launch.ps1`

## Readiness

`python scripts/protocol_v1_ready.py` — GET `/health` expects HTTP 200 and `reason` in `{ok, model_not_loaded, model_unavailable}` with auth.

Mock mode: `reason=ok` means protocol server is ready for mock inference.

Real local mode: `reason=ok` only when model is loaded; `model_not_loaded` means process up but not inference-ready.

## Liveness

`python scripts/protocol_v1_live.py` — TCP connect to configured host/port succeeds.

## Smoke

`python scripts/smoke_protocol_v1.py` — mock-only local smoke; writes sanitized evidence under `evaluations/diagnostics/protocol-v1-smoke/`.

## Shutdown

Send SIGINT/SIGTERM to the server process, or Ctrl+C. Server attempts graceful `httpd.shutdown()`.

Cleanup: stop process; no cloud resources created by this phase. Delete local smoke evidence if desired.

## GPU / disk (real mode, optional)

| Item | Expectation |
| --- | --- |
| Model | Qwen3-8B acquired artifacts (existing Core path) |
| Quantization | NF4 via existing `QwenLocalAdapter` (unchanged) |
| GPU | Optional; not provisioned by this phase |
| Disk | Existing model cache / artifact root from acquisition |
| TLS | Terminate at reverse proxy if ever exposed; local smoke is HTTP loopback |
| Auth | `COBRA_CORE_AUTH_SECRET` from env/secret store only |
| Cost ceiling | No cloud spend in this phase; keep `COBRA_INFERENCE_MODE=mock` unless intentionally loading local weights |

## Authentication setup

1. Generate a high-entropy secret offline.
2. Set `COBRA_CORE_AUTH_SECRET` in the process environment (never commit).
3. Computer client must use the same secret as Bearer token.

## Cancellation limitation

Client disconnect / cancel event stops **response delivery**. Mock inference cooperatively checks cancel between sleep slices. Local GPU `generate()` is **not** hard-cancelled; timed-out workers may finish in the background with results discarded.
