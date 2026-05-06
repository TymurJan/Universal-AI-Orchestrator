@echo off
setlocal
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"
".venv\Scripts\python.exe" "talan\autobot\backup_manager.py"
endlocal
exit
