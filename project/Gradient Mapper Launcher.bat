@echo off
cd /d "%~dp0"

title Gradient Mapper Launcher
color 0A

echo -
echo    Gradient Mapper
echo -
echo.
echo Starting...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Check if uv is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uv is not installed.
    echo.
    echo Installing uv package manager...
    echo.
    echo This will download and install uv from the official source.
    echo.
    echo Please wait...
    echo.
    
    REM Install uv
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    REM Refresh PATH so uv is available immediately
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
    
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv.
        echo.
        echo Please try installing uv manually:
        echo Visit https://docs.astral.sh/uv/getting-started/installation/
        echo.
        pause
        exit /b 1
    )
    
    echo [OK] uv installed successfully
    echo.
    pause
    exit /b 0
)

echo [OK] uv is ready
uv --version
echo.

REM Install dependencies
echo [INFO] Lacking dependencies
echo.
echo Installing dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo.
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM Start the web server
echo -
echo    Gradient Mapper Web UI
echo -
echo.
echo Starting...
echo.
echo The application will open in your browser at:
echo http://localhost:8000
echo.
echo Press Ctrl+C to stop the server when done
echo.

REM Start the server in a new window
echo CD = "%CD%"
pause
start "Gradient Mapper Server" cmd /k "uv run -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8000 --reload"


REM Give server time to boot
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8000