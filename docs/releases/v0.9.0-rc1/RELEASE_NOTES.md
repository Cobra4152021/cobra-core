# Cobra Core v0.9.0-rc1 — Release Notes

**Tag intent:** `v0.9.0-rc1`  
**Package version:** `0.9.0rc1`  
**Protocol:** V1 / Compatibility 1 / Schema 1.0.0  
**schemaHash:** `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3`  
**fixtureHash:** `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7`  
**Official CobraBench score:** `0.840` (unchanged)  
**CobraBench status:** `prepared-not-run`

## Scope

This RC certifies the **Cobra Core software package**:

- Model lab tooling and frozen Protocol V1 governance
- Loopback Protocol V1 inference server (mock + optional local Qwen path)
- RC1 process controls: kill switch, concurrency, daily quota, metrics
- Reproducible offline quality gates (pytest, ruff, mypy, conformance, wheel build)

This RC does **not**:

- Designate a production SaaS deployment
- Change Protocol V1 schemas or fixtures
- Replace the official 0.840 score
- Authorize training
- Require a live GPU CobraBench run (optional; separately authorized)

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
# Or from a built wheel:
# pip install dist/cobra_core-0.9.0rc1-*.whl
```

## Configure (Protocol V1 server)

See `.env.example` and `docs/releases/v0.9.0-rc1/CONFIGURATION.md`.

Minimum:

```bash
export COBRA_CORE_AUTH_SECRET="<secret>"
export COBRA_INFERENCE_MODE=mock
export COBRA_CORE_ENABLED=true
export COBRA_CORE_HOST=127.0.0.1
export COBRA_CORE_PORT=8080
cobra-protocol-v1
```

## Verify

```bash
pytest
ruff check src tests scripts
mypy src/cobra_core
cobra-protocol-conformance
python -m build
```

## Rollback

1. Set `COBRA_CORE_ENABLED=false` (kill switch) or stop the process.
2. Rotate/delete `COBRA_CORE_AUTH_SECRET`.
3. Reinstall previous wheel/tag if needed.
4. Confirm `/v1/chat/completions` returns `provider_disabled` or connection refused.

See `docs/releases/v0.9.0-rc1/ROLLBACK.md`.

## Compatibility

- Protocol V1 request/response schemas **unchanged**
- Computer adapters expecting Bearer + `/health` + `/v1/chat/completions` remain compatible
- New optional endpoint: `GET /metrics` (Bearer, Prometheus text) when metrics enabled
