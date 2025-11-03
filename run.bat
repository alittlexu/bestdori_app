@echo off
REM Set UTF-8 code page for proper character display
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=UTF-8

echo Starting Bestdori Card Manager...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found in PATH!
    echo Please install Python 3.8 or higher and add it to your system PATH.
    echo.
    pause
    exit /b 1
)

REM Run the Python script
python run.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo Startup failed! Please check:
    echo 1. Is Python 3.8 or higher installed?
    echo 2. Are all dependencies installed? Run: pip install -r requirements.txt
    echo 3. Check the error messages above
    echo.
    pause
    exit /b 1
)

exit /b 0
