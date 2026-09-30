@echo off
title BharatSignal Dashboard
echo.
echo  ======================================
echo   BharatSignal Command Center
echo   Starting local server...
echo  ======================================
echo.
cd /d "%~dp0"
start "" "http://localhost:8080"
echo  Dashboard will open in your browser.
echo  Server running at: http://localhost:8080
echo  Press CTRL+C to stop the server.
echo.
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m http.server 8080 --directory apps/intelligence/dashboard
) else (
    python -m http.server 8080 --directory apps/intelligence/dashboard
)
pause
