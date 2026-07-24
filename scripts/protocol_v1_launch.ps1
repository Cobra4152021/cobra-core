# Launch Protocol V1 server on loopback (mock default). Do not expose publicly.
$ErrorActionPreference = "Stop"
if (-not $env:COBRA_CORE_AUTH_SECRET) {
  Write-Error "COBRA_CORE_AUTH_SECRET is required (use a fake local secret)."
}
$env:COBRA_INFERENCE_MODE = if ($env:COBRA_INFERENCE_MODE) { $env:COBRA_INFERENCE_MODE } else { "mock" }
$env:COBRA_CORE_HOST = if ($env:COBRA_CORE_HOST) { $env:COBRA_CORE_HOST } else { "127.0.0.1" }
$env:COBRA_CORE_PORT = if ($env:COBRA_CORE_PORT) { $env:COBRA_CORE_PORT } else { "8080" }
$env:COBRA_PROTOCOL_VERSION = "1"
$env:COBRA_COMPATIBILITY_VERSION = "1"
python -m cobra_core.protocol_v1.cli
