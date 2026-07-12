@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus CPU-safe diagnostic mode.
echo This avoids CUDA to prove whether the crash is GPU/CUDA/PyTorch related.
echo It will be much slower than GPU mode.
echo.
%PYTHON_CMD% launch.py --disable-analytics --disable-in-browser --always-cpu 4 --attention-pytorch --vae-in-cpu --disable-xformers

echo.
echo Fooocus CPU-safe mode stopped. Press any key to close.
pause >nul
