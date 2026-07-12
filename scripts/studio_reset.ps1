param(
    [ValidateSet("start", "refresh", "hot", "cold")]
    [string]$Mode = "start"
)

$ErrorActionPreference = "Continue"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$env:GRADIO_ANALYTICS_ENABLED = "False"
$env:GRADIO_VERSION_CHECK = "False"

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
            Write-Host "Stopping process on port $Port: PID $processId"
            Stop-Process -Id $processId -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not stop PID $processId on port $Port: $($_.Exception.Message)"
        }
    }
}

function Start-CmdWindow {
    param(
        [string]$Title,
        [string]$Command
    )
    Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", "title $Title && $Command") -WorkingDirectory $Root
}

function Start-FooocusEngine {
    if (Test-PortListening 7865) {
        Write-Host "Fooocus engine already appears to be running on http://127.0.0.1:7865"
        return
    }

    if (-not (Test-Path "$env:TEMP\fooocus")) {
        New-Item -ItemType Directory -Path "$env:TEMP\fooocus" | Out-Null
    }

    Start-CmdWindow "Fooocus Engine" "$PythonCmd scripts\run_fooocus_keepalive.py --disable-analytics --disable-in-browser"
    Write-Host "Starting Fooocus engine on http://127.0.0.1:7865"
}

function Start-AIStudio {
    if (Test-PortListening 7872) {
        Write-Host "AI Studio already appears to be running on http://127.0.0.1:7872"
        return
    }

    Start-CmdWindow "AI Studio" "$PythonCmd ai_studio_app.py"
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
