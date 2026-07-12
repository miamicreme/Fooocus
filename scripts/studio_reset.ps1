param(
    [ValidateSet("start", "refresh", "hot", "cold")]
    [string]$Mode = "start"
)

$ErrorActionPreference = "Continue"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$env:GRADIO_ANALYTICS_ENABLED = "False"
$env:GRADIO_VERSION_CHECK = "False"

$LogDir = Join-Path $Root "logs\studio"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$PythonCmd = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonCmd = ".venv\Scripts\python.exe"
}

function Test-PortListening {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Stop-PortProcess {
    param([int]$Port)
    $pids = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($processId in $pids) {
        try {
            Write-Host "Stopping process on port ${Port}: PID $processId"
            Stop-Process -Id $processId -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not stop PID $processId on port ${Port}: $($_.Exception.Message)"
        }
    }
}

function Start-LoggedWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$LogName
    )

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "scripts\run_logged_process.ps1",
        "-Title", $Title,
        "-Command", $Command,
        "-LogName", $LogName
    ) -WorkingDirectory $Root
}

function Start-FooocusEngine {
    if (Test-PortListening 7865) {
        Write-Host "Fooocus engine already appears to be running on http://127.0.0.1:7865"
        return
    }

    if (-not (Test-Path "$env:TEMP\fooocus")) {
        New-Item -ItemType Directory -Path "$env:TEMP\fooocus" | Out-Null
    }

    Start-LoggedWindow "Fooocus Engine" "$PythonCmd scripts\run_fooocus_keepalive.py --disable-analytics --disable-in-browser" "fooocus-engine"
    Write-Host "Starting Fooocus engine on http://127.0.0.1:7865"
}

function Start-AIStudio {
    if (Test-PortListening 7872) {
        Write-Host "AI Studio already appears to be running on http://127.0.0.1:7872"
        return
    }

    Start-LoggedWindow "AI Studio" "$PythonCmd ai_studio_app.py" "ai-studio"
    Write-Host "Starting AI Studio on http://127.0.0.1:7872"
}

switch ($Mode) {
    "refresh" {
        Write-Host "Refreshing browser only. No processes stopped."
        Start-Process "http://127.0.0.1:7872"
    }
    "hot" {
        Write-Host "Hot reset: restarting AI Studio only. Fooocus engine stays warm."
        Stop-PortProcess 7872
        Start-Sleep -Seconds 2
        Start-AIStudio
        Start-Sleep -Seconds 2
        Start-Process "http://127.0.0.1:7872"
    }
    "cold" {
        Write-Host "Cold reset: stopping Studio and Fooocus, clearing temp session folder, then starting clean."
        Stop-PortProcess 7872
        Stop-PortProcess 7865
        Remove-Item "$env:TEMP\fooocus" -Recurse -Force -ErrorAction SilentlyContinue
        New-Item -ItemType Directory -Path "$env:TEMP\fooocus" -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 2
        Start-FooocusEngine
        Start-Sleep -Seconds 12
        Start-AIStudio
        Start-Sleep -Seconds 2
        Start-Process "http://127.0.0.1:7872"
    }
    default {
        Write-Host "Start/Open: starting missing services and opening AI Studio."
        Start-FooocusEngine
        Start-Sleep -Seconds 12
        Start-AIStudio
        Start-Sleep -Seconds 2
        Start-Process "http://127.0.0.1:7872"
    }
}

Write-Host ""
Write-Host "AI Studio:      http://127.0.0.1:7872"
Write-Host "Fooocus Engine: http://127.0.0.1:7865"
Write-Host "Logs:           $LogDir"
Write-Host "Latest Studio:  logs\studio\latest-ai-studio.log"
Write-Host "Latest Engine:  logs\studio\latest-fooocus-engine.log"
