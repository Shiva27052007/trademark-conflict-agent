@echo off
title Trademark Screening Frontend Dev Server
echo ========================================================
echo Starting Trademark Conflict Screening Agent Frontend...
echo ========================================================
cd /d "%~dp0\frontend"
npm run dev -- --host 127.0.0.1 --port 5173
pause
