@echo off
REM Launcher script for Financial Planner
REM This script should be placed in the same directory as the FinancialPlanner.exe

echo Starting Financial Planner v0.85...
echo Opening in your default web browser...
echo.
echo To stop the application, close this window or press Ctrl+C
echo.

REM Run streamlit with the executable
FinancialPlanner.exe run FinancialPlanner_v0_85.py --server.headless=true --browser.gatherUsageStats=false

pause
