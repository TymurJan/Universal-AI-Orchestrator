# stop_bot.ps1
# Зупиняє всі процеси Telegram-бота ГО "Талан ЮА"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ГО 'ТАЛАН ЮА' — Зупинка Telegram-бота" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Завершуємо cmd процеси, які мають у заголовку назву нашого вікна або CommandLine містить нашого бота
$cmdProcs = Get-CimInstance Win32_Process -Filter "name = 'cmd.exe'" | Where-Object { 
    $_.MainWindowTitle -like "*ГО ТАЛАН ЮА*" -or $_.CommandLine -like "*_start_bot.bat*"
}
if ($cmdProcs) {
    Write-Host "Зупиняю цикл перезапуску (cmd.exe)." -ForegroundColor Yellow
    foreach ($p in $cmdProcs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

# 2. Завершуємо процес за PID з bot.pid
if (Test-Path "bot.pid") {
    $pidVal = Get-Content "bot.pid" -Raw
    $pidVal = $pidVal.Trim()
    if ($pidVal -and (Get-Process -Id $pidVal -ErrorAction SilentlyContinue)) {
        Write-Host "Зупиняю процес Python за PID: $pidVal." -ForegroundColor Yellow
        Stop-Process -Id $pidVal -Force
    }
    Remove-Item "bot.pid" -Force -ErrorAction SilentlyContinue
}

# 3. Додатковий захист: шукаємо процеси python, які запустили bot.py
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $procId = $_.Id
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $procId").CommandLine
    $cmdLine -like "*bot.py*"
}
if ($pythonProcs) {
    Write-Host "Зупиняю додаткові процеси Python." -ForegroundColor Yellow
    $pythonProcs | Stop-Process -Force
}

Write-Host "✅ Всі фонові процеси бота успішно завершено." -ForegroundColor Green
