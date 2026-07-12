@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus engine only with keepalive.
echo This keeps the process open after Gradio starts at http://127.0.0.1:7865.
echo.
%PYTHON_CMD% scripts\run_fooocus_keepalive.py --disable-analytics --disable-in-browser

echo.
echo Fooocus engine stopped. Press any key to close.
pause >nul
