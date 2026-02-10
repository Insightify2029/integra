@echo off
chcp 65001 >nul 2>&1
title INTEGRA - Sync from GitHub

echo ══════════════════════════════════════════
echo    INTEGRA - GitHub Sync
echo ══════════════════════════════════════════
echo.

cd /d D:\Projects\Integra

echo [1/3] Fetching from GitHub...
git fetch origin
if errorlevel 1 (
    echo ERROR: Failed to fetch. Check internet connection.
    pause
    exit /b 1
)

echo [2/3] Resetting to origin/main...
git reset --hard origin/main
if errorlevel 1 (
    echo ERROR: Failed to reset.
    pause
    exit /b 1
)

echo [3/3] Cleaning local files...
git clean -fd

echo.
echo ══════════════════════════════════════════
echo    Done! Local = GitHub main
echo ══════════════════════════════════════════
echo.

pause
