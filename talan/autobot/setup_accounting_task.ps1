$ProgressPreference = 'SilentlyContinue'
$TaskName = "AntigravityAccountingWorker"
$ScriptPath = "d:\ГО Талан UA\Talan UA Antigravity manager\talan\autobot\accounting_worker.py"
$PythonPath = "d:\ГО Талан UA\Talan UA Antigravity manager\.venv\Scripts\python.exe"

# Команда для тихого запуску через pythonw (щоб не було вікна консолі)
$PythonW = "d:\ГО Талан UA\Talan UA Antigravity manager\.venv\Scripts\pythonw.exe"

$Action = New-ScheduledTaskAction -Execute "$PythonW" -Argument "`"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "Scheduled Task '$TaskName' created successfully." -ForegroundColor Green
    Write-Host "The Accounting Worker will now start automatically on Login." -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to create task. Please run code in a terminal with Admin rights." -ForegroundColor Red
}
