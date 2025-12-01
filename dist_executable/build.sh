#!/bin/bash

# Build script for Linux/Mac
# This script builds the Financial Planner executable

echo "=========================================="
echo "Financial Planner - Build Script"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

# Install required dependencies
echo "Installing dependencies..."
pip3 install -r requirements_build.txt

# Build the executable
echo ""
echo "Building executable..."
pyinstaller --clean FinancialPlanner.spec

if [ $? -eq 0 ]; then
    # Copy launcher script to dist folder
    echo "Copying launcher scripts..."
    cp run_FinancialPlanner.sh dist/FinancialPlanner/
    chmod +x dist/FinancialPlanner/run_FinancialPlanner.sh

    echo ""
    echo "=========================================="
    echo "Build successful!"
    echo "=========================================="
    echo ""
    echo "The executable has been created in: dist/FinancialPlanner/"
    echo ""
    echo "To run the application:"
    echo "  1. Navigate to: dist/FinancialPlanner/"
    echo "  2. Run: ./run_FinancialPlanner.sh (or double-click run_FinancialPlanner.sh)"
    echo ""
    echo "To distribute to friends:"
    echo "  - Zip the entire 'dist/FinancialPlanner/' folder"
    echo "  - Share the zip file"
    echo "  - They just extract and double-click the launcher!"
    echo ""
else
    echo ""
    echo "Build failed. Please check the error messages above."
    exit 1
fi
