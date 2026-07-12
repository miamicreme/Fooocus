@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus CPU-safe diagnostic mode with keepalive.
echo This avoids CUDA and keeps the server open after Gradio starts.
echo Open http://127.0.0.1:7865 after it prints the local URL.
echo.
%PYTHON_CMD% scripts\run_fooocus_keepalive.py --disable-analytics --disable-in-browser --always-cpu 4 --attention-pytorch --vae-in-cpu --disable-xformers

echo.
echo Fooocus CPU-safe mode stopped. Press any key to close.
pause >nul
