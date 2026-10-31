@echo off
title Everlast - 1-Click QoL ^& Balance Fix
cd /d "%~dp0"
echo ========================================================
echo  Everlast: Undying Tale - 1-Click Mod Patcher
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3 or use the HTML Tweaker instead.
    echo.
    pause
    exit /b 1
)

python everlast_stack_mod.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Patching encountered an error.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  Ready to play! You can now launch Everlast on Steam.
echo ========================================================
echo.
pause

