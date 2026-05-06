# fix_claude.ps1 - Скрипт для налаштування Claude Code
# ГО "Талан ЮА" / Antigravity Manager

Write-Host "--- Налаштування Claude Code ---" -ForegroundColor Cyan

# 1. Отримання ключа з .env
if (Test-Path ".env") {
    $envFile = Get-Content ".env"
    $apiKeyLine = $envFile | Select-String "ANTHROPIC_API_KEY="
    if ($apiKeyLine) {
        $apiKey = $apiKeyLine.ToString().Split("=")[1].Trim()
        [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $apiKey, "User")
        $env:ANTHROPIC_API_KEY = $apiKey
        Write-Host "[OK] ANTHROPIC_API_KEY встановлено у середовище користувача." -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Ключ ANTHROPIC_API_KEY не знайдено в .env" -ForegroundColor Red
    }
} else {
    Write-Host "[ERROR] Файл .env не знайдено." -ForegroundColor Red
}

# 2. Виправлення шляху та створення Alias
$npmPath = "C:\Users\style\AppData\Roaming\npm"
if (Test-Path "$npmPath\claude.cmd") {
    # Створення функції-аліасу для поточної сесії
    function claude { & "$npmPath\claude.cmd" $args }
    Write-Host "[OK] Команда 'claude' тепер доступна у цій сесії." -ForegroundColor Green
    Write-Host "Порада: Додайте '$npmPath' до системного PATH для постійного доступу." -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] claude.cmd не знайдено у $npmPath" -ForegroundColor Red
}

Write-Host "--- Готово! Тепер ви можете запускати 'claude' прямо тут. ---" -ForegroundColor Cyan
