$ProgressPreference = 'SilentlyContinue'
$TaskName = "AntigravityBotTask"
$VbsPath = "d:\ГО Талан UA\Talan UA Antigravity manager\talan\autobot\run_bot_silent.vbs"
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force -ErrorAction Stop
    Write-Host "Scheduled Task '$TaskName' created successfully." -ForegroundColor Green
} catch {
    Write-Warning "Failed to create task. Please run as Administrator."
}
