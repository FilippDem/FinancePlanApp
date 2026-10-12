@echo off
title Financial Planner
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\start.ps1"
if errorlevel 1 (
  echo.
  pause
)
