@echo off
setlocal
cd /d "%~dp0"
title Drishti Smart Stick - Vision AI V2 Desktop Preview
cls
echo ========================================================
echo  DRISHTI: LAUNCHING VISION AI V2 REAL-TIME PREVIEW
echo ========================================================
echo.

:: Automatically kill any orphaned background flasher processes that lock COM3
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*xmodem_send*' -or $_.CommandLine -like '*flash_edge_impulse*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

:: Detect Python executable (prefer Python 3.13 if installed, fallback to Python 3.15, python, or py -3)
set "PY_CMD="
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)
if "%PY_CMD%"=="" (
    if exist "C:\Python315\python.exe" set "PY_CMD=C:\Python315\python.exe"
)
if "%PY_CMD%"=="" (
    python --version >nul 2>&1 && set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
    py -3 --version >nul 2>&1 && set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    echo [!] Error: Python not found on this system.
    pause
    exit /b 1
)

echo [i] Starting preview with: %PY_CMD%
"%PY_CMD%" preview_drishti_vision.py
if errorlevel 1 (
    echo.
    echo [!] Preview terminated with error code: %errorlevel%
)
echo.
pause
