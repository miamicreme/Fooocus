@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting AI Studio Control Center.
echo Engine auto-start is OFF to prevent crash loops and duplicate windows.
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File scripts\run_studio_one_ui.ps1

echo.
echo Launcher stopped. Press any key to close.
pause >nul
