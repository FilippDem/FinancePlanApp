import os
import sys
import webbrowser
import time
import threading

#Use this command in terminal to compile the program 
#pyinstaller --onefile --console --icon=icons8-piggy-bank-64.ico --add-data "FinancialApp_V14.py;." --collect-all=streamlit --name "FinancialPlanner" launcher.py

def open_browser():
    time.sleep(4)
    try:
        webbrowser.open('http://localhost:8501')
    except:
        pass


def main():
    print("Financial Planning Suite V14 - Starting...")

    # Find the app file
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            app_dir = sys._MEIPASS
        else:
            app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    app_file = os.path.join(app_dir, 'FinancialApp_V14.py')

    if not os.path.exists(app_file):
        print("ERROR: FinancialApp_V14.py not found!")
        input("Press Enter to exit...")
        return

    print("Browser will open at: http://localhost:8501")

    # Change to app directory and start browser
    os.chdir(app_dir)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Run streamlit using os.system (this works with PyInstaller)
    cmd = f'streamlit run "{app_file}" --server.headless true --browser.gatherUsageStats false'
    os.system(cmd)


if __name__ == "__main__":
    main()
