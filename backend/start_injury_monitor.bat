@echo off
REM Start Injury Monitor Service (Separate from main.py)
REM This runs independently so Twitter issues won't crash the main site

echo ========================================
echo Injury Monitor Service (Standalone)
echo ========================================
echo.

REM Check if Nitter is running
echo Checking if Nitter is running...
curl -s http://127.0.0.1:8080 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Nitter not detected at http://127.0.0.1:8080
    echo.
    echo Starting Nitter with Docker Compose...
    docker-compose -f docker-compose.nitter.yml up -d
    timeout /t 5 /nobreak >nul
    echo Nitter started!
    echo.
) else (
    echo [OK] Nitter is running
    echo.
)

REM Install requirements if needed
echo Checking dependencies...
pip show feedparser >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install feedparser pyyaml requests
)

REM Start the injury monitor service
echo.
echo Starting Injury Monitor Service...
echo This will run continuously in the background.
echo Press Ctrl+C to stop.
echo.

python injury_monitor_service.py

pause
