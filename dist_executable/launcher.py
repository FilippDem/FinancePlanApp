#!/usr/bin/env python3
"""
Launcher script for Financial Planner Executable
This script starts the Streamlit application programmatically
"""

import sys
import os
import webbrowser
import threading
import time

def open_browser(url, delay=3):
    """Open browser after a delay"""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """Main launcher function"""
    print("=" * 50)
    print("Financial Planning Application v0.75")
    print("=" * 50)
    print()
    print("Starting the application...")
    print()

    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))

    # Path to the main application file
    app_file = os.path.join(application_path, 'FinancialPlanner_v0_7.py')

    if not os.path.exists(app_file):
        print(f"ERROR: Application file not found: {app_file}")
        print(f"Looking in: {application_path}")
        try:
            if os.path.isdir(application_path):
                files = os.listdir(application_path)
                print(f"Files available ({len(files)} total): {files[:10]}")
            else:
                print(f"ERROR: {application_path} is not a directory")
        except Exception as e:
            print(f"Could not list directory: {e}")
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)

    # Set environment variables
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

    # Streamlit configuration - try different ports if needed
    port = 8501
    url = f"http://localhost:{port}"

    print(f"Application will open in your browser at: {url}")
    print()
    print("To stop the application, close this window or press Ctrl+C")
    print()
    print("-" * 50)
    print()

    # Schedule browser opening in background thread (with longer delay for safety)
    browser_thread = threading.Thread(target=open_browser, args=(url, 5), daemon=True)
    browser_thread.start()

    try:
        # Import streamlit's CLI and run it directly
        print("Loading Streamlit...")
        from streamlit.web import cli as stcli
        print("Streamlit loaded successfully!")
        print()

        # Prepare arguments for streamlit run
        sys.argv = [
            "streamlit",
            "run",
            app_file,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none",
            "--browser.serverAddress", "localhost",
        ]

        print("Launching Streamlit server...")
        print()

        # Run streamlit
        sys.exit(stcli.main())

    except ImportError as e:
        print()
        print("=" * 50)
        print("ERROR: Could not import Streamlit")
        print("=" * 50)
        print(f"ImportError: {e}")
        print()
        print("This likely means Streamlit was not properly bundled.")
        print("Please rebuild the executable.")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)

    except Exception as e:
        print()
        print("=" * 50)
        print(f"ERROR: Failed to start application")
        print("=" * 50)
        print(f"Error: {e}")
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
        sys.exit(0)
    except Exception as e:
        print()
        print("=" * 50)
        print("UNEXPECTED ERROR")
        print("=" * 50)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Press Enter to exit...")
        input()
        sys.exit(1)
