# Financial Planning Application - Executable Distribution

Version 0.85

This folder contains everything needed to build and distribute a standalone executable version of the Financial Planning Application.

## 📦 What's This?

This is a distributable version of the Financial Planner that can be packaged into a standalone executable. Users who receive the built executable **DO NOT need Python installed** - they can just double-click and run!

## 🔨 Building the Executable (For Developers)

### Prerequisites

You need Python installed to BUILD the executable (but end users won't need it):
- Python 3.8 or higher
- pip (Python package installer)

### Build Instructions

#### **Windows:**
1. Open Command Prompt or PowerShell
2. Navigate to this `dist_executable` folder
3. Run: `build.bat`
4. Wait for the build to complete (may take 2-5 minutes)
5. The executable will be in: `dist/FinancialPlanner/`

#### **Linux/Mac:**
1. Open Terminal
2. Navigate to this `dist_executable` folder
3. Run: `./build.sh`
4. Wait for the build to complete (may take 2-5 minutes)
5. The executable will be in: `dist/FinancialPlanner/`

### What Gets Built?

After building, you'll have a `dist/FinancialPlanner/` folder containing:
- The main executable (FinancialPlanner.exe on Windows, FinancialPlanner on Linux/Mac)
- All necessary libraries and dependencies
- The launcher scripts (`run_FinancialPlanner.bat` or `run_FinancialPlanner.sh`)
- Assets folder with icons and resources

## 📤 Distributing to Friends

### What to Share

**Share the entire `dist/FinancialPlanner/` folder** with your friends. They need all the files, not just the executable!

You can:
1. **Compress it**: Zip the entire `dist/FinancialPlanner/` folder
2. **Share via**: Email, cloud storage (Dropbox, Google Drive), USB drive, etc.

### Installation Instructions (For End Users)

**FOR YOUR FRIENDS WHO RECEIVE THE APP:**

1. **Download/Copy** the FinancialPlanner folder to your computer
2. **Extract** if it's in a zip file
3. **Open** the FinancialPlanner folder
4. **Double-click** the launcher script:
   - Windows: `run_FinancialPlanner.bat`
   - Mac/Linux: `run_FinancialPlanner.sh`
5. **Wait** a few seconds - your web browser will automatically open with the app
6. **Start planning!** 💰

### First Time Setup

**Windows Users:**
- If you see a "Windows protected your PC" warning, click "More info" and then "Run anyway"
- This is normal for applications that aren't signed with an expensive code signing certificate

**Mac Users:**
- If you see a security warning, go to System Preferences > Security & Privacy and click "Open Anyway"
- Or right-click the file and select "Open" the first time

**Linux Users:**
- Make sure the script is executable: `chmod +x run_FinancialPlanner.sh`

## 🚀 Running the Application

### For End Users (No Python Required!)

Simply double-click the launcher script:
- **Windows**: `run_FinancialPlanner.bat`
- **Mac/Linux**: `run_FinancialPlanner.sh`

The app will:
1. Start in the background
2. Automatically open in your default web browser
3. Display at: http://localhost:8501

To stop the app, just close the terminal/command window that opened.

### Troubleshooting

**Browser doesn't open automatically?**
- Manually open your browser and go to: http://localhost:8501

**Port 8501 already in use?**
- Close any other Streamlit applications
- Or edit the launcher script to use a different port

**Application won't start?**
- Check your antivirus isn't blocking it
- Make sure you extracted ALL files from the zip
- Try running from a folder path without spaces

## 📋 System Requirements

- **Windows**: Windows 10 or later (64-bit)
- **Mac**: macOS 10.13 or later
- **Linux**: Most modern distributions (Ubuntu 18.04+, etc.)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for the application files

## 🔧 Technical Details

### How It Works

This uses PyInstaller to bundle:
- Python interpreter
- Streamlit web framework
- All Python libraries (pandas, plotly, numpy, etc.)
- Your application code
- Assets and resources

Into a single folder that can run independently.

### File Structure

```
dist/FinancialPlanner/
├── FinancialPlanner.exe (or FinancialPlanner on Mac/Linux)
├── run_FinancialPlanner.bat (Windows launcher)
├── run_FinancialPlanner.sh (Mac/Linux launcher)
├── FinancialPlanner_v0_85.py (bundled)
├── assets/
│   └── piggy-bank-coin.svg
└── [many library files...]
```

## 🆘 Support

If you or your friends encounter issues:

1. **Check System Requirements**: Make sure the system meets minimum requirements
2. **Antivirus**: Some antivirus programs are overzealous with executables
3. **Permissions**: Ensure the folder has read/write permissions
4. **Rebuild**: Try building again if something seems corrupted

## 📝 License

Same license as the main Financial Planning Application.

## 🎯 Version History

- **v0.85**: Initial executable distribution version
  - Standalone packaging with PyInstaller
  - One-click launch experience
  - No Python installation required for end users

---

**Built with ❤️ using Python, Streamlit, and PyInstaller**
