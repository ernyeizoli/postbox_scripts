@echo off
REM Get the directory where this batch script is located
set "ScriptDir=%~dp0"

REM Define the name of your PowerShell script (UPDATED NAME HERE)
set "PsScript=setPBVScriptsScheduel.ps1"

REM Construct the full path to the PowerShell script
set "FullPsScriptPath=%ScriptDir%%PsScript%"

echo Running PowerShell script to configure scheduled task...
echo PowerShell Script Path: %FullPsScriptPath%
echo.

REM Execute the PowerShell script with admin privileges
REM Use quotes around %FullPsScriptPath% to handle spaces in the path if they exist
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%FullPsScriptPath%"

echo.
echo Script execution complete.
pause