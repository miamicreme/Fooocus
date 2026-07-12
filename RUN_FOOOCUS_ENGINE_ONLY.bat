@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

if not exist "%TEMP%\fooocus" mkdir "%TEMP%\fooocus"

echo Starting Fooocus engine only with the stable command.
echo If this crashes, the issue is local Fooocus/CUDA/PyTorch/model loading, not AI Studio.
echo.
%PYTHON_CMD% launch.py --disable-analytics --disable-in-browser

echo.
echo Fooocus engine stopped. Press any key to close.
pause >nul
