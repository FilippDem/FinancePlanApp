@echo off
REM Build script for Windows
REM This script builds the Financial Planner executable

echo ==========================================
echo Financial Planner - Build Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed!
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Install required dependencies
echo Installing dependencies...
pip install -r requirements_build.txt

REM Build the executable
echo.
echo Building executable...
pyinstaller --clean FinancialPlanner.spec

if %errorlevel% equ 0 (
    REM Copy launcher script to dist folder
    echo Copying launcher scripts...
    copy run_FinancialPlanner.bat dist\FinancialPlanner\

    echo.
    echo ==========================================
    echo Build successful!
    echo ==========================================
    echo.
    echo The executable has been created in: dist\FinancialPlanner\
    echo.
    echo To run the application:
    echo   1. Navigate to: dist\FinancialPlanner\
    echo   2. Double-click: run_FinancialPlanner.bat
    echo.
    echo To distribute to friends:
    echo   - Zip the entire 'dist\FinancialPlanner\' folder
    echo   - Share the zip file
    echo   - They just extract and double-click the launcher!
    echo.
) else (
    echo.
    echo Build failed. Please check the error messages above.
    pause
    exit /b 1
)

pause
