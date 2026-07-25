# Changelog

All notable changes to Cobra Core are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0rc1] — 2026-07-25

### Added

- Protocol V1 process kill switch via `COBRA_CORE_ENABLED`
- In-process admission control: `COBRA_CORE_MAX_CONCURRENT`, `COBRA_CORE_DAILY_REQUEST_LIMIT`
- In-process metrics registry + authenticated `GET /metrics` (Prometheus text)
- RC1 control tests including offline mock soak (100 requests)
- GitHub Actions CI (lint, mypy, pytest, protocol conformance, wheel build/install)
- RC1 release package under `docs/releases/v0.9.0-rc1/`

### Changed

- Package version set to `0.9.0rc1`
- Protocol error mapping documents `rate_limited` (429)
- Quality fixes: order-independent CobraBench isolation test; mypy/ruff clean in supported scope

### Security

- Metrics and completions remain Bearer-authenticated
- Metrics contain counters only (no prompts, responses, secrets, cookies, JWTs)

### Known limitations

- CobraBench remains `prepared-not-run`; official score **0.840** unchanged
- Real-GPU soak / repeated Phase 4 capability validation require separate GPU authorization
- Protocol V1 remains loopback-only; public exposure is out of scope for RC1
- Daily quota / concurrency counters are process-local (not durable across restarts)

## [0.1.0] — prior

Initial model-lab and Protocol V1 integration builds prior to RC packaging.
