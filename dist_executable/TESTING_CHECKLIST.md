# Executable Distribution - Testing Checklist

This checklist ensures the Financial Planning Application executable works correctly.

## Pre-Build Checks

- [ ] Python 3.8+ installed
- [ ] All files present in `dist_executable/` folder:
  - [ ] launcher.py
  - [ ] FinancialPlanner_v0_85.py
  - [ ] FinancialPlanner.spec
  - [ ] build.sh / build.bat
  - [ ] run_FinancialPlanner.sh / run_FinancialPlanner.bat
  - [ ] requirements_build.txt
  - [ ] assets/piggy-bank-coin.svg
  - [ ] README.md

## Build Process Tests

### Windows Build
- [ ] Run `build.bat`
- [ ] Build completes without errors
- [ ] `dist/FinancialPlanner/` folder created
- [ ] FinancialPlanner.exe exists
- [ ] run_FinancialPlanner.bat copied to dist folder
- [ ] Assets folder copied
- [ ] Build size is reasonable (200-500 MB is normal)

### Linux/Mac Build
- [ ] Run `./build.sh`
- [ ] Build completes without errors
- [ ] `dist/FinancialPlanner/` folder created
- [ ] FinancialPlanner executable exists and is executable
- [ ] run_FinancialPlanner.sh copied to dist folder
- [ ] Assets folder copied
- [ ] Build size is reasonable (200-500 MB is normal)

## Execution Tests

### First Run
- [ ] Double-click run_FinancialPlanner script (or .exe directly)
- [ ] Console window opens and STAYS OPEN
- [ ] See "Financial Planning Application v0.85" header
- [ ] See "Starting the application..." message
- [ ] See "Loading Streamlit..." message
- [ ] See "Streamlit loaded successfully!" message
- [ ] See "Launching Streamlit server..." message
- [ ] Browser opens automatically (within 5-10 seconds)
- [ ] Application loads in browser at http://localhost:8501
- [ ] No errors in console window

### Application Functionality
- [ ] App displays title "Financial Planning Application v0.85"
- [ ] Sidebar visible and functional
- [ ] Can input data in all fields
- [ ] Charts render correctly
- [ ] Tables display properly
- [ ] Can generate Excel reports
- [ ] Can generate PDF reports (if reportlab installed)
- [ ] Can save/load scenarios
- [ ] All calculations work correctly

### Error Handling
- [ ] If port 8501 in use, displays clear error message
- [ ] If app file missing, shows helpful error
- [ ] Pressing Ctrl+C stops application cleanly
- [ ] Closing console window stops application

### Distribution Test
- [ ] Zip the entire `dist/FinancialPlanner/` folder
- [ ] Copy zip to another computer (or different folder)
- [ ] Extract zip
- [ ] Run application WITHOUT Python installed
- [ ] Application works correctly

## Common Issues to Check

### Issue: Window Flashes and Closes
**Check:**
- [ ] Using run_FinancialPlanner script, not exe directly
- [ ] All files extracted from zip (not running from within zip)
- [ ] Not running from OneDrive or network drive
- [ ] Antivirus not blocking

### Issue: Browser Doesn't Open
**Check:**
- [ ] Wait 10 seconds
- [ ] Manually open http://localhost:8501
- [ ] Check firewall settings

### Issue: Import Errors
**Check:**
- [ ] Rebuild with latest code
- [ ] All dependencies in requirements_build.txt
- [ ] PyInstaller >= 5.0.0

### Issue: Port Already in Use
**Check:**
- [ ] Close other Streamlit applications
- [ ] Check with: `netstat -ano | findstr :8501` (Windows) or `lsof -i :8501` (Mac/Linux)
- [ ] Restart computer if needed

## Performance Checks

- [ ] Application starts within 10 seconds
- [ ] Charts render smoothly
- [ ] No excessive memory usage (< 1 GB normal)
- [ ] Calculations complete quickly
- [ ] File operations work correctly

## Platform-Specific Tests

### Windows 10/11
- [ ] SmartScreen warning expected (click "More info" -> "Run anyway")
- [ ] Application runs correctly
- [ ] Can create desktop shortcut to run_FinancialPlanner.bat

### macOS
- [ ] Security warning expected (System Preferences -> Security & Privacy -> "Open Anyway")
- [ ] Application runs correctly
- [ ] Can create alias to run_FinancialPlanner.sh

### Linux (Ubuntu/Debian)
- [ ] Script has execute permission
- [ ] Application runs correctly
- [ ] Can create desktop launcher

## Final Verification

- [ ] Application version shows v0.85
- [ ] All features from main version work
- [ ] No Python installation required on test machine
- [ ] Can distribute zip file to non-technical users
- [ ] Instructions in README.md are clear and accurate
- [ ] Console messages are helpful and informative

## Sign-Off

**Build Date:** _______________
**Tested By:** _______________
**Platform:** _______________
**Status:** ☐ PASS ☐ FAIL
**Notes:**
_______________________________________
_______________________________________
_______________________________________

---

## Quick Troubleshooting Reference

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Window closes immediately | Running exe directly | Use run script |
| Import errors | Missing hiddenimports | Rebuild with updated spec |
| Port in use | Another app on 8501 | Close other apps or restart |
| Browser doesn't open | Timing issue | Wait or open manually |
| Antivirus blocks | False positive | Add exception or whitelist |
| Charts don't render | Kaleido missing | Check requirements_build.txt |
| PDF export fails | Reportlab missing | Check requirements_build.txt |

## Build Environment Info

Document your build environment for reproducibility:
- Python version: _______________
- PyInstaller version: _______________
- Streamlit version: _______________
- OS version: _______________
- Build date: _______________
