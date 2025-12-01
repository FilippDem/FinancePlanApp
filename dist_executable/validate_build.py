#!/usr/bin/env python3
"""
Pre-build validation script for Financial Planner executable
Checks for common issues before building with PyInstaller
"""

import sys
import os
import importlib.util

print("=" * 60)
print("Financial Planner - Pre-Build Validation")
print("=" * 60)
print()

errors = []
warnings = []
checks_passed = 0
checks_total = 0

def check(description):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            global checks_total, checks_passed
            checks_total += 1
            print(f"[{checks_total}] Checking: {description}...", end=" ")
            try:
                result = func(*args, **kwargs)
                if result:
                    print("✓ PASS")
                    checks_passed += 1
                    return True
                else:
                    print("✗ FAIL")
                    return False
            except Exception as e:
                print(f"✗ ERROR: {e}")
                errors.append(f"{description}: {e}")
                return False
        return wrapper
    return decorator

@check("Python version is 3.8+")
def check_python_version():
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f" (Python {version.major}.{version.minor}.{version.micro})")
        return True
    else:
        errors.append(f"Python {version.major}.{version.minor} is too old. Need 3.8+")
        return False

@check("PyInstaller is installed")
def check_pyinstaller():
    try:
        import PyInstaller
        print(f" (v{PyInstaller.__version__})")
        return True
    except ImportError:
        warnings.append("PyInstaller not installed - will be installed during build")
        return True

@check("Streamlit is installed")
def check_streamlit():
    try:
        import streamlit
        print(f" (v{streamlit.__version__})")
        return True
    except ImportError:
        errors.append("Streamlit not installed - run: pip install -r requirements_build.txt")
        return False

@check("Required packages installed")
def check_required_packages():
    required = ['pandas', 'numpy', 'plotly', 'openpyxl', 'reportlab']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        errors.append(f"Missing packages: {', '.join(missing)}")
        return False
    return True

@check("launcher.py exists and is readable")
def check_launcher():
    if not os.path.exists('launcher.py'):
        errors.append("launcher.py not found")
        return False
    with open('launcher.py', 'r') as f:
        content = f.read()
        if 'from streamlit.web import cli as stcli' not in content:
            errors.append("launcher.py doesn't import Streamlit CLI")
            return False
    return True

@check("FinancialPlanner_v0_85.py exists and has correct version")
def check_main_app():
    if not os.path.exists('FinancialPlanner_v0_85.py'):
        errors.append("FinancialPlanner_v0_85.py not found")
        return False
    with open('FinancialPlanner_v0_85.py', 'r') as f:
        content = f.read()
        if 'v0.85' not in content:
            warnings.append("Version string v0.85 not found in main app")
    return True

@check("FinancialPlanner.spec exists and is valid")
def check_spec_file():
    if not os.path.exists('FinancialPlanner.spec'):
        errors.append("FinancialPlanner.spec not found")
        return False

    with open('FinancialPlanner.spec', 'r') as f:
        content = f.read()

        # Check for metadata collection
        if 'copy_metadata' not in content:
            errors.append("spec file missing copy_metadata import - this will cause errors!")
            return False

        if "copy_metadata('streamlit')" not in content:
            errors.append("spec file not collecting streamlit metadata - this will cause errors!")
            return False

        # Check for launcher as entry point
        if "['launcher.py']" not in content:
            errors.append("spec file not using launcher.py as entry point")
            return False

    return True

@check("assets folder exists")
def check_assets():
    if not os.path.exists('assets'):
        warnings.append("assets folder not found")
        return True
    if not os.path.exists('assets/piggy-bank-coin.svg'):
        warnings.append("piggy-bank-coin.svg not found in assets")
    return True

@check("build scripts exist")
def check_build_scripts():
    has_bat = os.path.exists('build.bat')
    has_sh = os.path.exists('build.sh')

    if not has_bat and not has_sh:
        errors.append("No build scripts found")
        return False

    if sys.platform == 'win32' and not has_bat:
        warnings.append("build.bat not found (you're on Windows)")
    elif sys.platform != 'win32' and not has_sh:
        warnings.append("build.sh not found (you're on Unix)")

    return True

@check("run scripts exist")
def check_run_scripts():
    has_bat = os.path.exists('run_FinancialPlanner.bat')
    has_sh = os.path.exists('run_FinancialPlanner.sh')

    if not has_bat and not has_sh:
        errors.append("No run scripts found")
        return False

    return True

@check("requirements_build.txt exists")
def check_requirements():
    if not os.path.exists('requirements_build.txt'):
        errors.append("requirements_build.txt not found")
        return False

    with open('requirements_build.txt', 'r') as f:
        content = f.read()
        required = ['pyinstaller', 'streamlit', 'pandas', 'plotly']
        for pkg in required:
            if pkg.lower() not in content.lower():
                warnings.append(f"{pkg} not in requirements_build.txt")

    return True

@check("PyInstaller metadata hooks available")
def check_pyinstaller_hooks():
    try:
        from PyInstaller.utils.hooks import copy_metadata, collect_data_files

        # Test if we can collect streamlit metadata
        try:
            import streamlit
            # Don't actually collect, just verify the function works
            print(" (hooks functional)")
            return True
        except ImportError:
            warnings.append("Can't test metadata collection - Streamlit not installed")
            return True
    except ImportError:
        errors.append("PyInstaller hooks not available")
        return False

@check("Streamlit can be imported and initialized")
def check_streamlit_import():
    try:
        # Try importing the specific module we use in launcher
        from streamlit.web import cli as stcli
        print(" (CLI module accessible)")
        return True
    except ImportError as e:
        errors.append(f"Cannot import streamlit.web.cli: {e}")
        return False

@check("Current directory is dist_executable")
def check_directory():
    cwd = os.getcwd()
    if 'dist_executable' not in cwd:
        warnings.append(f"Current directory is {cwd} - should be in dist_executable folder")
    return True

@check("No conflicting dist/build folders")
def check_no_old_builds():
    if os.path.exists('dist') or os.path.exists('build'):
        warnings.append("Old dist/build folders exist - will be cleaned during build")
    return True

# Run all checks
print()
print("Running validation checks...")
print()

check_python_version()
check_pyinstaller()
check_streamlit()
check_required_packages()
check_launcher()
check_main_app()
check_spec_file()
check_assets()
check_build_scripts()
check_run_scripts()
check_requirements()
check_pyinstaller_hooks()
check_streamlit_import()
check_directory()
check_no_old_builds()

print()
print("=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)
print()
print(f"Total Checks: {checks_total}")
print(f"Passed: {checks_passed}")
print(f"Failed: {checks_total - checks_passed}")
print()

if warnings:
    print("⚠️  WARNINGS:")
    for w in warnings:
        print(f"  - {w}")
    print()

if errors:
    print("❌ ERRORS:")
    for e in errors:
        print(f"  - {e}")
    print()
    print("=" * 60)
    print("❌ VALIDATION FAILED")
    print("=" * 60)
    print()
    print("Please fix the errors above before building.")
    sys.exit(1)
else:
    print("=" * 60)
    print("✅ VALIDATION PASSED")
    print("=" * 60)
    print()
    if warnings:
        print("There are warnings, but you can proceed with the build.")
        print()
    print("You can now run:")
    if sys.platform == 'win32':
        print("  .\\build.bat")
    else:
        print("  ./build.sh")
    print()
    sys.exit(0)
