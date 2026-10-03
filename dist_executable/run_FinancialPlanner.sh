#!/bin/bash

# Launcher script for Financial Planner
# This script should be placed in the same directory as the FinancialPlanner executable

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Launch the Financial Planner
./FinancialPlanner
