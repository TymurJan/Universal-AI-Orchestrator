@echo on
chcp 65001 >nul
title ГО ТАЛАН ЮА — Telegram Bot (Antigravity)
echo ============================================
echo    ГО "ТАЛАН ЮА" — @tymur_jan_bot
echo    Запуск через _start_bot.bat...
echo ============================================
echo.

:loop
cd /d "d:\ГО Талан UA\Talan UA Antigravity manager"
uv run python bot.py

echo.
echo Бот упав або був зупинений. Перезапуск через 5 секунд...
timeout /t 5
goto loop

 