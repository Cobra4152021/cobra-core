# KC-021 — Inference Profiles

## Why profiles

Deployments and Cobra Computer should select a **named capability profile**,
not a vendor. CIAL resolves the profile to an internal provider + model.

## Built-in profiles

| Profile | Internal provider | Model source | Live required |
|---------|-------------------|--------------|---------------|
| `default` | `mock` | wire mock identity (`cobra-core-qwen3-8b`) | no |
| `offline` | `mock` | mock identity | no |
| `research` | `openai` | `OPENAI_MODEL` | yes (staging + live flag + key) |

## Activation

```text
CIAL_PROFILE=default|offline|research
CIAL_LIVE_PROVIDER_ENABLED=false   # must be true for research live path
APP_ENV=staging                    # production never activates live
```

If `research` is selected but the live gate is closed, CIAL forces mock/offline
with route reason `profile_live_unavailable_use_offline` (never silent live).

## Legacy

`CIAL_PROVIDER=mock|openai` still maps to `default|research` when `CIAL_PROFILE`
is unset. Prefer `CIAL_PROFILE` for all new staging config.

## Computer

No Computer change required for this step: Core staging selects the profile via
env/vars. Future Computer wiring should pass a profile name, never a vendor id.
