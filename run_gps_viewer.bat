@echo off
REM Quick launcher for GPS Viewer
REM Activates virtual environment if present and runs the viewer

echo Starting GPS Animal Movement Viewer...
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the GPS viewer
python gps_viewer.py

REM If error occurred, pause to see the error message
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start GPS viewer
    echo.
    echo Common solutions:
    echo   1. Install dependencies: pip install -r requirements_gps_viewer.txt
    echo   2. Fetch GPS data: python fetch_movebank_data.py --sensors gps
    echo   3. Run test script: python test_gps_viewer.py
    echo.
    pause
)
