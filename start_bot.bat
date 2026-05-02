@echo off
chcp 65001 >nul
title ГО ТАЛАН ЮА — Telegram Bot

echo ============================================
echo    ГО "ТАЛАН ЮА" — @tymur_jan_bot
echo    Запуск Antigravity Manager Bot...
echo ============================================
echo.
echo Для зупинки натисніть Ctrl+C
echo.

cd /d "d:\ГО Талан UA\Talan UA Antigravity manager"
uv run python bot.py

echo.
echo Бот зупинено. Натисніть будь-яку клавішу для закриття.
pause >nul
