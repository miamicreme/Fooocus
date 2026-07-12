@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus low-VRAM safe diagnostic mode with keepalive.
echo This keeps CUDA enabled with conservative RTX 2060 flags and keeps the server open after Gradio starts.
echo Open http://127.0.0.1:7865 after it prints the local URL.
echo.
%PYTHON_CMD% scripts\run_fooocus_keepalive.py --disable-analytics --disable-in-browser --always-no-vram --attention-pytorch --vae-in-cpu --disable-xformers --disable-async-cuda-allocation

echo.
echo Fooocus low-VRAM safe mode stopped. Press any key to close.
pause >nul
