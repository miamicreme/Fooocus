@echo off
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False

start "Fooocus Engine" cmd /k "%PYTHON_CMD% launch.py --disable-analytics"
timeout /t 8 /nobreak >nul
start "AI Studio One UI" cmd /k "%PYTHON_CMD% ai_studio_app.py"

echo One UI is starting.
echo Work here: http://127.0.0.1:7872
echo Fooocus engine: http://127.0.0.1:7865
echo.
echo Keep both opened command windows running.
pause
