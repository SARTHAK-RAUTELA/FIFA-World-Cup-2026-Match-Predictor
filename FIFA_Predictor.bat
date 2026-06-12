@echo off
title FIFA 2026 - Match Prediction Tool
mode con: cols=180 lines=50
color 0B
chcp 65001 > nul

cd /d "%~dp0"

echo.
echo  ============================================================
echo    FIFA 2026 Match Prediction Tool - Starting...
echo  ============================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

if not exist ".venv\Scripts\python.exe" (
    echo  [ERROR] Virtual environment not found.
    echo  Please run setup first:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" launcher.py

echo.
echo  ============================================================
echo   Session ended. Press any key to close this window.
echo  ============================================================
pause > nul
