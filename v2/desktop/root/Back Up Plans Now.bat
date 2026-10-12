@echo off
title Financial Planner backup
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\backup.ps1" -Force
echo.
pause
