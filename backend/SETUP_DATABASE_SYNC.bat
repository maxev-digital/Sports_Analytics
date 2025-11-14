@echo off
REM Setup Windows Task Scheduler for Daily Database Sync
REM Run this ONCE to set up automated daily syncing at 2:00 AM CST

echo ========================================
echo DATABASE SYNC - Task Scheduler Setup
echo ========================================
echo.
echo This will create a scheduled task to sync databases daily at 2:00 AM CST
echo Press CTRL+C to cancel, or
pause

schtasks /create /tn "SportTrader Database Sync" /tr "python C:\Users\nashr\backend\sync_databases_to_vps.py" /sc daily /st 02:00 /f

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS - Task Created
    echo ========================================
    echo Task Name: SportTrader Database Sync
    echo Schedule: Daily at 2:00 AM CST
    echo Script: C:\Users\nashr\backend\sync_databases_to_vps.py
    echo.
    echo Databases will automatically sync to VPS every night before predictions run.
    echo.
) else (
    echo.
    echo ERROR - Failed to create task. You may need to run as Administrator.
    echo.
)

pause
