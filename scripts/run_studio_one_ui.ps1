param(
    [switch]$StartEngine,
    [switch]$OpenBrowser,
    [int]$EngineWaitSeconds = 180,
    [int]$StudioWaitSeconds = 120,
    [int]$InitialEngineDelaySeconds = 30,
    [int]$EngineStableSeconds = 12
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$PythonCmd = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonCmd = ".venv\Scripts\python.exe"
}

$env:GRADIO_ANALYTICS_ENABLED = "False"
$env:GRADIO_VERSION_CHECK = "False"

$TempFooocus = Join-Path $env:TEMP "fooocus"
New-Item -ItemType Directory -Force -Path $TempFooocus | Out-Null

$LogDir = Join-Path $RepoRoot "logs\studio"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$EngineOutLog = Join-Path $LogDir "latest-fooocus-engine.out.log"
$EngineErrLog = Join-Path $LogDir "latest-fooocus-engine.err.log"
$StudioOutLog = Join-Path $LogDir "latest-ai-studio.out.log"
$StudioErrLog = Join-Path $LogDir "latest-ai-studio.err.log"
Remove-Item $EngineOutLog, $EngineErrLog, $StudioOutLog, $StudioErrLog -Force -ErrorAction SilentlyContinue

function Test-PortOpen {
    param([string]$HostName, [int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $ready = $async.AsyncWaitHandle.WaitOne(1000, $false)
        if (-not $ready) {
            $client.Close()
            return $false
        }
        $client.EndConnect($async)
        $client.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Show-RecentLog {
    param([string]$Label, [string]$OutLog, [string]$ErrLog)
    Write-Host "Recent $Label stdout log: $OutLog"
    if (Test-Path $OutLog) { Get-Content $OutLog -Tail 80 }
    Write-Host "Recent $Label stderr log: $ErrLog"
    if (Test-Path $ErrLog) { Get-Content $ErrLog -Tail 80 }
}

function Wait-PortOpen {
    param(
        [string]$Name,
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSeconds,
        [System.Diagnostics.Process]$ProcessToWatch = $null
    )
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        if ($ProcessToWatch -and $ProcessToWatch.HasExited) {
            Write-Host "$Name process exited before port $Port stayed ready. Exit code: $($ProcessToWatch.ExitCode)"
            return $false
        }
        if (Test-PortOpen -HostName $HostName -Port $Port) {
            Write-Host "$Name is reachable on http://${HostName}:$Port after ${elapsed}s"
            return $true
        }
        Write-Host "Waiting for $Name on port $Port... ${elapsed}s elapsed, $($TimeoutSeconds - $elapsed)s remaining"
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    Write-Host "WARNING: $Name was not reachable on port $Port after ${TimeoutSeconds}s."
    return $false
}

function Test-StableEngine {
    param([System.Diagnostics.Process]$EngineProcess)
    Write-Host "Checking that Fooocus engine stays alive for ${EngineStableSeconds}s..."
    Start-Sleep -Seconds $EngineStableSeconds
    if ($EngineProcess -and $EngineProcess.HasExited) {
        Write-Host "Fooocus engine exited during stability check. Exit code: $($EngineProcess.ExitCode)"
        return $false
    }
    if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7865)) {
        Write-Host "Fooocus engine port 7865 disappeared during stability check."
        return $false
    }
    Write-Host "Checking Fooocus Studio engine health endpoint..."
    $verifyOutput = & $PythonCmd "scripts\verify_studio_engine.py" 2>&1
    $verifyCode = $LASTEXITCODE
    $verifyOutput | ForEach-Object { Write-Host $_ }
    if ($verifyCode -ne 0) {
        Write-Host "Fooocus engine is reachable, but Studio health check failed."
        return $false
    }
    Write-Host "Fooocus engine passed stability and Studio health checks."
    return $true
}

function Watch-Studio {
    param(
        [System.Diagnostics.Process]$StudioProcess,
        [System.Diagnostics.Process]$EngineProcess,
        [bool]$EngineUsable
    )

    Write-Host ""
    Write-Host "Keep this launcher window open while working. Press Ctrl+C here to stop watching."
    Write-Host ""

    $engineExitReported = $false
    try {
        while ($true) {
            if ($StudioProcess -and $StudioProcess.HasExited) {
                Write-Host "AI Studio process exited with code $($StudioProcess.ExitCode)."
                Show-RecentLog -Label "AI Studio" -OutLog $StudioOutLog -ErrLog $StudioErrLog
                break
            }

            if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7872)) {
                Write-Host "AI Studio is no longer reachable on http://127.0.0.1:7872."
                Show-RecentLog -Label "AI Studio" -OutLog $StudioOutLog -ErrLog $StudioErrLog
                break
            }

            if ($EngineProcess -and $EngineProcess.HasExited -and -not $engineExitReported) {
                $engineExitReported = $true
                Write-Host "Fooocus engine process exited with code $($EngineProcess.ExitCode). Generate in Studio will not work until the engine is fixed."
                Show-RecentLog -Label "Fooocus engine" -OutLog $EngineOutLog -ErrLog $EngineErrLog
            }

            if ($EngineUsable -and -not (Test-PortOpen -HostName "127.0.0.1" -Port 7865) -and -not $engineExitReported) {
                $engineExitReported = $true
                Write-Host "Fooocus engine port 7865 is no longer reachable. Generate in Studio will not work until the engine is fixed."
                Show-RecentLog -Label "Fooocus engine" -OutLog $EngineOutLog -ErrLog $EngineErrLog
            }

            Start-Sleep -Seconds 5
        }
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        throw
    }
    catch {
        Write-Host "Launcher watch stopped: $($_.Exception.Message)"
        throw
    }
}

Write-Host "Starting AI Studio Control Center."
Write-Host "Using Python: $PythonCmd"
Write-Host "Engine auto-start: $StartEngine"

$EngineProcess = $null
$EngineUsable = $false
if ($StartEngine) {
    if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7865)) {
        Write-Host "Starting hidden Fooocus engine on http://127.0.0.1:7865"
        $EngineProcess = Start-Process -FilePath $PythonCmd -ArgumentList @("launch.py", "--disable-analytics", "--disable-in-browser") -WorkingDirectory $RepoRoot -RedirectStandardOutput $EngineOutLog -RedirectStandardError $EngineErrLog -WindowStyle Minimized -PassThru
        Write-Host "Waiting initial ${InitialEngineDelaySeconds}s for model/UI warmup before checking engine port..."
        Start-Sleep -Seconds $InitialEngineDelaySeconds
    }
    else {
        Write-Host "Fooocus engine is already reachable on http://127.0.0.1:7865"
    }

    $engineReady = Wait-PortOpen -Name "Fooocus Engine" -HostName "127.0.0.1" -Port 7865 -TimeoutSeconds $EngineWaitSeconds -ProcessToWatch $EngineProcess
    if ($engineReady) {
        $EngineUsable = Test-StableEngine -EngineProcess $EngineProcess
    }
    if (-not $EngineUsable) {
        Show-RecentLog -Label "Fooocus engine" -OutLog $EngineOutLog -ErrLog $EngineErrLog
        Write-Host "Studio will still open on http://127.0.0.1:7872, but Generate in Studio is disabled until the engine passes health."
    }
}
else {
    Write-Host "Skipping Fooocus engine auto-start."
}

$startedStudio = $false
$StudioProcess = $null
if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7872)) {
    Write-Host "Starting AI Studio on http://127.0.0.1:7872"
    $StudioProcess = Start-Process -FilePath $PythonCmd -ArgumentList @("ai_studio_app.py") -WorkingDirectory $RepoRoot -RedirectStandardOutput $StudioOutLog -RedirectStandardError $StudioErrLog -WindowStyle Minimized -PassThru
    $startedStudio = $true
}
else {
    Write-Host "AI Studio is already running on http://127.0.0.1:7872"
}

$studioReady = Wait-PortOpen -Name "AI Studio" -HostName "127.0.0.1" -Port 7872 -TimeoutSeconds $StudioWaitSeconds -ProcessToWatch $StudioProcess
if ($studioReady) {
    if ($OpenBrowser -or $startedStudio) {
        Write-Host "Opening AI Studio in browser once."
        Start-Process "http://127.0.0.1:7872"
    }
    else {
        Write-Host "AI Studio is already open/running. Not opening another browser tab."
    }
}
else {
    Show-RecentLog -Label "AI Studio" -OutLog $StudioOutLog -ErrLog $StudioErrLog
    exit 1
}

Write-Host ""
Write-Host "Main UI: http://127.0.0.1:7872"
if ($EngineUsable) {
    Write-Host "Hidden engine: healthy on http://127.0.0.1:7865"
}
else {
    Write-Host "Hidden engine: NOT HEALTHY. Do not use http://127.0.0.1:7865 directly."
}
Write-Host "Engine stdout log: $EngineOutLog"
Write-Host "Engine stderr log: $EngineErrLog"
Write-Host "Studio stdout log: $StudioOutLog"
Write-Host "Studio stderr log: $StudioErrLog"

Watch-Studio -StudioProcess $StudioProcess -EngineProcess $EngineProcess -EngineUsable $EngineUsable
