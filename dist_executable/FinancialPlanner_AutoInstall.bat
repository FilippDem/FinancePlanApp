@echo off
REM ============================================================
REM Financial Planner - Auto-Installing Launcher for Windows
REM ============================================================
REM This launcher automatically downloads and installs Python
REM if needed, then runs the Financial Planning Application
REM ============================================================

SETLOCAL EnableDelayedExpansion

echo ========================================================
echo Financial Planning Application v0.85
echo Auto-Installing Portable Distribution
echo ========================================================
echo.

REM Get the directory where this script is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM ============================================================
REM Step 1: Check for Python
REM ============================================================

echo [1/4] Checking for Python...

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

REM Check if portable Python exists in this folder
if exist "python_portable\python.exe" (
    echo [OK] Using portable Python from this folder
    set "PYTHON_CMD=python_portable\python.exe"
    set "PATH=%APP_DIR%python_portable;%APP_DIR%python_portable\Scripts;%PATH%"
    goto :check_venv
)

echo [!] Python not found
echo.

REM ============================================================
REM Step 2: Offer to install Python automatically
REM ============================================================

echo ========================================================
echo Python Installation Required
echo ========================================================
echo.
echo This application requires Python 3.11 to run.
echo.
echo Would you like to download and install Python automatically?
echo.
echo Option 1: Download Python installer (recommended)
echo           - Downloads Python 3.11 installer
echo           - Installs system-wide
echo           - Can be used by other programs
echo.
echo Option 2: Download portable Python
echo           - Downloads portable Python to this folder
echo           - No system installation needed
echo           - Only works for this app
echo.
echo Option 3: Cancel
echo           - Exit and install Python manually from python.org
echo.
echo ========================================================
echo.
set /p INSTALL_CHOICE="Enter choice (1, 2, or 3): "

if "%INSTALL_CHOICE%"=="1" goto :install_python_full
if "%INSTALL_CHOICE%"=="2" goto :install_python_portable
if "%INSTALL_CHOICE%"=="3" goto :cancel_install

echo Invalid choice. Exiting.
pause
exit /b 1

REM ============================================================
REM Option 1: Full Python Installation
REM ============================================================

:install_python_full
echo.
echo ========================================================
echo Downloading Python 3.11 Installer...
echo ========================================================
echo.

set "PYTHON_VERSION=3.11.9"
set "PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%"

REM Check if PowerShell is available
powershell -Command "exit" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is required to download Python.
    echo Please download Python manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Downloading from: %PYTHON_URL%
echo This may take a few minutes...
echo.

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"

if %errorlevel% neq 0 (
    echo ERROR: Failed to download Python installer.
    echo.
    echo Please download and install Python manually from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

echo [OK] Download complete!
echo.
echo ========================================================
echo Installing Python...
echo ========================================================
echo.
echo The Python installer will now launch.
echo.
echo IMPORTANT: During installation:
echo   1. CHECK the box "Add Python to PATH"
echo   2. Click "Install Now"
echo   3. Wait for installation to complete
echo.
pause

REM Run the installer with recommended options
%PYTHON_INSTALLER% /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo.
echo Waiting for installation to complete...
timeout /t 10 /nobreak >nul

REM Clean up installer
del "%PYTHON_INSTALLER%"

echo.
echo [OK] Python installation complete!
echo Please close this window and run the launcher again.
echo.
pause
exit /b 0

REM ============================================================
REM Option 2: Portable Python Installation
REM ============================================================

:install_python_portable
echo.
echo ========================================================
echo Downloading Portable Python...
echo ========================================================
echo.

set "PYTHON_VERSION=3.11.9"
set "PYTHON_EMBED=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_EMBED%"

echo Downloading from: %PYTHON_URL%
echo This may take a few minutes...
echo.

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EMBED%'}"

if %errorlevel% neq 0 (
    echo ERROR: Failed to download portable Python.
    echo Please try Option 1 instead, or install Python manually.
    pause
    exit /b 1
)

echo [OK] Download complete!
echo.
echo Extracting portable Python...

powershell -Command "Expand-Archive -Path '%PYTHON_EMBED%' -DestinationPath 'python_portable' -Force"

if %errorlevel% neq 0 (
    echo ERROR: Failed to extract portable Python.
    pause
    exit /b 1
)

REM Clean up zip file
del "%PYTHON_EMBED%"

REM Download get-pip.py to install pip in portable Python
echo Downloading pip installer...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python_portable\get-pip.py'}"

REM Enable site-packages in portable Python
echo import site >> python_portable\python311._pth

REM Install pip
echo Installing pip...
python_portable\python.exe python_portable\get-pip.py

echo.
echo [OK] Portable Python installed successfully!
echo.
echo Restarting launcher...
timeout /t 3 /nobreak >nul

REM Restart this script
"%~f0"
exit /b 0

:cancel_install
echo.
echo Installation cancelled.
echo.
echo To install Python manually:
echo 1. Visit: https://www.python.org/downloads/
echo 2. Download and install Python 3.11 or newer
echo 3. Make sure to check "Add Python to PATH" during installation
echo 4. Run this launcher again
echo.
pause
exit /b 1

REM ============================================================
REM Step 3: Create Virtual Environment
REM ============================================================

:check_venv
echo.
echo [2/4] Setting up virtual environment...

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment exists
    goto :activate_venv
)

echo Creating virtual environment...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo.
    echo Trying to install venv module...
    %PYTHON_CMD% -m pip install --upgrade pip
    %PYTHON_CMD% -m pip install virtualenv
    %PYTHON_CMD% -m virtualenv venv
    if %errorlevel% neq 0 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment created

REM ============================================================
REM Step 4: Install Dependencies
REM ============================================================

:activate_venv
echo.
echo [3/4] Installing dependencies...

call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Installing required packages...
    echo This will take 2-5 minutes on first run.
    echo.

    REM Update pip first
    echo Updating pip...
    python -m pip install --upgrade pip >nul 2>&1

    REM Install dependencies with retry logic
    echo Installing dependencies (attempt 1/3)...
    python -m pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
    if %errorlevel% neq 0 (
        echo.
        echo First attempt failed, retrying (attempt 2/3)...
        timeout /t 3 /nobreak >nul
        python -m pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
        if %errorlevel% neq 0 (
            echo.
            echo Second attempt failed, final retry (attempt 3/3)...
            timeout /t 5 /nobreak >nul
            python -m pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
            if %errorlevel% neq 0 (
                echo.
                echo ERROR: Failed to install dependencies after 3 attempts
                echo.
                echo Please check:
                echo   - Your internet connection
                echo   - Firewall settings
                echo   - Try running as Administrator
                echo.
                pause
                exit /b 1
            )
        )
    )
    echo.
    echo [OK] All dependencies installed successfully!
) else (
    echo [OK] Dependencies already installed
)

REM ============================================================
REM Step 5: Launch Application
REM ============================================================

echo.
echo [4/4] Starting application...
echo.
echo ========================================================
echo Financial Planning Application v0.85
echo ========================================================
echo.
echo Starting Streamlit server...
echo.
echo To stop the application:
echo   - Close this window, or
echo   - Press Ctrl+C
echo.
echo --------------------------------------------------------
echo.

REM Start Streamlit in background and capture the process
start /B streamlit run FinancialPlanner_v0_85.py --server.headless=true --browser.gatherUsageStats=false

REM Wait for Streamlit to start (give it 5 seconds)
echo Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Open browser
echo Opening browser...
python -c "import webbrowser; webbrowser.open('http://localhost:8501')"

echo.
echo [OK] Application is running!
echo Browser should open at: http://localhost:8501
echo.
echo If browser didn't open, manually navigate to:
echo http://localhost:8501
echo.
echo --------------------------------------------------------
echo.

REM Wait for streamlit to finish (keeps window open)
wait

REM If we get here, the app was stopped
echo.
echo ========================================================
echo Application Stopped
echo ========================================================
echo.
pause
