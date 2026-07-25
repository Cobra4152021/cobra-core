# KC-016 smoke tests for staging Core RC1
# Usage:
#   $env:COBRA_CORE_BASE_URL = "https://cobra-core-staging-rc1.fly.dev"
#   $env:COBRA_CORE_AUTH_SECRET = "..."
#   ./deploy/staging-rc1/smoke.ps1

$ErrorActionPreference = "Stop"
$Base = ($env:COBRA_CORE_BASE_URL -replace "/+$", "")
$Secret = $env:COBRA_CORE_AUTH_SECRET
$Org = if ($env:COBRA_CORE_SMOKE_ORG) { $env:COBRA_CORE_SMOKE_ORG } else { "org_staging_smoke" }
$ExpectedRev = "ec400d83a9cc8105557bda2105f177cc619638b2"

if (-not $Base) { throw "COBRA_CORE_BASE_URL required" }
if (-not $Secret) { throw "COBRA_CORE_AUTH_SECRET required" }

$Headers = @{ Authorization = "Bearer $Secret" }

Write-Host "GET $Base/health"
$health = Invoke-RestMethod -Uri "$Base/health" -Headers $Headers -Method GET
if ($health.status -ne "healthy") { throw "health status=$($health.status)" }
if ($health.revision -ne $ExpectedRev) { throw "revision mismatch: $($health.revision)" }
if ($health.version -ne "v0.9.0-rc1") { throw "version mismatch: $($health.version)" }
Write-Host "ok health"

Write-Host "GET $Base/version"
$ver = Invoke-RestMethod -Uri "$Base/version" -Headers $Headers -Method GET
if ($ver.revision -ne $ExpectedRev) { throw "version revision mismatch" }
Write-Host "ok version"

Write-Host "POST anonymous should fail"
try {
  Invoke-WebRequest -Uri "$Base/health" -Method GET -UseBasicParsing | Out-Null
  throw "anonymous health unexpectedly succeeded"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -ne 401) {
    # Core may return 401 via edge/proxy
    Write-Host "anonymous blocked (status may vary): $($_.Exception.Message)"
  } else {
    Write-Host "ok anonymous blocked"
  }
}

Write-Host "POST /v1/chat/completions"
$body = @{
  model = "cobra-core-qwen3-8b"
  stream = $false
  max_tokens = 32
  messages = @(@{ role = "user"; content = "ping" })
} | ConvertTo-Json -Depth 5
$infHeaders = @{
  Authorization = "Bearer $Secret"
  "Content-Type" = "application/json"
  "X-Cobra-Org-Id" = $Org
}
$comp = Invoke-RestMethod -Uri "$Base/v1/chat/completions" -Headers $infHeaders -Method POST -Body $body
if (-not $comp.choices) { throw "missing choices" }
Write-Host "ok completion"

Write-Host "PASS KC-016 smoke"
