# Скрипт запуску екосистеми 'Новий Шлях'
Write-Host "🚀 Запуск системи автоматизації..." -ForegroundColor Green

$pythonPath = "d:\ГО Талан UA\Talan UA Antigravity manager\.venv\Scripts\python.exe"

# 1. Запуск головного бота
Write-Host "🤖 Запуск Telegram-бота..." -ForegroundColor Cyan
Start-Process $pythonPath -ArgumentList "bot.py" -NoNewWindow

# 2. Запуск планувальника відгуків
Write-Host "⏰ Запуск Планувальника відгуків (48h follow-up)..." -ForegroundColor Yellow
Start-Process $pythonPath -ArgumentList "scheduler.py" -NoNewWindow

# 3. Запуск веб-сервера (API)
Write-Host "🌐 Запуск Веб-сервера (API)..." -ForegroundColor Blue
Start-Process $pythonPath -ArgumentList "server.py" -NoNewWindow

Write-Host "✅ Всі модулі активовано. Система працює в автономному режимі." -ForegroundColor Green
Write-Host "Натисніть Ctrl+C у цьому вікні, щоб зупинити все (якщо процеси запущено не у фоні)."
