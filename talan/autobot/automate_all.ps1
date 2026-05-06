$ProgressPreference = 'SilentlyContinue'
# Отримуємо корінь проєкту відносно розташування скрипта
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$PythonExe = "$BaseDir\.venv\Scripts\python.exe"

# 1. Задача для Бота (At Logon)
$BotTaskName = "AntigravityBotTask"
$VbsPath = "$BaseDir\talan\autobot\run_bot_silent.vbs"
$BotAction = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""
$BotTrigger = New-ScheduledTaskTrigger -AtLogOn
$BotSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# 2. Задача для Бекапу (Daily at 03:00)
$BackupTaskName = "AntigravityDailyBackup"
$BackupScript = "$BaseDir\talan\autobot\backup_manager.py"
$BackupAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$BackupScript`""
$BackupTrigger = New-ScheduledTaskTrigger -Daily -At 12am

# 3. Задача для Синхронізації KB (Every 4 hours)
$SyncTaskName = "AntigravityKBSync"
$SyncScript = "$BaseDir\talan\autobot\kb_sync.py"
$SyncAction = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$SyncScript`""
$SyncTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4)

# 4. Задача для Web Scout (At Logon)
$ScoutTaskName = "AntigravityWebScout"
$ScoutScript = "$BaseDir\.agents\skills\03-web-scout\web_scout_autostart.pyw"
$ScoutAction = New-ScheduledTaskAction -Execute "pythonw.exe" -Argument "`"$ScoutScript`""
$ScoutTrigger = New-ScheduledTaskTrigger -AtLogOn

Write-Host "`n============================================================" -ForegroundColor White
Write-Host "   КЕРУВАННЯ АВТОМАТИЗАЦІЄЮ - ГО 'ТАЛАН ЮА'" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor White

Write-Host "Цей скрипт зареєструє наступні завдання у планувальнику Windows:" -ForegroundColor Cyan
Write-Host "1. Автозапуск бота при вході в систему."
Write-Host "2. Щоденний бекап проєкту о 00:00 (частинами по 20МБ)."
Write-Host "3. Синхронізація бази знань (Knowledge Base) кожні 4 години."
Write-Host "4. Автономний розвідник (Web Scout) при вході (щопонеділка - пошук нових джерел)."
Write-Host "`nВАЖЛИВО: Переконайтеся, що ви запустили запуск від Адміністратора.`n" -ForegroundColor Yellow

Read-Host "Натисніть Enter, щоб продовжити або Ctrl+C для скасування"

try {
    # Реєстрація задач
    Register-ScheduledTask -TaskName $BotTaskName -Action $BotAction -Trigger $BotTrigger -Settings $BotSettings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "[OK] Задача для Бота (AntigravityBotTask) створена." -ForegroundColor Green

    Register-ScheduledTask -TaskName $BackupTaskName -Action $BackupAction -Trigger $BackupTrigger -Settings $BotSettings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "[OK] Задача для Бекапу (AntigravityDailyBackup) створена. Щодня о 00:00." -ForegroundColor Green

    Register-ScheduledTask -TaskName $SyncTaskName -Action $SyncAction -Trigger $SyncTrigger -Settings $BotSettings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "[OK] Задача для Синхронізації (AntigravityKBSync) створена. Кожні 4 години." -ForegroundColor Green

    Register-ScheduledTask -TaskName $ScoutTaskName -Action $ScoutAction -Trigger $ScoutTrigger -Settings $BotSettings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "[OK] Задача для Web Scout (AntigravityWebScout) створена. При вході." -ForegroundColor Green

    Write-Host "`n[ФІНАЛ] Усі системи успішно автоматизовано!" -ForegroundColor Cyan
} catch {
    Write-Host "`n[!] ПОМИЛКА: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Переконайтеся, що ви запустили скрипт від імені Адміністратора." -ForegroundColor Red
}
