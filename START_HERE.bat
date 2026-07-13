@echo off
title Start AI Studio
cd /d %~dp0

echo Starting AI Studio the simple way.
echo This will update the app, start the Fooocus engine, start Studio, and open the browser.
echo.
call RUN_STUDIO_ONE_UI.bat
