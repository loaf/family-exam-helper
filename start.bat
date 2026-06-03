@echo off
chcp 65001 >nul 2>&1
echo Starting Family Exam Helper...
echo.

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

:: Install dependencies if needed
python -c "import flask" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

:: Create required directories
if not exist "banks" mkdir banks
if not exist "uploads" mkdir uploads
if not exist "imports" mkdir imports

:: Start app
echo Server started! Opening browser...
echo Press Ctrl+C to stop.
echo.
start http://localhost:5000
python app.py
pause
