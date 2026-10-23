# Connect your Oracle Fusion pod to Claude Code (read-only "oracle-fusion" MCP server).
# Usage: double-click Connect-Oracle-Fusion.cmd in the project root, or run this script directly.
# It reads pod URL and user from .env, asks for the password with hidden typing,
# and stores the password in Windows Credential Manager only.

$ErrorActionPreference = 'Continue'

# Resolve paths relative to this script
$proj = Split-Path -Parent $MyInvocation.MyCommand.Path        # mcp-servers/fusion-mcp
$root = Split-Path -Parent (Split-Path -Parent $proj)          # repo root (../../)
# Handle case where script IS at mcp-servers/fusion-mcp level
if (-not (Test-Path (Join-Path $root '.env.example'))) {
    $root = Split-Path -Parent $proj
    if (-not (Test-Path (Join-Path $root '.env.example'))) {
        $root = $proj
    }
}

$py   = Join-Path $proj '.venv\Scripts\python.exe'
$uv   = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
if (-not (Test-Path $uv)) {
    # Try system-wide uv
    $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $uv) {
        Write-Host 'uv is not installed. Install it from https://docs.astral.sh/uv/getting-started/installation/' -ForegroundColor Red
        exit 1
    }
}

# --- Read .env file if it exists ---
$envFile = Join-Path $root '.env'
$pod  = ''
$user = ''
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*FUSION_POD_URL\s*=\s*(.+)$')  { $pod  = $Matches[1].Trim().Trim('"').Trim("'") }
        if ($_ -match '^\s*FUSION_USER\s*=\s*(.+)$')      { $user = $Matches[1].Trim().Trim('"').Trim("'") }
    }
}

# --- Prompt for missing values ---
if (-not $pod -or $pod -like '*your-pod*') {
    $pod = Read-Host 'Enter your Fusion pod URL (e.g. https://abcd-dev1.fa.us2.oraclecloud.com)'
}
if (-not $user -or $user -like '*example.com*') {
    $user = Read-Host 'Enter your Fusion user name (e.g. integration.user@company.com)'
}

if (-not $pod -or -not $user) {
    Write-Host 'Pod URL and user name are required. Set them in .env or enter them above.' -ForegroundColor Red
    exit 1
}

# --- Ensure Python venv ---
if (-not (Test-Path $py)) {
    Write-Host 'Python environment missing - building it ...' -ForegroundColor Yellow
    & $uv --directory $proj sync --frozen
    if (-not (Test-Path $py)) {
        Write-Host 'Could not build the Python environment. Is uv installed and Python >= 3.12 available?' -ForegroundColor Red
        exit 1
    }
}
$helper = Join-Path $proj 'fusion_setup_helper.py'

Write-Host ''
Write-Host '[1/3] Saving the pod URL and user name (no password) ...' -ForegroundColor Cyan
& $py $helper config $pod $user
if ($LASTEXITCODE -ne 0) { Write-Host 'Could not save the settings.' -ForegroundColor Red; exit 1 }

Write-Host ''
Write-Host "[2/3] Type the Fusion password for $user and press Enter ..." -ForegroundColor Cyan
& $py $helper store
if ($LASTEXITCODE -ne 0) { Write-Host 'Password was not saved. Run this again.' -ForegroundColor Red; exit 1 }

Write-Host ''
Write-Host '[3/3] Checking and repairing the whole connection ...' -ForegroundColor Cyan
& $py $helper doctor --fix
