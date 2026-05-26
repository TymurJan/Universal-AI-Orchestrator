@echo off
chcp 65001 >nul
echo ============================================
echo   ГО "ТАЛАН ЮА" — Зупинка Telegram-бота
echo ============================================

:: 1. Зупиняємо cmd.exe з вікном циклу перезапуску (як видимі, так і приховані)
taskkill /FI "WINDOWTITLE eq ГО ТАЛАН ЮА*" /F >nul 2>&1
wmic process where "CommandLine like '%%_start_bot.bat%%'" call terminate >nul 2>&1

:: 2. Зупиняємо процес Python за PID із bot.pid
if exist "bot.pid" (
    set /p BOT_PID=<bot.pid
    echo Знайдено PID бота: %BOT_PID%
    taskkill /PID %BOT_PID% /F >nul 2>&1
    del bot.pid
)

:: 3. Додатковий захист: завершення будь-яких процесів python, що виконують bot.py
wmic process where "CommandLine like '%%bot.py%%'" call terminate >nul 2>&1

echo.
echo ✅ Всі фонові процеси бота успішно завершено.
timeout /t 2 >nul
