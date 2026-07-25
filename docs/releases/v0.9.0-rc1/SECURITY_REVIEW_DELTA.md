# Security Review Delta — v0.9.0-rc1

Baseline: `docs/security/SECURITY_REVIEW.md` (lab + Protocol V1).

## Changes in RC1

| Area | Assessment |
| --- | --- |
| Auth | Unchanged Bearer constant-time compare; required for `/health`, completions, `/metrics` |
| Kill switch | `COBRA_CORE_ENABLED=false` denies completions with `provider_disabled` |
| Admission | Concurrency + optional daily quota reduce overload/abuse on loopback server |
| Metrics | Counters only; no prompt/response/secret fields |
| Protocol schemas | Unchanged (hashes verified) |
| Bind address | Still loopback-enforced |
| Logging | Existing redaction retained |

## Dependency review (RC1)

Runtime dependencies remain minimal:

- `pydantic>=2.7,<3`
- `PyYAML>=6.0,<7`

Dev/build: pytest, ruff, mypy, types-PyYAML, build.

Optional inference extras (torch/transformers/…) are **not** required for mock RC software certification.

No new network clients were added to the Protocol V1 server path.

## Residual risks

- Shared bearer is a single secret (rotate via env).
- `/metrics` discloses traffic volume to anyone with the bearer.
- Process-local quotas are not a billing control.

## Verdict

Security posture for **loopback RC1 software package**: acceptable with documented residual risks.  
Not a production internet exposure approval.
