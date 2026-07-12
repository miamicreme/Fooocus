param(
    [int]$EngineWaitSeconds = 420,
    [int]$StudioWaitSeconds = 120,
    [int]$InitialEngineDelaySeconds = 45
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
    if (Test-Path $OutLog) { Get-Content $OutLog -Tail 60 }
    Write-Host "Recent $Label stderr log: $ErrLog"
    if (Test-Path $ErrLog) { Get-Content $ErrLog -Tail 60 }
}

function Wait-PortOpen {
    param([string]$Name, [string]$HostName, [int]$Port, [int]$TimeoutSeconds)
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        if (Test-PortOpen -HostName $HostName -Port $Port) {
            Write-Host "$Name is ready on http://${HostName}:$Port after ${elapsed}s"
            return $true
        }
        Write-Host "Waiting for $Name on port $Port... ${elapsed}s elapsed, $($TimeoutSeconds - $elapsed)s remaining"
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    Write-Host "WARNING: $Name was not ready on port $Port after ${TimeoutSeconds}s."
    return $false
}

Write-Host "Starting Studio One UI with engine wait."
Write-Host "Using Python: $PythonCmd"
Write-Host "Engine wait: ${EngineWaitSeconds}s. Initial engine delay: ${InitialEngineDelaySeconds}s."

if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7865)) {
    Write-Host "Starting Fooocus engine on http://127.0.0.1:7865"
    Start-Process -FilePath $PythonCmd -ArgumentList @("scripts\run_fooocus_keepalive.py", "--disable-analytics", "--disable-in-browser") -WorkingDirectory $RepoRoot -RedirectStandardOutput $EngineOutLog -RedirectStandardError $EngineErrLog -WindowStyle Minimized
    Write-Host "Waiting initial ${InitialEngineDelaySeconds}s for model/UI warmup before checking engine port..."
    Start-Sleep -Seconds $InitialEngineDelaySeconds
}
else {
    Write-Host "Fooocus engine is already running on http://127.0.0.1:7865"
}

$engineReady = Wait-PortOpen -Name "Fooocus Engine" -HostName "127.0.0.1" -Port 7865 -TimeoutSeconds $EngineWaitSeconds
if (-not $engineReady) {
    Show-RecentLog -Label "Fooocus engine" -OutLog $EngineOutLog -ErrLog $EngineErrLog
    Write-Host "Studio will still start, but the hidden engine panel may not work until Fooocus finishes or the log error is fixed."
}

if (-not (Test-PortOpen -HostName "127.0.0.1" -Port 7872)) {
    Write-Host "Starting AI Studio on http://127.0.0.1:7872"
    Start-Process -FilePath $PythonCmd -ArgumentList @("ai_studio_app.py") -WorkingDirectory $RepoRoot -RedirectStandardOutput $StudioOutLog -RedirectStandardError $StudioErrLog -WindowStyle Minimized
}
else {
    Write-Host "AI Studio is already running on http://127.0.0.1:7872"
}

$studioReady = Wait-PortOpen -Name "AI Studio" -HostName "127.0.0.1" -Port 7872 -TimeoutSeconds $StudioWaitSeconds
if ($studioReady) {
    Write-Host "Opening AI Studio in browser."
    Start-Process "http://127.0.0.1:7872"
}
else {
    Show-RecentLog -Label "AI Studio" -OutLog $StudioOutLog -ErrLog $StudioErrLog
}

Write-Host ""
Write-Host "Main UI: http://127.0.0.1:7872"
Write-Host "Hidden engine: http://127.0.0.1:7865"
Write-Host "Engine stdout log: $EngineOutLog"
Write-Host "Engine stderr log: $EngineErrLog"
Write-Host "Studio stdout log: $StudioOutLog"
Write-Host "Studio stderr log: $StudioErrLog"
Write-Host "Keep this launcher window open while working."
