@echo off
REM Example: Predict USA vs Paraguay with bookmaker odds, show all results
set PYTHONIOENCODING=utf-8
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" --match "USA" "Paraguay" --all
