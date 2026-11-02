@echo off
setlocal
cd /d "%~dp0"
title Drishti Smart Stick - Flash Vision AI Module V2
cls
echo =================================================================
echo  DRISHTI: FLASHING EDGE IMPULSE VISION AI MODULE V2
echo =================================================================
echo.

:: Detect Python executable
set "PY_CMD="
python --version >nul 2>&1 && set "PY_CMD=python"
if "%PY_CMD%"=="" (
    py -3 --version >nul 2>&1 && set "PY_CMD=py -3"
)
if "%PY_CMD%"=="" (
    if exist "C:\Python315\python.exe" set "PY_CMD=C:\Python315\python.exe"
)
if "%PY_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

if "%PY_CMD%"=="" (
    echo [!] Error: Python not found on this system.
    echo Please install Python and ensure it is added to your PATH.
    pause
    exit /b 1
)

echo [*] Using Python: %PY_CMD%
%PY_CMD% flash_edge_impulse.py
echo.
pause
