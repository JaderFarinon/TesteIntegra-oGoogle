tskill "powershell.exe"

# Caminho base
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Backend
$backendPath = Join-Path $root "backend"
Start-Process "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; if (!(Test-Path '.venv')) { python -m venv .venv }; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload"

# Frontend
$frontendPath = Join-Path $root "frontend"
Start-Process "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm install; npm run dev"