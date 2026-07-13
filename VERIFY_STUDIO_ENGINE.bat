@echo off
setlocal
cd /d %~dp0

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo Verifying Studio engine endpoints on http://127.0.0.1:7865
echo.
"%PYTHON_CMD%" scripts\verify_studio_engine.py
set VERIFY_EXIT=%ERRORLEVEL%
echo.
if not "%VERIFY_EXIT%"=="0" (
    echo Verification failed. Start Studio with START_HERE.bat, wait for Fooocus to finish loading, then run this again.
    pause
    exit /b %VERIFY_EXIT%
)

choice /C YN /N /M "Run one real smoke generation now? [Y/N] "
if errorlevel 2 goto done
"%PYTHON_CMD%" scripts\verify_studio_engine.py --generate
set VERIFY_EXIT=%ERRORLEVEL%

:done
echo.
if "%VERIFY_EXIT%"=="0" (
    echo Studio engine verification completed.
) else (
    echo Studio smoke generation failed. Check the Fooocus launcher window for the engine error.
)
pause
exit /b %VERIFY_EXIT%
