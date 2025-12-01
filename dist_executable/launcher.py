#!/usr/bin/env python3
"""
Launcher script for Financial Planner Executable
This script starts the Streamlit application programmatically
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    """Main launcher function"""
    print("=" * 50)
    print("Financial Planning Application v0.85")
    print("=" * 50)
    print()
    print("Starting the application...")
    print()

    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        executable_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
        executable_dir = application_path

    # Path to the main application file
    app_file = os.path.join(application_path, 'FinancialPlanner_v0_85.py')

    if not os.path.exists(app_file):
        print(f"ERROR: Application file not found: {app_file}")
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)

    # Set environment variable to prevent Streamlit from checking for updates
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

    # Streamlit configuration
    port = 8501
    url = f"http://localhost:{port}"

    print(f"Application will open in your browser at: {url}")
    print()
    print("To stop the application, close this window or press Ctrl+C")
    print()
    print("-" * 50)
    print()

    # Start Streamlit in a subprocess
    try:
        # Build the streamlit command
        cmd = [
            sys.executable,
            '-m', 'streamlit', 'run',
            app_file,
            '--server.port', str(port),
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--server.fileWatcherType', 'none',
            '--browser.serverAddress', 'localhost',
        ]

        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Wait a moment for Streamlit to start
        time.sleep(3)

        # Open browser
        print("Opening browser...")
        webbrowser.open(url)
        print()
        print("Application is running!")
        print()

        # Keep showing output
        try:
            for line in process.stdout:
                print(line, end='')
        except KeyboardInterrupt:
            print()
            print("Shutting down...")
            process.terminate()
            process.wait()

    except Exception as e:
        print(f"ERROR: Failed to start application: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Application closed by user.")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)
