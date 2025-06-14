# Define the path for your Python script on the network
$pythonScriptPath = "\\10.10.101.10\creative\work\Postbox\01_Config\Postbox_scripts\run_installs.py"
$taskName = "Run Postbox Python Script on Logon"
$taskDescription = "Launches the Postbox Python script (run_installs.py) automatically when a specific user logs on."

# --- Automatic User Detection ---
# The script automatically detects the current user to set up the task.
# The task will be triggered on this user's logon and will run under their account.
$userNameToTrigger = $env:USERNAME
$actionUser = $userNameToTrigger
# -----------------------------------------------------

# Get the directory of the Python script for the 'Start In' argument
$workingDirectory = Split-Path -Path $pythonScriptPath -Parent

# Check if the Python script exists at the specified path
if (-not (Test-Path $pythonScriptPath)) {
    Write-Error "Python script not found at '$pythonScriptPath'. Please verify the network path and your connection."
    exit 1
}

Write-Host "Configuring Scheduled Task: '$taskName'"
Write-Host "Python Script to Run: '$pythonScriptPath'"
Write-Host "Trigger User:           '$userNameToTrigger'"
Write-Host "Run As User:            '$actionUser'"
Write-Host "---"

# Create a Scheduled Task Action to run the Python script.
# -Execute uses 'py.exe' (the Windows Python Launcher) which should be in your system's PATH.
# -Argument is the full path to your .py script.
$action = New-ScheduledTaskAction -Execute "py.exe" -Argument $pythonScriptPath -WorkingDirectory $workingDirectory

# Create a Scheduled Task Trigger (on user logon)
$trigger = New-ScheduledTaskTrigger -AtLogon -User $userNameToTrigger

# Create Scheduled Task Settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register the Scheduled Task
try {
    # The -Principal is set to the specified user with default (Limited) privileges.
    # -RunLevel is not set to 'Highest' as requested.
    Register-ScheduledTask -TaskName $taskName `
        -Description $taskDescription `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal (New-ScheduledTaskPrincipal -UserId $actionUser -RunLevel Limited) `
        -Force # Use -Force to overwrite an existing task with the same name

    Write-Host "`nScheduled Task '$taskName' created successfully."
    Write-Host "The Python script will run with standard privileges when user '$userNameToTrigger' logs on."
    Write-Host "To test, log off and back on with the specified user account."

} catch {
    Write-Error "Failed to create the scheduled task. Error: $($_.Exception.Message)"
    Write-Error "Ensure you have the necessary permissions to create scheduled tasks."
}