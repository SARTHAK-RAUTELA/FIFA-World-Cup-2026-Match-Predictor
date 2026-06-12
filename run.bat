@echo off
REM FIFA 2026 Match Prediction Tool launcher
REM Usage: run.bat [options]
REM   run.bat --match "USA" "Paraguay" --odds --all
REM   run.bat --watch
REM   run.bat --date 2026-06-15

set PYTHONIOENCODING=utf-8
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
