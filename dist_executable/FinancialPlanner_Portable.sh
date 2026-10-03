#!/bin/bash
# ============================================================
# Financial Planner - Portable Launcher for Mac/Linux
# ============================================================
# This launcher automatically sets up a Python environment
# and runs the Financial Planning Application
# ============================================================

echo "========================================================"
echo "Financial Planning Application v0.85"
echo "Portable Distribution for Mac/Linux"
echo "========================================================"
echo ""

# Get the directory where this script is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$APP_DIR"

# Check if Python 3 is installed
if command -v python3 &> /dev/null; then
    echo "[OK] Python is installed"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if it's Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        echo "[OK] Python is installed"
        PYTHON_CMD="python"
    else
        echo "ERROR: Python 3 is required but only Python 2 was found"
        exit 1
    fi
else
    echo ""
    echo "========================================================"
    echo "Python Not Found!"
    echo "========================================================"
    echo ""
    echo "This application requires Python 3.8+ to run."
    echo ""
    echo "Installation instructions:"
    echo ""
    echo "macOS:"
    echo "  brew install python3"
    echo "  (or download from https://www.python.org/downloads/)"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-venv python3-pip"
    echo ""
    echo "Fedora/RHEL:"
    echo "  sudo dnf install python3 python3-pip"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "[OK] Virtual environment exists"
else
    echo ""
    echo "========================================================"
    echo "First-Time Setup"
    echo "========================================================"
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Try running: $PYTHON_CMD -m pip install --upgrade pip"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "[OK] Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import streamlit" &> /dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Installing dependencies (this may take a few minutes)..."
    echo ""
    python -m pip install --upgrade pip
    python -m pip install streamlit pandas numpy plotly openpyxl reportlab kaleido
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install dependencies"
        echo "Check your internet connection and try again"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
    echo "[OK] Dependencies installed successfully"
fi

# Run the application
echo ""
echo "========================================================"
echo "Starting Financial Planning Application"
echo "========================================================"
echo ""
echo "The application will open in your browser in a few seconds..."
echo "To stop the application, close this window or press Ctrl+C"
echo ""
echo "--------------------------------------------------------"
echo ""

streamlit run FinancialPlanner_v0_85.py --server.headless=true --browser.gatherUsageStats=false

# If we get here, the app was stopped
echo ""
echo "========================================================"
echo "Application Stopped"
echo "========================================================"
echo ""
