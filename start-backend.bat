@echo off
title Trademark Screening Backend Server
echo ========================================================
echo Starting Trademark Conflict Screening Agent Backend...
echo ========================================================
cd /d "%~dp0"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
