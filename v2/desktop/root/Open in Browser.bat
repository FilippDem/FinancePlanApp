@echo off
title Financial Planner (browser)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\start.ps1" -Browser
if errorlevel 1 (
  echo.
  pause
)
