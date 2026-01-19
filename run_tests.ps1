# Test runner for claude-code-auto-resume (Windows PowerShell)
# Uses uv for isolated environment management

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = "$ScriptDir\.test-venv"

Write-Host "Running tests for claude-code-auto-resume..."
Write-Host ""

# Check for uv
$UvPath = Get-Command uv -ErrorAction SilentlyContinue
if (-not $UvPath) {
    Write-Host "Error: 'uv' is not installed." -ForegroundColor Red
    Write-Host "Install it with: powershell -c 'irm https://astral.sh/uv/install.ps1 | iex'"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating test virtual environment..."
    uv venv $VenvDir
}

# Activate virtual environment
$ActivateScript = "$VenvDir\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
} else {
    Write-Host "Error: Could not find activation script at $ActivateScript" -ForegroundColor Red
    exit 1
}

# Install pytest if not present
try {
    python -c "import pytest" 2>$null
} catch {
    Write-Host "Installing pytest..."
    uv pip install pytest
}

Write-Host ""
Write-Host "Running pytest..."
Write-Host "========================================"

# Run tests with verbose output
Set-Location $ScriptDir
$TestArgs = @("tests/", "-v") + $args
python -m pytest @TestArgs

$TestExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================"
if ($TestExitCode -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed." -ForegroundColor Red
}

exit $TestExitCode
