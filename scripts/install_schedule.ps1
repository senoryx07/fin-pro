# Registers a Windows scheduled task that refreshes Fin Pro's data and
# republishes the site every weekday evening after NSE publishes the day's
# bhavcopy.
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_schedule.ps1
#
# Remove it with:
#   Unregister-ScheduledTask -TaskName "Fin Pro Daily Update" -Confirm:$false

param(
    [string]$Time = "19:30"
)

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$script = Join-Path $root "scripts\daily_update.py"

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at $python"
}

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "`"$script`"" `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At $Time

# Run late if the PC was off or asleep at the scheduled time, and never
# start a second copy while one is still running.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask `
    -TaskName "Fin Pro Daily Update" `
    -Description "Refresh Fin Pro data from NSE and publish the site." `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Force | Out-Null

Write-Host "Scheduled 'Fin Pro Daily Update' for $Time on weekdays."
