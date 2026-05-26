@echo off
chcp 65001 >nul
cd /d "%~dp0Novy_Shlyakh_Portal\backend"
"..\..\.venv\Scripts\python.exe" bot.py
pause
