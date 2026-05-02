@echo off
title Universal AI: Omni-Check
echo 🔍 Initializing Omni-Resilience Check...

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [! ] CRITICAL ERROR: Python not found.
    echo [i ] Fix: Install Python from python.org and check 'Add to PATH'.
    echo.
    pause
    exit /b
)

:: 2. Launch
python orchestrator.py

echo.
echo --------------------------------------------------
echo [i] Session reached a natural conclusion.
pause
