# Format code using ruff
# Usage: .\scripts\fmt.ps1

$ErrorActionPreference = "Stop"

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    pip install -q ruff
} else {
    & .\venv\Scripts\Activate.ps1
}

# Install ruff if not available
$ruffInstalled = pip show ruff 2>$null
if (-not $ruffInstalled) {
    Write-Host "Installing ruff..." -ForegroundColor Green
    pip install -q ruff
}

Write-Host "Formatting code with ruff..." -ForegroundColor Green
ruff format api/ worker/

Write-Host "Checking linting..." -ForegroundColor Green
ruff check api/ worker/

Write-Host "Done!" -ForegroundColor Green

