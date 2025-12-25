# Run tests
# Usage: .\scripts\test.ps1

$ErrorActionPreference = "Stop"

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    pip install -q -r requirements.txt
    pip install -q pytest pytest-cov
} else {
    & .\venv\Scripts\Activate.ps1
}

# Install pytest if not available
$pytestInstalled = pip show pytest 2>$null
if (-not $pytestInstalled) {
    Write-Host "Installing pytest..." -ForegroundColor Green
    pip install -q pytest pytest-cov
}

Write-Host "Running tests..." -ForegroundColor Green
Write-Host ""

# Run tests
pytest api/tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Some tests failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

