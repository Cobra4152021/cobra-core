# Configuration — Cobra Core v0.9.0-rc1

## Required

| Variable | Purpose |
| --- | --- |
| `COBRA_CORE_AUTH_SECRET` | Bearer secret (required to serve) |

## Protocol identity (frozen)

| Variable | Allowed |
| --- | --- |
| `COBRA_PROTOCOL_VERSION` | `1` only |
| `COBRA_COMPATIBILITY_VERSION` | `1` only |

## Server

| Variable | Default | Notes |
| --- | --- | --- |
| `COBRA_CORE_HOST` | `127.0.0.1` | Loopback only |
| `COBRA_CORE_PORT` | `8080` | |
| `COBRA_CORE_MODEL` | `cobra-core-qwen3-8b` | Identity string |
| `COBRA_CORE_REVISION` | git short / `local-dev` | |
| `COBRA_CORE_GIT_SHA` | auto from git | |
| `COBRA_CORE_TIMEOUT_MS` | `120000` | |
| `COBRA_CORE_MAX_CONTEXT` | unset | Optional hard cap |
| `COBRA_CORE_MAX_OUTPUT_TOKENS` | unset | Optional hard cap |
| `COBRA_INFERENCE_MODE` | `mock` | `mock\|echo\|test\|local\|qwen-local` |
| `COBRA_CORE_LOG_LEVEL` | `INFO` | Structured logs; secrets redacted |

## RC1 controls

| Variable | Default | Notes |
| --- | --- | --- |
| `COBRA_CORE_ENABLED` | `true` | Kill switch (`false` → `provider_disabled`) |
| `COBRA_CORE_MAX_CONCURRENT` | `1` | In-flight completions |
| `COBRA_CORE_DAILY_REQUEST_LIMIT` | unset | Process-local UTC day quota |
| `COBRA_CORE_METRICS_ENABLED` | `true` | Enables `GET /metrics` |

Never commit real secrets. Prefer environment / secret manager injection.
