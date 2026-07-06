@echo off
title Fooocus Local Runner
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo Starting Fooocus locally...
echo Using: %PYTHON_CMD%
echo.
%PYTHON_CMD% launch.py --disable-analytics
echo.
echo Fooocus stopped. Press any key to close.
pause >nul
