$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$verificationRoot = Join-Path $repoRoot "data\verification"
$asOf = "2026-08-07"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $repoRoot
try {
    Invoke-Checked "Python tests" { python -m pytest -q }
    Invoke-Checked "Reset deterministic demo data" {
        python -m scripts.seed_demo --reset --root $verificationRoot --asof $asOf
    }
    Invoke-Checked "Repeat seed to verify idempotency" {
        python -m scripts.seed_demo --root $verificationRoot --asof $asOf
    }
    Invoke-Checked "Synthetic pipeline health" {
        python -m scripts.health_check --root $verificationRoot --asof $asOf
    }
    Invoke-Checked "Frontend tests" { npm.cmd test --prefix console/web }
    Invoke-Checked "Frontend production build" { npm.cmd run build --prefix console/web }
    Invoke-Checked "Patch whitespace check" { git diff --check }

    Write-Host "`nAll public companion checks passed." -ForegroundColor Green
}
finally {
    Pop-Location
}
