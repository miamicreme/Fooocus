@echo off
title AI Studio One-Click Launcher
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

if not "%FOOOCUS_SKIP_SELF_SYNC%"=="1" (
    set FOOOCUS_SKIP_SELF_SYNC=1
    if exist ".git" (
        echo Updating AI Studio to the latest approved version...
        git fetch origin
        if errorlevel 1 goto sync_failed
        git checkout studio/designed-control-ui
        if errorlevel 1 goto sync_failed
        git reset --hard origin/studio/designed-control-ui
        if errorlevel 1 goto sync_failed
        echo Update complete. Starting the refreshed launcher now.
        call "%~f0"
        exit /b %ERRORLEVEL%
    )
)

goto launch_studio

:sync_failed
echo Update check failed. Starting with the local files already on this computer.

:launch_studio
echo Starting AI Studio Control Center.
echo One-click mode: update, start Fooocus engine, start Studio, open browser.
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File scripts\run_studio_one_ui.ps1 -StartEngine -OpenBrowser

echo.
echo AI Studio launcher stopped. Press any key to close.
pause >nul
