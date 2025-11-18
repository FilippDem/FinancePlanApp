@echo off
REM FinancePlanApp - One-Click Launcher for Windows
REM Double-click this file to start the application

echo =========================================
echo FinancePlanApp - Starting Application
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Error: Virtual environment not found.
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    echo.
    pause
    exit /b 1
)

REM Check if streamlit is installed
where streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Streamlit is not installed.
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo Launching FinancePlanApp...
echo The application will open in your default web browser.
echo.
echo To stop the application, close this window.
echo.

streamlit run FinancialPlannerV16_ClaudeCodeV.py

pause
