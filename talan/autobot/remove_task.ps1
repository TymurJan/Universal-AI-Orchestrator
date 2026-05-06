$ProgressPreference = 'SilentlyContinue'
$TaskName = "AntigravityBotTask"
try {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "Scheduled Task '$TaskName' removed." -ForegroundColor Yellow
    }
} catch {
    # Silently ignore if already removed or no permissions
}
