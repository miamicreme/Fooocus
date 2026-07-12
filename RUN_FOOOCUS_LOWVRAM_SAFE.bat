@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus low-VRAM safe diagnostic mode.
echo This keeps CUDA enabled but uses the safest RTX 2060 flags.
echo.
%PYTHON_CMD% launch.py --disable-analytics --disable-in-browser --always-no-vram --attention-pytorch --vae-in-cpu --disable-xformers --disable-async-cuda-allocation

echo.
echo Fooocus low-VRAM safe mode stopped. Press any key to close.
pause >nul
