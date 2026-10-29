Write-Host "===================================================================" -ForegroundColor Green
Write-Host "Starting CanteenIQ Enterprise Platform" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Green

Write-Host "[1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python -m uvicorn main:app --port 8000 --reload"

Write-Host "[2/2] Starting React Vite Frontend on http://localhost:5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Platform URLs:" -ForegroundColor Yellow
Write-Host " • Manager Dashboard:    http://localhost:5173/dashboard" -ForegroundColor White
Write-Host " • Student Marketplace:  http://localhost:5173/surplus-marketplace" -ForegroundColor White
Write-Host " • OpenAPI Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================================" -ForegroundColor Green
