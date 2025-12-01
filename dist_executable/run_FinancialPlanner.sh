#!/bin/bash

# Launcher script for Financial Planner
# This script should be placed in the same directory as the FinancialPlanner executable

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Launch the Financial Planner with Streamlit
echo "Starting Financial Planner v0.85..."
echo "Opening in your default web browser..."
echo ""
echo "To stop the application, close this window or press Ctrl+C"
echo ""

# Run streamlit with the executable
./FinancialPlanner run FinancialPlanner_v0_85.py --server.headless=true --browser.gatherUsageStats=false
