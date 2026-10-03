@echo off
REM ============================================================
REM Financial Planner - Portable Launcher for Windows
REM ============================================================
REM This launcher automatically sets up a Python environment
REM and runs the Financial Planning Application
REM ============================================================

SETLOCAL EnableDelayedExpansion

echo ========================================================
echo Financial Planning Application v0.85
echo Portable Distribution for Windows
echo ========================================================
echo.

REM Get the directory where this script is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
    set "PYTHON_CMD=python"
    goto :check_venv
)

REM Check if python3 command exists
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
    set "PYTHON_CMD=python3"
    goto :check_venv
)

REM Python not found - provide instructions
echo.
echo ========================================================
echo Python Not Found!
echo ========================================================
echo.
echo This application requires Python to run.
echo.
echo OPTION 1 - Quick Setup (Recommended):
echo   1. Download Python from: https://www.python.org/downloads/
echo   2. Run the installer
echo   3. IMPORTANT: Check "Add Python to PATH" during installation
echo   4. After installation, run this script again
echo.
echo OPTION 2 - Portable Python:
echo   1. Download Python embeddable package from python.org
echo   2. Extract to a folder named "python_portable" next to this script
echo   3. Run this script again
echo.
pause
exit /b 1

:check_venv
REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment exists
    goto :activate_venv
)

echo.
echo ========================================================
echo First-Time Setup
echo ========================================================
echo.
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Try running: python -m pip install --upgrade pip
    pause
    exit /b 1
)
echo [OK] Virtual environment created

:activate_venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Installing dependencies (this may take a few minutes)...
    echo.
    python -m pip install --upgrade pip
    python -m pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install dependencies
        echo Check your internet connection and try again
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed successfully
)

REM Run the application
echo.
echo ========================================================
echo Starting Financial Planning Application
echo ========================================================
echo.
echo The application will open in your browser in a few seconds...
echo To stop the application, close this window or press Ctrl+C
echo.
echo --------------------------------------------------------
echo.

streamlit run FinancialPlanner_v0_85.py --server.headless=true --browser.gatherUsageStats=false

REM If we get here, the app was stopped
echo.
echo ========================================================
echo Application Stopped
echo ========================================================
echo.
pause
