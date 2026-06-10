<#
.SYNOPSIS
    A11ySense AI — One-command dependency installer for the full backend stack.

.DESCRIPTION
    Installs all Python dependencies for all 6 microservices from the
    centralized common/requirements/ directory.

    All packages are resolved and de-duplicated by pip automatically.
    Shared dependencies (fastapi, sqlalchemy, etc.) are installed only once.

.USAGE
    From the backend/ directory:
        .\install.ps1

    With a specific Python/pip:
        .\install.ps1 -PipCmd "python -m pip"

    Upgrade all packages to latest pinned versions:
        .\install.ps1 -Upgrade

.PARAMETER PipCmd
    The pip command to use. Defaults to "pip".

.PARAMETER Upgrade
    If set, passes --upgrade flag to pip.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Upgrade
    .\install.ps1 -PipCmd "python -m pip"
#>

param(
    [string]$PipCmd = "pip",
    [switch]$Upgrade
)

$ErrorActionPreference = "Stop"

# Resolve the backend root (directory this script lives in)
$BackendRoot = $PSScriptRoot
$MasterRequirements = Join-Path $BackendRoot "common\requirements\all.txt"

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  A11ySense AI — Backend Dependency Installer" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Verify requirements file exists
if (-Not (Test-Path $MasterRequirements)) {
    Write-Host "[ERROR] Master requirements file not found:" -ForegroundColor Red
    Write-Host "        $MasterRequirements" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Installing from: common\requirements\all.txt" -ForegroundColor Green
Write-Host "[INFO] pip command:      $PipCmd" -ForegroundColor Green
if ($Upgrade) {
    Write-Host "[INFO] Mode:             UPGRADE (--upgrade)" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Mode:             INSTALL (pinned versions)" -ForegroundColor Green
}
Write-Host ""

# Build pip command
$PipArgs = @("install", "-r", $MasterRequirements)
if ($Upgrade) {
    $PipArgs += "--upgrade"
}

Write-Host "Running: $PipCmd $($PipArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

# Execute
& $PipCmd @PipArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Green
    Write-Host "  All dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Services ready to run:" -ForegroundColor Green
    Write-Host "    Gateway   → uvicorn app.main:app --port 8000 (in services/gateway)" -ForegroundColor White
    Write-Host "    Agent     → uvicorn app.main:app --port 8001 (in services/agent)" -ForegroundColor White
    Write-Host "    Reporting → uvicorn app.main:app --port 8002 (in services/reporting)" -ForegroundColor White
    Write-Host "    Crawler   → uvicorn app.main:app --port 8003 (in services/crawler)" -ForegroundColor White
    Write-Host "    Analyzer  → uvicorn app.main:app --port 8004 (in services/analyzer)" -ForegroundColor White
    Write-Host "    LLM       → uvicorn app.main:app --port 8005 (in services/llm)" -ForegroundColor White
    Write-Host "=========================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] pip install failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
