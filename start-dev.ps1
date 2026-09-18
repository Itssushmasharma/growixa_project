# Growixa One-Click Full Stack Local Dev Starter
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Growixa Full Stack Services  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Local PostgreSQL on port 5433 if not running
$pgListening = Get-NetTCPConnection -LocalPort 5433 -State Listen -ErrorAction SilentlyContinue
if (-not $pgListening) {
    Write-Host "[1/3] Starting Local PostgreSQL (port 5433)..." -ForegroundColor Yellow
    & "C:\Program Files\PostgreSQL\14\bin\pg_ctl.exe" -D "$Root\.pgdata" -o "-p 5433" -l "$Root\.pgdata\postgres.log" start
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/3] Local PostgreSQL is already running on port 5433." -ForegroundColor Green
}

# 2. Start FastAPI Backend on port 8000 if not running
$apiListening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $apiListening) {
    Write-Host "[2/3] Starting FastAPI Backend (port 8000)..." -ForegroundColor Yellow
    Start-Process -FilePath "$Root\apps\api\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn growixa_api.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "$Root\apps\api"
    Start-Sleep -Seconds 3
} else {
    Write-Host "[2/3] FastAPI Backend is already running on port 8000." -ForegroundColor Green
}

# 3. Start Next.js Frontend on port 3000
$webListening = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $webListening) {
    Write-Host "[3/3] Starting Next.js Web App (port 3000)..." -ForegroundColor Yellow
    Set-Location -Path "$Root\apps\web"
    npm run dev
} else {
    Write-Host "[3/3] Next.js Web App is already running on http://localhost:3000." -ForegroundColor Green
    Write-Host ""
    Write-Host "All services are LIVE!" -ForegroundColor Cyan
    Write-Host "Open in browser: http://localhost:3000/login" -ForegroundColor Cyan
}
