@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus low-VRAM safe GPU mode.
echo This keeps CUDA enabled with conservative RTX 2060 flags.
echo Local URL: http://127.0.0.1:7865
echo.
%PYTHON_CMD% launch.py --disable-analytics --disable-in-browser --always-no-vram --attention-pytorch --vae-in-cpu --disable-xformers --disable-async-cuda-allocation

echo.
echo Fooocus low-VRAM safe mode stopped. Press any key to close.
pause >nul
