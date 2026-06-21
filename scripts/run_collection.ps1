# DataOS - Scheduled collection wrapper
# Runs the collection pipeline and logs output, for use with Windows Task Scheduler.

$workspace = "C:\Users\patri\OneDrive\Desktop\aios-starter-kit"
$python = Join-Path $workspace ".venv\Scripts\python.exe"
$script = Join-Path $workspace "scripts\collect.py"
$log = Join-Path $workspace "data\collect.log"

Set-Location $workspace
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] Starting scheduled collection" | Out-File -FilePath $log -Append -Encoding utf8

& $python $script 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
