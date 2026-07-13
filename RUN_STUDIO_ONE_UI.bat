@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

if not "%FOOOCUS_SKIP_SELF_SYNC%"=="1" (
    set FOOOCUS_SKIP_SELF_SYNC=1
    if exist ".git" (
        echo Syncing latest Studio launcher from origin/studio/designed-control-ui...
        git fetch origin
        if errorlevel 1 goto sync_failed
        git checkout studio/designed-control-ui
        if errorlevel 1 goto sync_failed
        git reset --hard origin/studio/designed-control-ui
        if errorlevel 1 goto sync_failed
        echo Relaunching updated Studio launcher.
        call "%~f0"
        exit /b %ERRORLEVEL%
    )
)

goto launch_studio

:sync_failed
echo Studio self-sync failed. Continuing with the local files already on disk.

:launch_studio
echo Starting AI Studio Control Center.
echo Engine auto-start is OFF to prevent crash loops and duplicate windows.
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File scripts\run_studio_one_ui.ps1

echo.
echo Launcher stopped. Press any key to close.
pause >nul
