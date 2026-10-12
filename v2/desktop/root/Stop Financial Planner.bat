@echo off
title Financial Planner
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\stop.ps1"
timeout /t 3 >nul
