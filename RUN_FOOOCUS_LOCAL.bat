@echo off
title Fooocus Local Runner
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

echo Starting Fooocus locally...
echo Using: %PYTHON_CMD%
echo Gradio is intentionally pinned for Fooocus compatibility.
echo Applying Easy SDXL WebUI integration...
%PYTHON_CMD% scripts\apply_easy_sdxl_webui.py
echo.
%PYTHON_CMD% launch.py --disable-analytics --listen
echo.
echo Fooocus stopped. Press any key to close.
pause >nul
