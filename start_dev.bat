@echo off
echo ===================================================================
echo Starting CanteenIQ Enterprise Platform
echo (MongoDB Atlas + ML Engine + FastAPI Backend + React Frontend)
echo ===================================================================

echo [1/2] Launching Python FastAPI Backend Server (Port 8000)...
start "CanteenIQ Backend" cmd /k "cd backend && ..\.venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload"

echo [2/2] Launching React Vite Frontend Application (Port 5173)...
start "CanteenIQ Frontend" cmd /k "cd frontend01 && npm run dev"

echo.
echo CanteenIQ services launched!
echo Management Dashboard: http://localhost:5173/dashboard
echo Student Marketplace:  http://localhost:5173/surplus-marketplace
echo Backend API Docs:     http://localhost:8000/docs
echo System Status:        http://localhost:8000/api/system/status
echo ===================================================================
