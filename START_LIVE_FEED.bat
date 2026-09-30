@echo off
title BharatSignal Live Ingestion Worker (2-Min Auto-Refresh)
echo.
echo  ======================================================
echo   BharatSignal Automated Live Ingestion Worker
echo   Polling real APIs (USGS, NASA, GDACS, Weather)
echo   Interval: Every 2 minutes (120 seconds)
echo  ======================================================
echo.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m apps.intelligence.live_worker --interval 120
) else (
    python -m apps.intelligence.live_worker --interval 120
)
pause
