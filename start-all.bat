@echo off
title Trademark Screening App - Full Stack
echo ========================================================
echo Starting BOTH Backend and Frontend Servers...
echo ========================================================
cd /d "%~dp0"
start "Trademark Backend (Port 8000)" cmd /k "C:\Python314\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
start "Trademark Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"
echo.
echo Both servers have been launched in separate terminal windows!
echo - Backend API:  http://127.0.0.1:8000/docs
echo - Frontend UI:  http://localhost:5173/
echo ========================================================
