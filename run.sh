#!/bin/bash

# FinancePlanApp - One-Click Launcher for Mac/Linux
# Double-click this file or run ./run.sh to start the application

echo "========================================="
echo "FinancePlanApp - Starting Application"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run setup.sh first to install dependencies."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "Error: Streamlit is not installed."
    echo "Please run setup.sh first to install dependencies."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Launch the application
echo "Launching FinancePlanApp..."
echo "The application will open in your default web browser."
echo ""
echo "To stop the application, press Ctrl+C in this window."
echo ""

streamlit run FinancialPlannerV15_ClaudeCodeV.py
