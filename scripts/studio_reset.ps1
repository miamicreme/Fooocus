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

$StudioLog = Join-Path $LogDir "latest-ai-studio.log"
$EngineLog = Join-Path $LogDir "latest-fooocus-engine.log"

$PythonCmd = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonCmd = ".venv\Scripts\python.exe"
}

function Test-PortListening {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Show-LogTail {
    param(
        [string]$Name,
        [string]$LogPath
    )

    if (-not (Test-Path $LogPath)) {
        Write-Warning "$Name log does not exist yet: $LogPath"
        return
    }

    Write-Host ""
    Write-Host "Last lines from $Name log: $LogPath"
    Write-Host "------------------------------------------------------------"
    Get-Content -Path $LogPath -Tail 80 -ErrorAction SilentlyContinue
    Write-Host "------------------------------------------------------------"
}

function Wait-PortReady {
    param(
        [string]$Name,
        [int]$Port,
        [int]$TimeoutSeconds,
        [string]$LogPath
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastNotice = Get-Date

    while ((Get-Date) -lt $deadline) {
        if (Test-PortListening $Port) {
            Write-Host "$Name is ready on http://127.0.0.1:$Port"
            return $true
        }

        if (((Get-Date) - $lastNotice).TotalSeconds -ge 5) {
            Write-Host "Waiting for $Name on port ${Port}..."
            $lastNotice = Get-Date
        }

        Start-Sleep -Milliseconds 500
    }

    Write-Warning "$Name did not become ready on port ${Port} within $TimeoutSeconds seconds."
    Show-LogTail $Name $LogPath
    return $false
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
        if (Wait-PortReady "AI Studio" 7872 90 $StudioLog) {
            Start-Process "http://127.0.0.1:7872"
        }
    }
    "cold" {
        Write-Host "Cold reset: stopping Studio and Fooocus, clearing temp session folder, then starting clean."
        Stop-PortProcess 7872
        Stop-PortProcess 7865
        Remove-Item "$env:TEMP\fooocus" -Recurse -Force -ErrorAction SilentlyContinue
        New-Item -ItemType Directory -Path "$env:TEMP\fooocus" -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 2
        Start-FooocusEngine
        $engineReady = Wait-PortReady "Fooocus Engine" 7865 180 $EngineLog
        Start-AIStudio
        $studioReady = Wait-PortReady "AI Studio" 7872 90 $StudioLog
        if ($engineReady -and $studioReady) {
            Start-Process "http://127.0.0.1:7872"
        }
    }
    default {
        Write-Host "Start/Open: starting missing services and opening AI Studio."
        Start-FooocusEngine
        $engineReady = Wait-PortReady "Fooocus Engine" 7865 180 $EngineLog
        Start-AIStudio
        $studioReady = Wait-PortReady "AI Studio" 7872 90 $StudioLog
        if ($engineReady -and $studioReady) {
            Start-Process "http://127.0.0.1:7872"
        }
    }
}

Write-Host ""
Write-Host "AI Studio:      http://127.0.0.1:7872"
Write-Host "Fooocus Engine: http://127.0.0.1:7865"
Write-Host "Logs:           $LogDir"
Write-Host "Latest Studio:  logs\studio\latest-ai-studio.log"
Write-Host "Latest Engine:  logs\studio\latest-fooocus-engine.log"
