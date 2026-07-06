@echo off
title Fooocus Local Markup Assistant
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo Starting Fooocus Local Markup Assistant...
echo Using: %PYTHON_CMD%
echo Open browser: http://127.0.0.1:7871
echo.
%PYTHON_CMD% local_markup_app.py
echo.
echo Markup Assistant stopped. Press any key to close.
pause >nul
