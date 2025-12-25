# Run local FastAPI server
# Usage: .\scripts\run_local_api.ps1

$ErrorActionPreference = "Stop"

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please edit .env with your configuration before running." -ForegroundColor Yellow
}

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Green
pip install -q -r requirements.txt

# Run the API
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "API will be available at http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

